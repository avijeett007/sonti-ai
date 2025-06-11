"""Unit tests for database connectors."""

import pytest
import pytest_asyncio
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

from knova_ai.db import get_connector, SQLiteConnector
from knova_ai.db.entities import User, Agent


class TestSQLiteConnector:
    """Test SQLite connector."""
    
    @pytest_asyncio.fixture
    async def db(self):
        """Create a temporary SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        connector = SQLiteConnector(db_path)
        await connector.connect()
        
        # Create test tables
        await connector.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                role TEXT DEFAULT 'member',
                org_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        await connector.execute("""
            CREATE TABLE agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                config TEXT NOT NULL,
                prompt_template TEXT,
                status TEXT DEFAULT 'active',
                org_id TEXT,
                user_id TEXT,
                webhook_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        yield connector
        
        await connector.disconnect()
        Path(db_path).unlink()
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connection and disconnection."""
        connector = SQLiteConnector(":memory:")
        
        # Test connection
        await connector.connect()
        assert connector._db is not None
        
        # Test disconnection
        await connector.disconnect()
        assert connector._db is None
    
    @pytest.mark.asyncio
    async def test_create_entity(self, db):
        """Test creating an entity."""
        user = User(
            email="test@example.com",
            first_name="John",
            last_name="Doe"
        )
        
        created_user = await db.create(user)
        
        assert created_user.id == user.id
        assert created_user.email == "test@example.com"
        assert created_user.first_name == "John"
        assert created_user.last_name == "Doe"
    
    @pytest.mark.asyncio
    async def test_get_entity(self, db):
        """Test getting an entity by ID."""
        # Create a user
        user = User(email="test@example.com")
        await db.create(user)
        
        # Get the user
        retrieved_user = await db.get(User, user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.email == "test@example.com"
        
        # Test non-existent user
        non_existent = await db.get(User, "non-existent-id")
        assert non_existent is None
    
    @pytest.mark.asyncio
    async def test_update_entity(self, db):
        """Test updating an entity."""
        # Create a user
        user = User(email="test@example.com", first_name="John")
        await db.create(user)
        
        # Update the user
        user.first_name = "Jane"
        user.last_name = "Smith"
        updated_user = await db.update(user)
        
        assert updated_user.first_name == "Jane"
        assert updated_user.last_name == "Smith"
        
        # Verify in database
        retrieved = await db.get(User, user.id)
        assert retrieved.first_name == "Jane"
        assert retrieved.last_name == "Smith"
    
    @pytest.mark.asyncio
    async def test_delete_entity(self, db):
        """Test deleting an entity."""
        # Create a user
        user = User(email="test@example.com")
        await db.create(user)
        
        # Delete the user
        result = await db.delete(User, user.id)
        assert result is True
        
        # Verify deletion
        retrieved = await db.get(User, user.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_list_entities(self, db):
        """Test listing entities."""
        # Create multiple users
        users = []
        for i in range(5):
            user = User(email=f"user{i}@example.com", role="member" if i < 3 else "admin")
            await db.create(user)
            users.append(user)
        
        # List all users
        all_users = await db.list(User)
        assert len(all_users) == 5
        
        # List with filter
        members = await db.list(User, filters={"role": "member"})
        assert len(members) == 3
        
        admins = await db.list(User, filters={"role": "admin"})
        assert len(admins) == 2
        
        # List with limit
        limited = await db.list(User, limit=2)
        assert len(limited) == 2
        
        # List with offset
        offset_users = await db.list(User, offset=3)
        assert len(offset_users) == 2
    
    @pytest.mark.asyncio
    async def test_count_entities(self, db):
        """Test counting entities."""
        # Create multiple users
        for i in range(5):
            user = User(email=f"user{i}@example.com", role="member" if i < 3 else "admin")
            await db.create(user)
        
        # Count all
        total = await db.count(User)
        assert total == 5
        
        # Count with filter
        member_count = await db.count(User, filters={"role": "member"})
        assert member_count == 3
        
        admin_count = await db.count(User, filters={"role": "admin"})
        assert admin_count == 2
    
    @pytest.mark.asyncio
    async def test_transaction(self, db):
        """Test transaction handling."""
        # Test successful transaction
        await db.begin_transaction()
        
        user1 = User(email="user1@example.com")
        await db.create(user1)
        
        user2 = User(email="user2@example.com")
        await db.create(user2)
        
        await db.commit_transaction()
        
        # Verify both users exist
        assert await db.get(User, user1.id) is not None
        assert await db.get(User, user2.id) is not None
        
        # Test rollback
        await db.begin_transaction()
        
        user3 = User(email="user3@example.com")
        await db.create(user3)
        
        await db.rollback_transaction()
        
        # Verify user3 doesn't exist
        assert await db.get(User, user3.id) is None
    
    @pytest.mark.asyncio
    async def test_json_fields(self, db):
        """Test handling of JSON fields."""
        config = {
            "llm": {"provider": "openai", "model": "gpt-4"},
            "stt": {"provider": "deepgram"},
            "tts": {"provider": "elevenlabs"}
        }
        
        agent = Agent(
            name="Test Agent",
            config=config,
            prompt_template="Test prompt"
        )
        
        # Create agent
        created = await db.create(agent)
        assert created.config == config
        
        # Retrieve and verify
        retrieved = await db.get(Agent, agent.id)
        assert retrieved.config == config
        assert retrieved.config["llm"]["model"] == "gpt-4"


class TestConnectorFactory:
    """Test the get_connector factory function."""
    
    def test_get_sqlite_connector(self):
        """Test getting SQLite connector."""
        connector = get_connector("sqlite", ":memory:")
        assert isinstance(connector, SQLiteConnector)
        
        # Test with file path
        connector = get_connector("sqlite", "/tmp/test.db")
        assert isinstance(connector, SQLiteConnector)
    
    def test_get_postgresql_connector(self):
        """Test getting PostgreSQL connector."""
        from knova_ai.db.connectors.postgres import PostgreSQLConnector
        
        connector = get_connector("postgresql", "postgresql://localhost/test")
        assert isinstance(connector, PostgreSQLConnector)
        
        # Test alias
        connector = get_connector("postgres", "postgresql://localhost/test")
        assert isinstance(connector, PostgreSQLConnector)
    
    def test_get_supabase_connector(self):
        """Test getting Supabase connector."""
        from knova_ai.db.connectors.supabase import SupabaseConnector
        
        connector = get_connector("supabase", "postgresql://test.supabase.co/test")
        assert isinstance(connector, SupabaseConnector)
    
    def test_get_neondb_connector(self):
        """Test getting NeonDB connector."""
        from knova_ai.db.connectors.neondb import NeonDBConnector
        
        connector = get_connector("neondb", "postgresql://test.neon.tech/test")
        assert isinstance(connector, NeonDBConnector)
        
        # Test alias
        connector = get_connector("neon", "postgresql://test.neon.tech/test")
        assert isinstance(connector, NeonDBConnector)
    
    def test_invalid_db_type(self):
        """Test invalid database type."""
        with pytest.raises(ValueError) as exc_info:
            get_connector("invalid", "some://url")
        
        assert "Unsupported database type" in str(exc_info.value)


class TestConnectorUtils:
    """Test connector utility methods."""
    
    @pytest.mark.asyncio
    async def test_build_where_clause(self):
        """Test WHERE clause building."""
        connector = SQLiteConnector(":memory:")
        
        # No filters
        where, params = connector.build_where_clause()
        assert where == ""
        assert params == {}
        
        # Single filter
        where, params = connector.build_where_clause({"status": "active"})
        assert where == "WHERE status = :status"
        assert params == {"status": "active"}
        
        # Multiple filters
        where, params = connector.build_where_clause({
            "status": "active",
            "role": "admin"
        })
        assert "status = :status" in where
        assert "role = :role" in where
        assert params == {"status": "active", "role": "admin"}
        
        # NULL value
        where, params = connector.build_where_clause({"deleted_at": None})
        assert "deleted_at IS NULL" in where
        assert params == {}
        
        # List value (IN clause)
        where, params = connector.build_where_clause({"role": ["admin", "member"]})
        assert "role IN (:role_0, :role_1)" in where
        assert params == {"role_0": "admin", "role_1": "member"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])