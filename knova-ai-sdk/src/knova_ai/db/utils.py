"""Database utility functions."""

import os
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
import re


def parse_database_url(url: str) -> Dict[str, Any]:
    """Parse a database URL into components.
    
    Args:
        url: Database URL (e.g., postgresql://user:pass@host:port/db)
        
    Returns:
        Dictionary with connection parameters
    """
    parsed = urlparse(url)
    
    # Extract basic components
    config = {
        'scheme': parsed.scheme,
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path.lstrip('/') if parsed.path else None,
        'username': parsed.username,
        'password': parsed.password,
    }
    
    # Parse query parameters
    if parsed.query:
        params = parse_qs(parsed.query)
        # Convert single-value lists to strings
        config['params'] = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
    else:
        config['params'] = {}
    
    return config


def build_database_url(config: Dict[str, Any]) -> str:
    """Build a database URL from components.
    
    Args:
        config: Dictionary with connection parameters
        
    Returns:
        Database URL string
    """
    scheme = config.get('scheme', 'postgresql')
    username = config.get('username', '')
    password = config.get('password', '')
    host = config.get('host', 'localhost')
    port = config.get('port', 5432)
    database = config.get('database', '')
    params = config.get('params', {})
    
    # Build URL
    url = f"{scheme}://"
    
    if username:
        url += username
        if password:
            url += f":{password}"
        url += "@"
    
    url += host
    if port:
        url += f":{port}"
    
    if database:
        url += f"/{database}"
    
    # Add query parameters
    if params:
        param_strings = []
        for key, value in params.items():
            if isinstance(value, list):
                for v in value:
                    param_strings.append(f"{key}={v}")
            else:
                param_strings.append(f"{key}={value}")
        
        if param_strings:
            url += "?" + "&".join(param_strings)
    
    return url


def get_database_type(connection_string: str) -> str:
    """Determine database type from connection string.
    
    Args:
        connection_string: Database connection string
        
    Returns:
        Database type (sqlite, postgresql, supabase, neondb)
    """
    # SQLite detection
    if connection_string.endswith('.db') or connection_string.endswith('.sqlite'):
        return 'sqlite'
    if connection_string == ':memory:':
        return 'sqlite'
    if not connection_string.startswith(('postgresql://', 'postgres://')):
        # Assume file path is SQLite
        if '/' in connection_string or '\\' in connection_string:
            return 'sqlite'
    
    # PostgreSQL variants
    parsed = urlparse(connection_string)
    host = parsed.hostname or ''
    
    if 'supabase.co' in host:
        return 'supabase'
    elif 'neon.tech' in host:
        return 'neondb'
    elif parsed.scheme in ('postgresql', 'postgres'):
        return 'postgresql'
    
    # Default to SQLite for unknown
    return 'sqlite'


def sanitize_identifier(name: str) -> str:
    """Sanitize a database identifier (table/column name).
    
    Args:
        name: Raw identifier name
        
    Returns:
        Sanitized identifier safe for use in SQL
    """
    # Remove any non-alphanumeric characters except underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = '_' + sanitized
    
    # Limit length
    if len(sanitized) > 63:  # PostgreSQL identifier limit
        sanitized = sanitized[:63]
    
    return sanitized.lower()


def escape_value(value: Any) -> str:
    """Escape a value for use in SQL.
    
    WARNING: This is for display/logging only. 
    Always use parameterized queries for actual database operations.
    
    Args:
        value: Value to escape
        
    Returns:
        Escaped string representation
    """
    if value is None:
        return 'NULL'
    elif isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # Basic escaping - replace single quotes
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    else:
        # Convert to string and escape
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"


def get_env_database_url(prefix: str = "DATABASE") -> Optional[str]:
    """Get database URL from environment variables.
    
    Args:
        prefix: Environment variable prefix
        
    Returns:
        Database URL if found in environment
    """
    # Check for direct URL
    url = os.environ.get(f"{prefix}_URL")
    if url:
        return url
    
    # Build from components
    host = os.environ.get(f"{prefix}_HOST")
    if not host:
        return None
    
    config = {
        'scheme': os.environ.get(f"{prefix}_SCHEME", "postgresql"),
        'host': host,
        'port': os.environ.get(f"{prefix}_PORT", 5432),
        'database': os.environ.get(f"{prefix}_NAME", os.environ.get(f"{prefix}_DATABASE")),
        'username': os.environ.get(f"{prefix}_USER", os.environ.get(f"{prefix}_USERNAME")),
        'password': os.environ.get(f"{prefix}_PASSWORD", os.environ.get(f"{prefix}_PASS")),
    }
    
    # Add SSL if specified
    ssl_mode = os.environ.get(f"{prefix}_SSLMODE")
    if ssl_mode:
        config['params'] = {'sslmode': ssl_mode}
    
    return build_database_url(config)


def format_table_name(entity_name: str, prefix: Optional[str] = None) -> str:
    """Format an entity name as a table name.
    
    Args:
        entity_name: Entity class name (e.g., "KnowledgeBase")
        prefix: Optional table prefix
        
    Returns:
        Formatted table name (e.g., "knowledge_bases")
    """
    # Convert CamelCase to snake_case
    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', entity_name).lower()
    
    # Pluralize common patterns
    if snake_case.endswith('y') and not snake_case.endswith('ay'):
        snake_case = snake_case[:-1] + 'ies'
    elif snake_case.endswith(('s', 'ss', 'x', 'z', 'ch', 'sh')):
        snake_case = snake_case + 'es'
    elif not snake_case.endswith('s'):
        snake_case = snake_case + 's'
    
    # Add prefix if provided
    if prefix:
        snake_case = f"{prefix}_{snake_case}"
    
    return snake_case