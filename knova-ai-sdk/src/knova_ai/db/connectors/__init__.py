"""Database connectors for various backends."""

from typing import Optional, Type
from .base import BaseConnectorImpl
from .sqlite import SQLiteConnector
from .postgres import PostgreSQLConnector
from .supabase import SupabaseConnector
from .neondb import NeonDBConnector

__all__ = [
    'BaseConnectorImpl',
    'SQLiteConnector',
    'PostgreSQLConnector',
    'SupabaseConnector', 
    'NeonDBConnector',
    'get_connector'
]


def get_connector(db_type: str, connection_string: str, **kwargs) -> BaseConnectorImpl:
    """Factory function to get the appropriate database connector.
    
    Args:
        db_type: Type of database (sqlite, postgresql, supabase, neondb)
        connection_string: Database connection string
        **kwargs: Additional connector-specific options
        
    Returns:
        Database connector instance
        
    Raises:
        ValueError: If db_type is not supported
    """
    connectors = {
        'sqlite': SQLiteConnector,
        'postgresql': PostgreSQLConnector,
        'postgres': PostgreSQLConnector,  # Alias
        'supabase': SupabaseConnector,
        'neondb': NeonDBConnector,
        'neon': NeonDBConnector  # Alias
    }
    
    db_type_lower = db_type.lower()
    connector_class = connectors.get(db_type_lower)
    
    if not connector_class:
        supported = ', '.join(connectors.keys())
        raise ValueError(f"Unsupported database type: {db_type}. Supported types: {supported}")
    
    return connector_class(connection_string, **kwargs)