"""Base classes for database entities and connectors."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
import uuid
from dataclasses import dataclass, field, asdict
import json

T = TypeVar('T', bound='BaseEntity')


@dataclass
class BaseEntity(ABC):
    """Base class for all database entities."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    @abstractmethod
    def table_name(cls) -> str:
        """Return the database table name for this entity."""
        pass
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create an entity instance from a dictionary."""
        # Convert string timestamps to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        # Handle JSON fields
        for field_name, field_type in cls.__annotations__.items():
            if field_name in data and isinstance(data[field_name], str):
                if hasattr(field_type, '__origin__') and field_type.__origin__ in (dict, list):
                    try:
                        data[field_name] = json.loads(data[field_name])
                    except (json.JSONDecodeError, TypeError):
                        pass
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity to a dictionary."""
        data = asdict(self)
        
        # Convert datetime objects to ISO format strings
        if isinstance(data.get('created_at'), datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data.get('updated_at'), datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        
        # Handle JSON fields
        for field_name, value in data.items():
            if isinstance(value, (dict, list)):
                data[field_name] = json.dumps(value)
        
        return data
    
    def validate(self) -> List[str]:
        """Validate the entity and return a list of validation errors."""
        errors = []
        
        if not self.id:
            errors.append("ID is required")
        
        if not isinstance(self.created_at, datetime):
            errors.append("created_at must be a datetime object")
        
        if not isinstance(self.updated_at, datetime):
            errors.append("updated_at must be a datetime object")
        
        if self.created_at > self.updated_at:
            errors.append("created_at cannot be after updated_at")
        
        return errors
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()


class BaseConnector(ABC):
    """Abstract base class for database connectors."""
    
    def __init__(self, connection_string: str, **kwargs):
        """Initialize the connector with a connection string."""
        self.connection_string = connection_string
        self.options = kwargs
        self._connection = None
    
    @abstractmethod
    async def connect(self):
        """Establish a connection to the database."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close the database connection."""
        pass
    
    @abstractmethod
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a raw SQL query."""
        pass
    
    @abstractmethod
    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Execute a query and fetch one result."""
        pass
    
    @abstractmethod
    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and fetch all results."""
        pass
    
    @abstractmethod
    async def create(self, entity: BaseEntity) -> BaseEntity:
        """Create a new entity in the database."""
        pass
    
    @abstractmethod
    async def get(self, entity_class: Type[T], id: str) -> Optional[T]:
        """Get an entity by ID."""
        pass
    
    @abstractmethod
    async def update(self, entity: BaseEntity) -> BaseEntity:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, entity_class: Type[T], id: str) -> bool:
        """Delete an entity by ID."""
        pass
    
    @abstractmethod
    async def list(self, entity_class: Type[T], filters: Optional[Dict[str, Any]] = None, 
                   limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """List entities with optional filtering and pagination."""
        pass
    
    @abstractmethod
    async def count(self, entity_class: Type[T], filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filtering."""
        pass
    
    @abstractmethod
    async def begin_transaction(self):
        """Begin a database transaction."""
        pass
    
    @abstractmethod
    async def commit_transaction(self):
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback_transaction(self):
        """Rollback the current transaction."""
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def build_where_clause(self, filters: Optional[Dict[str, Any]] = None) -> tuple[str, Dict[str, Any]]:
        """Build a WHERE clause from filters."""
        if not filters:
            return "", {}
        
        conditions = []
        params = {}
        
        for key, value in filters.items():
            if value is None:
                conditions.append(f"{key} IS NULL")
            elif isinstance(value, (list, tuple)):
                placeholders = [f":{key}_{i}" for i in range(len(value))]
                conditions.append(f"{key} IN ({', '.join(placeholders)})")
                for i, v in enumerate(value):
                    params[f"{key}_{i}"] = v
            else:
                conditions.append(f"{key} = :{key}")
                params[key] = value
        
        where_clause = " AND ".join(conditions)
        return f"WHERE {where_clause}" if where_clause else "", params