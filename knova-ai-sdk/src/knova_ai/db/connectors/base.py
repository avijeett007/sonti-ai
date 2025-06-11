"""Base implementation for database connectors."""

import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from ..base import BaseConnector, BaseEntity

T = TypeVar('T', bound=BaseEntity)
logger = logging.getLogger(__name__)


class BaseConnectorImpl(BaseConnector):
    """Base implementation with common functionality for all connectors."""
    
    def __init__(self, connection_string: str, **kwargs):
        """Initialize the connector."""
        super().__init__(connection_string, **kwargs)
        self._transaction = None
        self._logger = logger
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for database storage."""
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        elif hasattr(value, 'isoformat'):  # datetime objects
            return value.isoformat()
        return value
    
    def _deserialize_row(self, row: Dict[str, Any], entity_class: Type[T]) -> T:
        """Deserialize a database row to an entity."""
        # Handle None/NULL values
        if row is None:
            return None
        
        # Convert row to dict if needed
        if hasattr(row, '_asdict'):
            row = row._asdict()
        elif not isinstance(row, dict):
            row = dict(row)
        
        return entity_class.from_dict(row)
    
    def _build_insert_query(self, entity: BaseEntity) -> tuple[str, Dict[str, Any]]:
        """Build an INSERT query for an entity."""
        table = entity.table_name()
        data = entity.to_dict()
        
        columns = list(data.keys())
        placeholders = [f":{col}" for col in columns]
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """
        
        return query, data
    
    def _build_update_query(self, entity: BaseEntity) -> tuple[str, Dict[str, Any]]:
        """Build an UPDATE query for an entity."""
        table = entity.table_name()
        data = entity.to_dict()
        entity_id = data.pop('id')
        
        # Update timestamp
        entity.update_timestamp()
        data['updated_at'] = entity.updated_at.isoformat()
        
        set_clauses = [f"{col} = :{col}" for col in data.keys()]
        
        query = f"""
            UPDATE {table}
            SET {', '.join(set_clauses)}
            WHERE id = :id
            RETURNING *
        """
        
        data['id'] = entity_id
        return query, data
    
    def _build_select_query(self, entity_class: Type[T], filters: Optional[Dict[str, Any]] = None,
                          limit: Optional[int] = None, offset: Optional[int] = None) -> tuple[str, Dict[str, Any]]:
        """Build a SELECT query for entities."""
        table = entity_class.table_name()
        where_clause, params = self.build_where_clause(filters)
        
        query = f"SELECT * FROM {table} {where_clause}"
        
        if limit is not None:
            query += f" LIMIT {limit}"
        
        if offset is not None:
            query += f" OFFSET {offset}"
        
        return query, params
    
    async def create(self, entity: BaseEntity) -> BaseEntity:
        """Create a new entity in the database."""
        # Validate entity
        errors = entity.validate()
        if errors:
            raise ValueError(f"Entity validation failed: {'; '.join(errors)}")
        
        query, params = self._build_insert_query(entity)
        result = await self.fetch_one(query, params)
        
        if result:
            return self._deserialize_row(result, type(entity))
        
        return entity
    
    async def get(self, entity_class: Type[T], id: str) -> Optional[T]:
        """Get an entity by ID."""
        query = f"SELECT * FROM {entity_class.table_name()} WHERE id = :id"
        result = await self.fetch_one(query, {"id": id})
        
        if result:
            return self._deserialize_row(result, entity_class)
        
        return None
    
    async def update(self, entity: BaseEntity) -> BaseEntity:
        """Update an existing entity."""
        # Validate entity
        errors = entity.validate()
        if errors:
            raise ValueError(f"Entity validation failed: {'; '.join(errors)}")
        
        query, params = self._build_update_query(entity)
        result = await self.fetch_one(query, params)
        
        if result:
            return self._deserialize_row(result, type(entity))
        
        return entity
    
    async def delete(self, entity_class: Type[T], id: str) -> bool:
        """Delete an entity by ID."""
        query = f"DELETE FROM {entity_class.table_name()} WHERE id = :id"
        await self.execute(query, {"id": id})
        return True
    
    async def list(self, entity_class: Type[T], filters: Optional[Dict[str, Any]] = None,
                   limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """List entities with optional filtering and pagination."""
        query, params = self._build_select_query(entity_class, filters, limit, offset)
        results = await self.fetch_all(query, params)
        
        return [self._deserialize_row(row, entity_class) for row in results]
    
    async def count(self, entity_class: Type[T], filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filtering."""
        table = entity_class.table_name()
        where_clause, params = self.build_where_clause(filters)
        
        query = f"SELECT COUNT(*) as count FROM {table} {where_clause}"
        result = await self.fetch_one(query, params)
        
        return result.get('count', 0) if result else 0