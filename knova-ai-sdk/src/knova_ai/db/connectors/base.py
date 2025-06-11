"""Base implementation for database connectors."""

import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from ..base import BaseConnector, BaseEntity
from ..utils.validation import SQLValidator, ValidationError

T = TypeVar('T', bound=BaseEntity)
logger = logging.getLogger(__name__)


class BaseConnectorImpl(BaseConnector):
    """Base implementation with common functionality for all connectors."""
    
    def __init__(self, connection_string: str, **kwargs):
        """Initialize the connector."""
        super().__init__(connection_string, **kwargs)
        self._transaction = None
        self._logger = logger
        self._connected = False
    
    def _check_connection(self):
        """Check if the connector is connected to the database."""
        if not self._connected:
            raise RuntimeError("Not connected to database. Call connect() first.")
    
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
        # Validate table name to prevent SQL injection
        table = SQLValidator.validate_table_name(entity.table_name())
        data = entity.to_dict()
        
        # Validate column names
        columns = SQLValidator.validate_column_names(list(data.keys()))
        placeholders = [f":{col}" for col in columns]
        
        # Sanitize parameter values
        data = SQLValidator.validate_parameters(data)
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """
        
        return query, data
    
    def _build_update_query(self, entity: BaseEntity) -> tuple[str, Dict[str, Any]]:
        """Build an UPDATE query for an entity."""
        # Validate table name to prevent SQL injection
        table = SQLValidator.validate_table_name(entity.table_name())
        data = entity.to_dict()
        entity_id = data.pop('id')
        
        # Update timestamp
        entity.update_timestamp()
        data['updated_at'] = entity.updated_at.isoformat()
        
        # Validate column names
        columns = SQLValidator.validate_column_names(list(data.keys()))
        set_clauses = [f"{col} = :{col}" for col in columns]
        
        # Sanitize parameter values
        data = SQLValidator.validate_parameters(data)
        
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
        # Validate table name
        table = SQLValidator.validate_table_name(entity_class.table_name())
        
        # Sanitize filters
        if filters:
            filters = SQLValidator.validate_parameters(filters)
        
        where_clause, params = self.build_where_clause(filters)
        
        # Validate limit and offset
        limit = SQLValidator.validate_limit(limit)
        offset = SQLValidator.validate_offset(offset)
        
        query = f"SELECT * FROM {table} {where_clause}"
        
        if limit is not None:
            query += f" LIMIT {limit}"
        
        if offset is not None:
            query += f" OFFSET {offset}"
        
        return query, params
    
    async def create(self, entity: BaseEntity) -> BaseEntity:
        """Create a new entity in the database."""
        # Check connection
        self._check_connection()
        
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
        # Check connection
        self._check_connection()
        
        # Validate table name
        table = SQLValidator.validate_table_name(entity_class.table_name())
        query = f"SELECT * FROM {table} WHERE id = :id"
        
        # Sanitize parameters
        params = SQLValidator.validate_parameters({"id": id})
        result = await self.fetch_one(query, params)
        
        if result:
            return self._deserialize_row(result, entity_class)
        
        return None
    
    async def update(self, entity: BaseEntity) -> BaseEntity:
        """Update an existing entity."""
        # Check connection
        self._check_connection()
        
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
        # Validate table name
        table = SQLValidator.validate_table_name(entity_class.table_name())
        query = f"DELETE FROM {table} WHERE id = :id"
        
        # Sanitize parameters
        params = SQLValidator.validate_parameters({"id": id})
        await self.execute(query, params)
        return True
    
    async def list(self, entity_class: Type[T], filters: Optional[Dict[str, Any]] = None,
                   limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """List entities with optional filtering and pagination."""
        query, params = self._build_select_query(entity_class, filters, limit, offset)
        results = await self.fetch_all(query, params)
        
        return [self._deserialize_row(row, entity_class) for row in results]
    
    async def count(self, entity_class: Type[T], filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filtering."""
        # Validate table name
        table = SQLValidator.validate_table_name(entity_class.table_name())
        
        # Sanitize filters
        if filters:
            filters = SQLValidator.validate_parameters(filters)
        
        where_clause, params = self.build_where_clause(filters)
        
        query = f"SELECT COUNT(*) as count FROM {table} {where_clause}"
        result = await self.fetch_one(query, params)
        
        return result.get('count', 0) if result else 0
    
    async def bulk_create(self, entities: List[BaseEntity]) -> List[BaseEntity]:
        """Bulk create multiple entities efficiently."""
        if not entities:
            return []
        
        # Check connection
        self._check_connection()
        
        # Validate all entities first
        for i, entity in enumerate(entities):
            errors = entity.validate()
            if errors:
                raise ValueError(f"Entity #{i} validation failed: {'; '.join(errors)}")
        
        # Group entities by type
        entity_type = type(entities[0])
        if not all(isinstance(e, entity_type) for e in entities):
            raise ValueError("All entities must be of the same type for bulk operations")
        
        # Build bulk insert query
        table = SQLValidator.validate_table_name(entity_type.table_name())
        
        # Get column names from first entity
        first_data = entities[0].to_dict()
        columns = SQLValidator.validate_column_names(list(first_data.keys()))
        
        # Create placeholders for all entities
        values_clauses = []
        all_params = {}
        
        for i, entity in enumerate(entities):
            data = entity.to_dict()
            placeholders = []
            
            for col in columns:
                param_name = f"{col}_{i}"
                placeholders.append(f":{param_name}")
                all_params[param_name] = data.get(col)
            
            values_clauses.append(f"({', '.join(placeholders)})")
        
        # Sanitize all parameters
        all_params = SQLValidator.validate_parameters(all_params)
        
        # Build query (note: RETURNING * may not work with bulk insert in all databases)
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES {', '.join(values_clauses)}
        """
        
        # Execute bulk insert
        await self.execute(query, all_params)
        
        # Fetch all created entities (this is simplified - in practice might need different approach)
        # For now, return the entities as-is since they have IDs
        return entities
    
    async def bulk_update(self, entities: List[BaseEntity]) -> List[BaseEntity]:
        """Bulk update multiple entities efficiently."""
        if not entities:
            return []
        
        # Check connection
        self._check_connection()
        
        # For updates, we need to handle each entity separately due to different update values
        # But we can batch them in a transaction
        results = []
        
        await self.begin_transaction()
        try:
            for entity in entities:
                # Validate entity
                errors = entity.validate()
                if errors:
                    raise ValueError(f"Entity validation failed: {'; '.join(errors)}")
                
                query, params = self._build_update_query(entity)
                await self.execute(query, params)
                results.append(entity)
            
            await self.commit_transaction()
        except Exception:
            await self.rollback_transaction()
            raise
        
        return results
    
    async def bulk_delete(self, entity_class: Type[T], ids: List[str]) -> int:
        """Bulk delete multiple entities by IDs efficiently."""
        if not ids:
            return 0
        
        # Check connection
        self._check_connection()
        
        # Validate table name
        table = SQLValidator.validate_table_name(entity_class.table_name())
        
        # Create placeholders for all IDs
        placeholders = []
        params = {}
        
        for i, id_value in enumerate(ids):
            param_name = f"id_{i}"
            placeholders.append(f":{param_name}")
            params[param_name] = id_value
        
        # Sanitize parameters
        params = SQLValidator.validate_parameters(params)
        
        # Build and execute bulk delete query
        query = f"DELETE FROM {table} WHERE id IN ({', '.join(placeholders)})"
        await self.execute(query, params)
        
        # Return count of deleted records (simplified - actual count might need different approach)
        return len(ids)