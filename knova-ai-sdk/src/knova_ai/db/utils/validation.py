"""Database validation utilities."""

import re
from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class SQLValidator:
    """SQL validation utilities to prevent injection attacks."""
    
    # Valid table/column name pattern (alphanumeric + underscore)
    IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    
    # Reserved SQL keywords that shouldn't be used as identifiers
    RESERVED_KEYWORDS = {
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TABLE', 'DATABASE', 'INDEX', 'VIEW', 'TRIGGER', 'PROCEDURE',
        'FUNCTION', 'UNION', 'JOIN', 'WHERE', 'ORDER', 'GROUP', 'HAVING',
        'FROM', 'INTO', 'VALUES', 'SET', 'AND', 'OR', 'NOT', 'NULL',
        'PRIMARY', 'FOREIGN', 'KEY', 'REFERENCES', 'CASCADE', 'RESTRICT',
        'DEFAULT', 'CHECK', 'UNIQUE', 'EXISTS', 'BETWEEN', 'LIKE', 'IN',
        'AS', 'BY', 'ASC', 'DESC', 'LIMIT', 'OFFSET', 'FETCH', 'ROWS',
        'WITH', 'RECURSIVE', 'TEMP', 'TEMPORARY', 'TRANSACTION', 'COMMIT',
        'ROLLBACK', 'SAVEPOINT', 'RELEASE', 'PRAGMA', 'VACUUM', 'ANALYZE'
    }
    
    @classmethod
    def validate_identifier(cls, identifier: str, identifier_type: str = "identifier") -> str:
        """Validate SQL identifier (table name, column name, etc.).
        
        Args:
            identifier: The identifier to validate
            identifier_type: Type of identifier for error messages
            
        Returns:
            The validated identifier
            
        Raises:
            ValidationError: If the identifier is invalid
        """
        if not identifier:
            raise ValidationError(f"Empty {identifier_type} provided")
        
        # Check length
        if len(identifier) > 63:  # PostgreSQL limit
            raise ValidationError(f"{identifier_type} '{identifier}' exceeds maximum length of 63 characters")
        
        # Check pattern
        if not cls.IDENTIFIER_PATTERN.match(identifier):
            raise ValidationError(
                f"Invalid {identifier_type} '{identifier}'. "
                f"Must start with letter or underscore and contain only letters, numbers, and underscores"
            )
        
        # Check reserved keywords
        if identifier.upper() in cls.RESERVED_KEYWORDS:
            raise ValidationError(f"{identifier_type} '{identifier}' is a reserved SQL keyword")
        
        return identifier
    
    @classmethod
    def validate_table_name(cls, table_name: str) -> str:
        """Validate table name."""
        return cls.validate_identifier(table_name, "table name")
    
    @classmethod
    def validate_column_name(cls, column_name: str) -> str:
        """Validate column name."""
        return cls.validate_identifier(column_name, "column name")
    
    @classmethod
    def validate_column_names(cls, column_names: List[str]) -> List[str]:
        """Validate multiple column names."""
        return [cls.validate_column_name(name) for name in column_names]
    
    @classmethod
    def sanitize_value(cls, value: Any) -> Any:
        """Sanitize a value for SQL usage.
        
        Note: This is for additional safety. Parameters should always be bound, not concatenated.
        """
        if isinstance(value, str):
            # Remove any null bytes
            value = value.replace('\x00', '')
            # Limit string length
            if len(value) > 10000:
                value = value[:10000]
        
        return value
    
    @classmethod
    def validate_limit(cls, limit: Optional[int]) -> Optional[int]:
        """Validate LIMIT value."""
        if limit is None:
            return None
        
        if not isinstance(limit, int):
            raise ValidationError(f"LIMIT must be an integer, got {type(limit).__name__}")
        
        if limit < 0:
            raise ValidationError(f"LIMIT must be non-negative, got {limit}")
        
        if limit > 10000:
            raise ValidationError(f"LIMIT exceeds maximum value of 10000, got {limit}")
        
        return limit
    
    @classmethod
    def validate_offset(cls, offset: Optional[int]) -> Optional[int]:
        """Validate OFFSET value."""
        if offset is None:
            return None
        
        if not isinstance(offset, int):
            raise ValidationError(f"OFFSET must be an integer, got {type(offset).__name__}")
        
        if offset < 0:
            raise ValidationError(f"OFFSET must be non-negative, got {offset}")
        
        return offset
    
    @classmethod
    def validate_parameters(cls, params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate and sanitize query parameters."""
        if params is None:
            return None
        
        sanitized = {}
        for key, value in params.items():
            # Validate parameter name
            cls.validate_identifier(key, "parameter name")
            # Sanitize value
            sanitized[key] = cls.sanitize_value(value)
        
        return sanitized


class InputValidator:
    """General input validation utilities."""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address."""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            raise ValidationError(f"Invalid email address: {email}")
        return email.lower()
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate phone number."""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Check length (international numbers can be 7-15 digits)
        if len(digits) < 7 or len(digits) > 15:
            raise ValidationError(f"Invalid phone number length: {phone}")
        
        return digits
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate URL."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            raise ValidationError(f"Invalid URL: {url}")
        
        return url
    
    @staticmethod
    def validate_json(data: Any) -> Any:
        """Validate JSON-serializable data."""
        import json
        try:
            json.dumps(data)
            return data
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Data is not JSON serializable: {e}")
    
    @staticmethod
    def validate_string_length(value: str, max_length: int, field_name: str) -> str:
        """Validate string length."""
        if len(value) > max_length:
            raise ValidationError(f"{field_name} exceeds maximum length of {max_length} characters")
        return value