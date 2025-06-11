"""Connection pooling utilities for database connectors."""

import asyncio
import aiosqlite
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class SQLiteConnectionPool:
    """Connection pool for SQLite databases with async support."""
    
    def __init__(self, 
                 db_path: str,
                 pool_size: int = 5,
                 max_overflow: int = 10,
                 pool_timeout: float = 30.0,
                 connection_timeout: float = 5.0,
                 max_lifetime: int = 3600,
                 **connection_kwargs):
        """Initialize the connection pool.
        
        Args:
            db_path: Path to SQLite database file or ':memory:'
            pool_size: Number of connections to maintain in the pool
            max_overflow: Maximum overflow connections allowed
            pool_timeout: Timeout for getting a connection from the pool
            connection_timeout: Timeout for establishing a new connection
            max_lifetime: Maximum lifetime of a connection in seconds
            **connection_kwargs: Additional SQLite connection parameters
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.connection_timeout = connection_timeout
        self.max_lifetime = max_lifetime
        self.connection_kwargs = connection_kwargs
        
        # Pool management
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self._overflow_count = 0
        self._overflow_lock = asyncio.Lock()
        self._created_connections = 0
        self._closed = False
        
        # Connection tracking
        self._connection_info: Dict[Any, Dict[str, Any]] = {}
        
        # Statistics
        self._stats = {
            'connections_created': 0,
            'connections_closed': 0,
            'connections_reused': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'overflow_created': 0,
            'timeouts': 0
        }
    
    async def _create_connection(self) -> aiosqlite.Connection:
        """Create a new database connection."""
        # Create directory if needed
        if self.db_path != ':memory:':
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
        
        conn = await aiosqlite.connect(
            self.db_path,
            timeout=self.connection_timeout,
            **self.connection_kwargs
        )
        
        # Enable foreign keys and WAL mode
        await conn.execute("PRAGMA foreign_keys = ON")
        await conn.execute("PRAGMA journal_mode = WAL")
        await conn.commit()
        
        # Track connection info
        self._connection_info[id(conn)] = {
            'created_at': datetime.now(timezone.utc),
            'last_used': datetime.now(timezone.utc),
            'uses': 0
        }
        
        self._stats['connections_created'] += 1
        self._created_connections += 1
        
        logger.debug(f"Created new connection #{self._created_connections}")
        return conn
    
    async def _close_connection(self, conn: aiosqlite.Connection):
        """Close a database connection."""
        try:
            await conn.close()
            
            # Remove connection info
            conn_id = id(conn)
            if conn_id in self._connection_info:
                del self._connection_info[conn_id]
            
            self._stats['connections_closed'] += 1
            logger.debug("Closed database connection")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    
    async def _validate_connection(self, conn: aiosqlite.Connection) -> bool:
        """Validate that a connection is still alive and usable."""
        try:
            # Check connection lifetime
            conn_id = id(conn)
            if conn_id in self._connection_info:
                info = self._connection_info[conn_id]
                age = (datetime.now(timezone.utc) - info['created_at']).total_seconds()
                
                if age > self.max_lifetime:
                    logger.debug(f"Connection exceeded max lifetime ({age}s > {self.max_lifetime}s)")
                    return False
            
            # Test connection with a simple query
            await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.debug(f"Connection validation failed: {e}")
            return False
    
    async def _fill_pool(self):
        """Fill the pool with initial connections."""
        for _ in range(self.pool_size):
            if self._pool.full():
                break
            
            try:
                conn = await self._create_connection()
                await self._pool.put(conn)
            except Exception as e:
                logger.error(f"Failed to create initial connection: {e}")
    
    async def initialize(self):
        """Initialize the connection pool."""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        await self._fill_pool()
        logger.info(f"Initialized connection pool with {self._pool.qsize()} connections")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        conn = None
        from_pool = False
        
        try:
            # Try to get from pool
            try:
                conn = await asyncio.wait_for(
                    self._pool.get(),
                    timeout=self.pool_timeout
                )
                from_pool = True
                self._stats['pool_hits'] += 1
                
                # Validate connection
                if not await self._validate_connection(conn):
                    await self._close_connection(conn)
                    conn = await self._create_connection()
                    from_pool = False
                    
            except asyncio.TimeoutError:
                self._stats['timeouts'] += 1
                self._stats['pool_misses'] += 1
                
                # Try to create overflow connection
                async with self._overflow_lock:
                    if self._overflow_count < self.max_overflow:
                        conn = await self._create_connection()
                        self._overflow_count += 1
                        self._stats['overflow_created'] += 1
                        logger.debug(f"Created overflow connection ({self._overflow_count}/{self.max_overflow})")
                    else:
                        raise RuntimeError(
                            f"Connection pool exhausted (pool_size={self.pool_size}, "
                            f"max_overflow={self.max_overflow})"
                        )
            
            # Update connection usage
            conn_id = id(conn)
            if conn_id in self._connection_info:
                info = self._connection_info[conn_id]
                info['last_used'] = datetime.now(timezone.utc)
                info['uses'] += 1
                
                if from_pool:
                    self._stats['connections_reused'] += 1
            
            yield conn
            
        finally:
            if conn:
                # Return to pool or close
                if from_pool and not self._pool.full() and not self._closed:
                    try:
                        await self._pool.put(conn)
                    except asyncio.QueueFull:
                        await self._close_connection(conn)
                else:
                    await self._close_connection(conn)
                    if not from_pool:
                        async with self._overflow_lock:
                            self._overflow_count = max(0, self._overflow_count - 1)
    
    async def close(self):
        """Close all connections in the pool."""
        self._closed = True
        
        # Close all pooled connections
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                await self._close_connection(conn)
            except asyncio.QueueEmpty:
                break
        
        logger.info(f"Closed connection pool. Stats: {self._stats}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            **self._stats,
            'pool_size': self._pool.qsize(),
            'overflow_count': self._overflow_count,
            'total_connections': self._created_connections
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()