"""NeonDB database connector."""

from typing import Any, Dict, Optional
import re
from .postgres import PostgreSQLConnector


class NeonDBConnector(PostgreSQLConnector):
    """NeonDB database connector implementation.
    
    Extends PostgreSQL connector with NeonDB-specific features for serverless PostgreSQL.
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """Initialize NeonDB connector.
        
        Args:
            connection_string: NeonDB connection string
            **kwargs: Additional options including:
                - pooled_connection: Use pooled connection endpoint (recommended)
                - compute_endpoint: Specific compute endpoint
                - branch: Database branch name
                - role: Database role
        """
        # Parse NeonDB connection string
        connection_string = self._parse_neon_url(connection_string)
        
        # NeonDB specific settings
        self.pooled_connection = kwargs.pop('pooled_connection', True)
        self.compute_endpoint = kwargs.pop('compute_endpoint', None)
        self.branch = kwargs.pop('branch', 'main')
        self.role = kwargs.pop('role', None)
        
        # NeonDB recommends connection pooling for serverless
        if 'use_pool' not in kwargs:
            kwargs['use_pool'] = True
        
        # Smaller pool sizes for serverless
        if 'min_pool_size' not in kwargs:
            kwargs['min_pool_size'] = 1
        if 'max_pool_size' not in kwargs:
            kwargs['max_pool_size'] = 10
        
        # Enable SSL by default
        if 'ssl' not in kwargs:
            kwargs['ssl'] = 'require'
        
        # Set command timeout for serverless cold starts
        if 'command_timeout' not in kwargs:
            kwargs['command_timeout'] = 30
        
        super().__init__(connection_string, **kwargs)
    
    def _parse_neon_url(self, url: str) -> str:
        """Parse NeonDB URL formats.
        
        Handles:
        - Standard PostgreSQL connection strings
        - NeonDB dashboard URLs
        - Pooled vs direct connection endpoints
        """
        # If it's already a PostgreSQL connection string, check for pooling
        if url.startswith('postgresql://') or url.startswith('postgres://'):
            # Ensure we're using the pooled endpoint if requested
            if self.pooled_connection and '-pooler.' not in url:
                # Convert to pooled endpoint
                url = re.sub(r'\.neon\.tech', '-pooler.neon.tech', url)
                # Add pooling mode parameter
                if '?' in url:
                    url += '&options=project%3D' + self.compute_endpoint if self.compute_endpoint else ''
                else:
                    url += '?options=project%3D' + self.compute_endpoint if self.compute_endpoint else ''
            return url
        
        # Extract components from NeonDB dashboard URL
        match = re.search(r'([a-z0-9-]+)\.([a-z0-9-]+)\.neon\.tech', url)
        if match:
            endpoint = match.group(1)
            region = match.group(2)
            
            # Construct connection string
            base_host = f"{endpoint}.{region}"
            if self.pooled_connection:
                base_host += "-pooler"
            base_host += ".neon.tech"
            
            # Note: User needs to provide credentials
            return f"postgresql://[USER]:[PASSWORD]@{base_host}:5432/[DATABASE]"
        
        return url
    
    async def connect(self):
        """Connect to NeonDB database."""
        await super().connect()
        
        # Set NeonDB-specific session parameters
        await self._setup_neon_session()
        
        self._logger.info(f"Connected to NeonDB (branch: {self.branch}, pooled: {self.pooled_connection})")
    
    async def _setup_neon_session(self):
        """Set up NeonDB-specific session parameters."""
        # Set application name for better monitoring
        await self.execute("SET application_name = 'knova-ai-sdk'")
        
        # Set statement timeout for serverless
        await self.execute("SET statement_timeout = '30s'")
    
    async def create_branch(self, branch_name: str, from_branch: str = "main"):
        """Create a new database branch (requires NeonDB API)."""
        # Note: This would typically use the NeonDB management API
        # For now, we'll log the intent
        self._logger.info(f"Branch creation '{branch_name}' from '{from_branch}' requires NeonDB API")
        raise NotImplementedError("Branch creation requires NeonDB Management API integration")
    
    async def get_compute_status(self) -> Dict[str, Any]:
        """Get compute endpoint status."""
        # Query pg_stat_activity for connection info
        query = """
            SELECT 
                count(*) as active_connections,
                max(backend_start) as last_activity,
                current_setting('server_version') as pg_version
            FROM pg_stat_activity
            WHERE state = 'active'
        """
        
        result = await self.fetch_one(query)
        
        return {
            "status": "active",
            "active_connections": result.get("active_connections", 0),
            "last_activity": result.get("last_activity"),
            "postgres_version": result.get("pg_version"),
            "branch": self.branch,
            "pooled": self.pooled_connection
        }
    
    async def enable_logical_replication(self):
        """Enable logical replication for change data capture."""
        # NeonDB supports logical replication
        await self.execute("ALTER SYSTEM SET wal_level = 'logical'")
        self._logger.info("Enabled logical replication (requires compute restart)")
    
    async def optimize_for_analytics(self):
        """Optimize connection settings for analytical queries."""
        optimizations = [
            "SET work_mem = '256MB'",
            "SET maintenance_work_mem = '512MB'",
            "SET effective_cache_size = '4GB'",
            "SET random_page_cost = 1.1",
            "SET effective_io_concurrency = 200"
        ]
        
        for setting in optimizations:
            await self.execute(setting)
        
        self._logger.info("Optimized connection for analytics workloads")
    
    async def optimize_for_oltp(self):
        """Optimize connection settings for transactional workloads."""
        optimizations = [
            "SET work_mem = '16MB'",
            "SET maintenance_work_mem = '64MB'",
            "SET random_page_cost = 4",
            "SET effective_io_concurrency = 1",
            "SET synchronous_commit = 'on'"
        ]
        
        for setting in optimizations:
            await self.execute(setting)
        
        self._logger.info("Optimized connection for OLTP workloads")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get NeonDB connection information."""
        return {
            "type": "neondb",
            "pooled": self.pooled_connection,
            "branch": self.branch,
            "compute_endpoint": self.compute_endpoint,
            "pool_size": f"{self.min_pool_size}-{self.max_pool_size}",
            "ssl": self.ssl is not None
        }
    
    async def handle_cold_start(self):
        """Handle potential cold start by warming up the connection."""
        # Execute a simple query to warm up the compute
        await self.execute("SELECT 1")
        
        # Pre-compile common prepared statements
        common_queries = [
            "SELECT * FROM agents WHERE id = $1",
            "SELECT * FROM users WHERE id = $1",
            "SELECT * FROM workflows WHERE id = $1"
        ]
        
        for query in common_queries:
            try:
                # Prepare the statement (this caches the query plan)
                if self.use_pool:
                    async with self._pool.acquire() as conn:
                        await conn.prepare(query)
                else:
                    await self._connection.prepare(query)
            except Exception:
                # Table might not exist, ignore
                pass
        
        self._logger.info("Warmed up NeonDB connection")