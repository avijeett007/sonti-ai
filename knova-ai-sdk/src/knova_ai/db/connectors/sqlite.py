"""SQLite database connector."""

import aiosqlite
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from .base import BaseConnectorImpl


class SQLiteConnector(BaseConnectorImpl):
    """SQLite database connector implementation."""
    
    def __init__(self, connection_string: str, **kwargs):
        """Initialize SQLite connector.
        
        Args:
            connection_string: Path to SQLite database file or ':memory:'
            **kwargs: Additional options like check_same_thread, timeout
        """
        super().__init__(connection_string, **kwargs)
        self.db_path = connection_string
        self._db = None
        
        # SQLite specific options
        self.check_same_thread = kwargs.get('check_same_thread', False)
        self.timeout = kwargs.get('timeout', 5.0)
        self.isolation_level = kwargs.get('isolation_level', None)
        
        # Enable JSON1 extension
        self.enable_json = kwargs.get('enable_json', True)
    
    async def connect(self):
        """Establish connection to SQLite database."""
        # Create directory if needed
        if self.db_path != ':memory:':
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._db = await aiosqlite.connect(
            self.db_path,
            check_same_thread=self.check_same_thread,
            timeout=self.timeout,
            isolation_level=self.isolation_level
        )
        
        # Enable foreign keys
        await self._db.execute("PRAGMA foreign_keys = ON")
        
        # Set journal mode for better concurrency
        await self._db.execute("PRAGMA journal_mode = WAL")
        
        # Enable JSON1 extension functions
        if self.enable_json:
            await self._db.execute("PRAGMA compile_options")
        
        await self._db.commit()
        self._logger.info(f"Connected to SQLite database: {self.db_path}")
    
    async def disconnect(self):
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None
            self._logger.info("Disconnected from SQLite database")
    
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a raw SQL query."""
        if not self._db:
            raise RuntimeError("Not connected to database")
        
        # Convert dict params to SQLite format
        sqlite_params = self._convert_params(params) if params else {}
        
        cursor = await self._db.execute(query, sqlite_params)
        await self._db.commit()
        
        return cursor.lastrowid
    
    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Execute a query and fetch one result."""
        if not self._db:
            raise RuntimeError("Not connected to database")
        
        sqlite_params = self._convert_params(params) if params else {}
        
        cursor = await self._db.execute(query, sqlite_params)
        row = await cursor.fetchone()
        
        if row:
            # Convert Row to dict
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        
        return None
    
    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and fetch all results."""
        if not self._db:
            raise RuntimeError("Not connected to database")
        
        sqlite_params = self._convert_params(params) if params else {}
        
        cursor = await self._db.execute(query, sqlite_params)
        rows = await cursor.fetchall()
        
        if rows:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        
        return []
    
    async def begin_transaction(self):
        """Begin a database transaction."""
        if not self._db:
            raise RuntimeError("Not connected to database")
        
        await self._db.execute("BEGIN")
        self._transaction = True
    
    async def commit_transaction(self):
        """Commit the current transaction."""
        if not self._db:
            raise RuntimeError("Not connected to database")
        
        await self._db.commit()
        self._transaction = False
    
    async def rollback_transaction(self):
        """Rollback the current transaction."""
        if not self._db:
            raise RuntimeError("Not connected to database")
        
        await self._db.rollback()
        self._transaction = False
    
    def _convert_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert params from :name format to SQLite's :name format."""
        # SQLite uses the same parameter format, just serialize complex types
        converted = {}
        for key, value in params.items():
            converted[key] = self._serialize_value(value)
        return converted
    
    def _build_insert_query(self, entity) -> tuple[str, Dict[str, Any]]:
        """Build INSERT query for SQLite (handles RETURNING clause)."""
        table = entity.table_name()
        data = entity.to_dict()
        
        columns = list(data.keys())
        placeholders = [f":{col}" for col in columns]
        
        # SQLite doesn't support RETURNING * in older versions
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        return query, data
    
    def _build_update_query(self, entity) -> tuple[str, Dict[str, Any]]:
        """Build UPDATE query for SQLite (handles RETURNING clause)."""
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
        """
        
        data['id'] = entity_id
        return query, data
    
    async def create(self, entity):
        """Create entity (SQLite-specific implementation)."""
        # Validate entity
        errors = entity.validate()
        if errors:
            raise ValueError(f"Entity validation failed: {'; '.join(errors)}")
        
        query, params = self._build_insert_query(entity)
        await self.execute(query, params)
        
        # Fetch the created entity
        return await self.get(type(entity), entity.id)
    
    async def update(self, entity):
        """Update entity (SQLite-specific implementation)."""
        # Validate entity
        errors = entity.validate()
        if errors:
            raise ValueError(f"Entity validation failed: {'; '.join(errors)}")
        
        query, params = self._build_update_query(entity)
        await self.execute(query, params)
        
        # Fetch the updated entity
        return await self.get(type(entity), entity.id)
    
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