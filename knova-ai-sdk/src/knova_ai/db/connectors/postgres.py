"""PostgreSQL database connector."""

import asyncpg
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager
import json
from .base import BaseConnectorImpl


class PostgreSQLConnector(BaseConnectorImpl):
    """PostgreSQL database connector implementation."""
    
    def __init__(self, connection_string: str, **kwargs):
        """Initialize PostgreSQL connector.
        
        Args:
            connection_string: PostgreSQL connection string
            **kwargs: Additional options like pool_size, ssl, etc.
        """
        super().__init__(connection_string, **kwargs)
        self._pool = None
        self._connection = None
        
        # Connection pool settings
        self.min_pool_size = kwargs.get('min_pool_size', 10)
        self.max_pool_size = kwargs.get('max_pool_size', 20)
        self.command_timeout = kwargs.get('command_timeout', 60)
        self.ssl = kwargs.get('ssl', None)
        
        # Whether to use connection pooling
        self.use_pool = kwargs.get('use_pool', True)
    
    async def connect(self):
        """Establish connection to PostgreSQL database."""
        if self.use_pool:
            self._pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size,
                command_timeout=self.command_timeout,
                ssl=self.ssl
            )
            self._logger.info(f"Connected to PostgreSQL with pool (size: {self.min_pool_size}-{self.max_pool_size})")
        else:
            self._connection = await asyncpg.connect(
                self.connection_string,
                command_timeout=self.command_timeout,
                ssl=self.ssl
            )
            self._logger.info("Connected to PostgreSQL without pool")
    
    async def disconnect(self):
        """Close the database connection."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._logger.info("Closed PostgreSQL connection pool")
        elif self._connection:
            await self._connection.close()
            self._connection = None
            self._logger.info("Closed PostgreSQL connection")
    
    def _get_connection(self):
        """Get a connection (either pooled or direct)."""
        if self.use_pool:
            if not self._pool:
                raise RuntimeError("Not connected to database")
            return self._pool.acquire()
        else:
            if not self._connection:
                raise RuntimeError("Not connected to database")
            return self._connection
    
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a raw SQL query."""
        # Convert params to PostgreSQL format
        pg_query, pg_params = self._convert_query_params(query, params)
        
        if self.use_pool:
            async with self._pool.acquire() as conn:
                return await conn.execute(pg_query, *pg_params)
        else:
            return await self._connection.execute(pg_query, *pg_params)
    
    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Execute a query and fetch one result."""
        pg_query, pg_params = self._convert_query_params(query, params)
        
        if self.use_pool:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(pg_query, *pg_params)
        else:
            row = await self._connection.fetchrow(pg_query, *pg_params)
        
        if row:
            return dict(row)
        return None
    
    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and fetch all results."""
        pg_query, pg_params = self._convert_query_params(query, params)
        
        if self.use_pool:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(pg_query, *pg_params)
        else:
            rows = await self._connection.fetch(pg_query, *pg_params)
        
        return [dict(row) for row in rows]
    
    async def begin_transaction(self):
        """Begin a database transaction."""
        if self.use_pool:
            # For pooled connections, we need to acquire a connection for the transaction
            self._transaction = await self._pool.acquire()
            self._transaction_obj = self._transaction.transaction()
            await self._transaction_obj.start()
        else:
            self._transaction_obj = self._connection.transaction()
            await self._transaction_obj.start()
    
    async def commit_transaction(self):
        """Commit the current transaction."""
        if self._transaction_obj:
            await self._transaction_obj.commit()
            if self.use_pool and self._transaction:
                await self._pool.release(self._transaction)
                self._transaction = None
            self._transaction_obj = None
    
    async def rollback_transaction(self):
        """Rollback the current transaction."""
        if self._transaction_obj:
            await self._transaction_obj.rollback()
            if self.use_pool and self._transaction:
                await self._pool.release(self._transaction)
                self._transaction = None
            self._transaction_obj = None
    
    def _convert_query_params(self, query: str, params: Optional[Dict[str, Any]] = None) -> tuple[str, List[Any]]:
        """Convert named parameters to PostgreSQL $1, $2 format."""
        if not params:
            return query, []
        
        # Sort params by key to ensure consistent ordering
        sorted_params = sorted(params.items())
        
        # Replace :param_name with $1, $2, etc.
        pg_query = query
        pg_params = []
        
        for i, (key, value) in enumerate(sorted_params, 1):
            pg_query = pg_query.replace(f":{key}", f"${i}")
            
            # Handle JSON serialization
            if isinstance(value, (dict, list)):
                pg_params.append(json.dumps(value))
            else:
                pg_params.append(value)
        
        return pg_query, pg_params
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactions."""
        await self.begin_transaction()
        try:
            yield
            await self.commit_transaction()
        except Exception:
            await self.rollback_transaction()
            raise
    
    async def create_tables_if_not_exist(self, schema: str):
        """Create tables from schema if they don't exist."""
        if self.use_pool:
            async with self._pool.acquire() as conn:
                await conn.execute(schema)
        else:
            await self._connection.execute(schema)
        
        self._logger.info("Database schema created/verified")
    
    async def execute_many(self, query: str, params_list: List[Dict[str, Any]]) -> None:
        """Execute a query multiple times with different parameters."""
        if not params_list:
            return
        
        # Convert all parameters
        converted_params = []
        pg_query = query
        
        # Use the first params dict to determine parameter positions
        if params_list:
            pg_query, _ = self._convert_query_params(query, params_list[0])
            
            for params in params_list:
                _, pg_params = self._convert_query_params(query, params)
                converted_params.append(pg_params)
        
        if self.use_pool:
            async with self._pool.acquire() as conn:
                await conn.executemany(pg_query, converted_params)
        else:
            await self._connection.executemany(pg_query, converted_params)