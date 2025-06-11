"""Supabase database connector."""

from typing import Any, Dict, List, Optional
import re
from .postgres import PostgreSQLConnector


class SupabaseConnector(PostgreSQLConnector):
    """Supabase database connector implementation.
    
    Extends PostgreSQL connector with Supabase-specific features.
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """Initialize Supabase connector.
        
        Args:
            connection_string: Supabase connection string or URL
            **kwargs: Additional options including:
                - service_role_key: For bypassing RLS
                - anon_key: For client-side operations
                - project_ref: Supabase project reference
        """
        # Parse Supabase connection string if needed
        connection_string = self._parse_supabase_url(connection_string)
        
        # Supabase specific settings
        self.service_role_key = kwargs.pop('service_role_key', None)
        self.anon_key = kwargs.pop('anon_key', None)
        self.project_ref = kwargs.pop('project_ref', None)
        
        # Enable SSL by default for Supabase
        if 'ssl' not in kwargs:
            kwargs['ssl'] = 'require'
        
        # Use connection pooling by default
        if 'use_pool' not in kwargs:
            kwargs['use_pool'] = True
        
        super().__init__(connection_string, **kwargs)
    
    def _parse_supabase_url(self, url: str) -> str:
        """Parse Supabase URL formats.
        
        Handles:
        - Standard PostgreSQL connection strings
        - Supabase dashboard URLs (converts to connection string)
        """
        # If it's already a PostgreSQL connection string, return as-is
        if url.startswith('postgresql://') or url.startswith('postgres://'):
            return url
        
        # Handle Supabase project reference format
        if not url.startswith('postgresql://'):
            # Extract project reference from various formats
            match = re.search(r'([a-z0-9]+)\.supabase\.co', url)
            if match:
                project_ref = match.group(1)
                # Construct default Supabase connection string
                # Note: User will need to provide password separately
                return f"postgresql://postgres.{project_ref}:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
        
        return url
    
    async def connect(self):
        """Connect to Supabase database."""
        await super().connect()
        
        # Set up Supabase-specific session settings if service role key is provided
        if self.service_role_key:
            await self._setup_service_role_session()
        
        self._logger.info("Connected to Supabase database")
    
    async def _setup_service_role_session(self):
        """Set up session for service role operations."""
        # Service role bypasses RLS by default
        # This is handled at the connection level in Supabase
        pass
    
    async def enable_rls(self, table_name: str):
        """Enable Row Level Security for a table."""
        query = f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"
        await self.execute(query)
        self._logger.info(f"Enabled RLS for table: {table_name}")
    
    async def disable_rls(self, table_name: str):
        """Disable Row Level Security for a table."""
        if not self.service_role_key:
            raise PermissionError("Service role key required to disable RLS")
        
        query = f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY"
        await self.execute(query)
        self._logger.info(f"Disabled RLS for table: {table_name}")
    
    async def create_rls_policy(self, table_name: str, policy_name: str, 
                               operation: str, check_expr: str, 
                               using_expr: Optional[str] = None):
        """Create an RLS policy for a table.
        
        Args:
            table_name: Name of the table
            policy_name: Name for the policy
            operation: Operation (SELECT, INSERT, UPDATE, DELETE, ALL)
            check_expr: Expression for WITH CHECK clause
            using_expr: Expression for USING clause (defaults to check_expr)
        """
        if not self.service_role_key:
            raise PermissionError("Service role key required to create RLS policies")
        
        using_clause = f"USING ({using_expr or check_expr})"
        check_clause = f"WITH CHECK ({check_expr})" if operation != 'SELECT' else ""
        
        query = f"""
            CREATE POLICY {policy_name} ON {table_name}
            FOR {operation}
            {using_clause}
            {check_clause}
        """
        
        await self.execute(query)
        self._logger.info(f"Created RLS policy '{policy_name}' for table: {table_name}")
    
    async def create_auth_policies(self, table_name: str, user_id_column: str = "user_id"):
        """Create standard auth-based RLS policies for a table.
        
        Creates policies that allow users to only access their own data.
        """
        if not self.service_role_key:
            raise PermissionError("Service role key required to create RLS policies")
        
        # Enable RLS
        await self.enable_rls(table_name)
        
        # Create policies for authenticated users
        policies = [
            ("select", f"auth.uid() = {user_id_column}"),
            ("insert", f"auth.uid() = {user_id_column}"),
            ("update", f"auth.uid() = {user_id_column}"),
            ("delete", f"auth.uid() = {user_id_column}")
        ]
        
        for operation, expression in policies:
            policy_name = f"Users can {operation} own {table_name}"
            try:
                await self.create_rls_policy(
                    table_name=table_name,
                    policy_name=policy_name,
                    operation=operation.upper(),
                    check_expr=expression
                )
            except Exception as e:
                self._logger.warning(f"Failed to create policy '{policy_name}': {e}")
    
    async def create_function(self, function_sql: str):
        """Create a PostgreSQL function in Supabase."""
        if not self.service_role_key:
            raise PermissionError("Service role key required to create functions")
        
        await self.execute(function_sql)
        self._logger.info("Created PostgreSQL function")
    
    async def create_trigger(self, trigger_sql: str):
        """Create a PostgreSQL trigger in Supabase."""
        if not self.service_role_key:
            raise PermissionError("Service role key required to create triggers")
        
        await self.execute(trigger_sql)
        self._logger.info("Created PostgreSQL trigger")
    
    def get_rest_url(self, table_name: str) -> Optional[str]:
        """Get the Supabase REST API URL for a table."""
        if self.project_ref:
            return f"https://{self.project_ref}.supabase.co/rest/v1/{table_name}"
        return None
    
    def get_realtime_url(self) -> Optional[str]:
        """Get the Supabase Realtime websocket URL."""
        if self.project_ref:
            return f"wss://{self.project_ref}.supabase.co/realtime/v1/websocket"
        return None