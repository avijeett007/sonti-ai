"""Security tests for the Knova AI SDK database layer."""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
import aiosqlite

from knova_ai.db.connectors.sqlite import SQLiteConnector
from knova_ai.db.entities.agent import Agent
from knova_ai.db.utils.validation import ValidationError
from knova_ai.utils.encryption import EncryptionManager, encrypt_sensitive_data, decrypt_sensitive_data


class TestSQLInjectionPrevention:
    """Test SQL injection prevention measures."""
    
    @pytest.mark.asyncio
    async def test_table_name_injection_prevention(self):
        """Test that malicious table names are rejected."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create a malicious agent with SQL injection in table name
        class MaliciousAgent(Agent):
            @classmethod
            def table_name(cls):
                return "agents; DROP TABLE users; --"
        
        agent = MaliciousAgent(
            name="Test Agent",
            config={"llm": {"model": "test"}},
            prompt_template="Test prompt"
        )
        
        # Should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            await connector.create(agent)
        
        assert "Invalid table name" in str(exc_info.value)
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_column_name_injection_prevention(self):
        """Test that malicious column names are rejected."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create agent table first
        await connector.execute("""
            CREATE TABLE agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                prompt TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Try to create agent with malicious field name
        class MaliciousAgent(Agent):
            def to_dict(self):
                data = super().to_dict()
                # Add malicious column name
                data["name'; DROP TABLE agents; --"] = "malicious"
                return data
        
        agent = MaliciousAgent(
            name="Test Agent",
            config={"llm": {"model": "test"}},
            prompt_template="Test prompt"
        )
        
        # Should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            await connector.create(agent)
        
        assert "Invalid column name" in str(exc_info.value)
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_parameter_sanitization(self):
        """Test that parameters are properly sanitized."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create agent table with config column
        await connector.execute("""
            CREATE TABLE agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                prompt_template TEXT,
                config TEXT,
                status TEXT,
                org_id TEXT,
                user_id TEXT,
                webhook_id TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Create agent with potentially malicious content
        agent = Agent(
            name="Test'; DROP TABLE agents; --",
            config={"llm": {"model": "test"}},
            prompt_template="Test prompt with \x00 null byte"
        )
        
        # Should sanitize and create successfully
        created = await connector.create(agent)
        assert created.name == "Test'; DROP TABLE agents; --"  # Name preserved but safe
        
        # Verify null bytes were sanitized from prompt_template
        retrieved = await connector.get(Agent, created.id)
        assert "\x00" not in retrieved.prompt_template  # Null byte should be removed
        assert "Test prompt with  null byte" == retrieved.prompt_template
        
        # Verify table still exists
        result = await connector.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='agents'"
        )
        assert result is not None
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_reserved_keyword_prevention(self):
        """Test that reserved SQL keywords cannot be used as identifiers."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Test reserved keywords as table names
        class SelectAgent(Agent):
            @classmethod
            def table_name(cls):
                return "SELECT"
        
        agent = SelectAgent(name="Test", config={"llm": {"model": "test"}}, prompt_template="Test")
        
        with pytest.raises(ValidationError) as exc_info:
            await connector.create(agent)
        
        assert "reserved SQL keyword" in str(exc_info.value)
        await connector.disconnect()


class TestEncryptionSecurity:
    """Test encryption security features."""
    
    def test_encryption_key_persistence(self):
        """Test that encryption keys persist across instances."""
        # First instance
        manager1 = EncryptionManager()
        test_data = "sensitive information"
        encrypted = manager1.encrypt(test_data)
        
        # Second instance (simulating app restart)
        manager2 = EncryptionManager()
        decrypted = manager2.decrypt(encrypted)
        
        assert decrypted == test_data
    
    def test_encryption_key_from_environment(self):
        """Test loading encryption key from environment variable."""
        # Generate a test key
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key()
        
        # Set environment variable
        os.environ['KNOVA_ENCRYPTION_KEY'] = test_key.decode()
        
        try:
            # Create new manager instance
            manager = EncryptionManager()
            manager._cipher = None  # Force re-initialization
            manager._initialize_cipher()
            
            # Test encryption/decryption
            test_data = "test data"
            encrypted = manager.encrypt(test_data)
            decrypted = manager.decrypt(encrypted)
            
            assert decrypted == test_data
        finally:
            # Clean up
            if 'KNOVA_ENCRYPTION_KEY' in os.environ:
                del os.environ['KNOVA_ENCRYPTION_KEY']
    
    def test_encryption_key_file_permissions(self):
        """Test that encryption key file has proper permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set custom key path
            key_path = Path(tmpdir) / 'test_key'
            os.environ['KNOVA_ENCRYPTION_KEY_PATH'] = str(key_path)
            
            try:
                manager = EncryptionManager()
                manager._cipher = None
                manager._initialize_cipher()
                
                # Check file permissions (Unix-like systems only)
                if hasattr(os, 'stat'):
                    stats = os.stat(key_path)
                    mode = stats.st_mode & 0o777
                    # Should be readable/writable by owner only (0o600)
                    assert mode == 0o600
            finally:
                if 'KNOVA_ENCRYPTION_KEY_PATH' in os.environ:
                    del os.environ['KNOVA_ENCRYPTION_KEY_PATH']
    
    def test_invalid_encrypted_data_handling(self):
        """Test handling of invalid encrypted data."""
        manager = EncryptionManager()
        
        # Test with invalid base64
        with pytest.raises(Exception):
            manager.decrypt("not-valid-base64!@#$")
        
        # Test with valid base64 but invalid encryption
        with pytest.raises(Exception):
            manager.decrypt("dGVzdCBkYXRh")  # "test data" in base64
    
    def test_key_rotation(self):
        """Test encryption key rotation."""
        manager = EncryptionManager()
        
        # Encrypt with old key
        test_data = "sensitive data"
        encrypted_old = manager.encrypt(test_data)
        
        # Rotate key
        new_key = manager.rotate_key()
        assert new_key is not None
        
        # Encrypt with new key
        encrypted_new = manager.encrypt(test_data)
        
        # Old encrypted data should not decrypt with new key
        with pytest.raises(Exception):
            manager.decrypt(encrypted_old)
        
        # New encrypted data should decrypt properly
        decrypted = manager.decrypt(encrypted_new)
        assert decrypted == test_data


class TestInputValidation:
    """Test input validation security."""
    
    @pytest.mark.asyncio
    async def test_email_validation(self):
        """Test email validation in entities."""
        from knova_ai.db.base import BaseEntity
        from dataclasses import dataclass
        
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create a test entity with email field
        @dataclass
        class User(BaseEntity):
            name: str = ""
            email: str = ""
            
            @classmethod
            def table_name(cls):
                return "users"
        
        # Test invalid email
        user = User(
            name="Test User",
            email="not-an-email"
        )
        
        errors = user.validate()
        assert any("Invalid email" in error for error in errors)
        
        # Test valid email
        user2 = User(
            name="Test User",
            email="test@example.com"
        )
        
        errors2 = user2.validate()
        assert not any("Invalid email" in error for error in errors2)
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_string_length_validation(self):
        """Test string length limits."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create agent with excessively long name
        long_name = "A" * 10001  # Over 10000 character limit
        agent = Agent(
            name=long_name,
            config={"llm": {"model": "test"}},
            prompt_template="Test"
        )
        
        errors = agent.validate()
        assert any("exceeds maximum length" in error for error in errors)
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_null_byte_prevention(self):
        """Test null byte sanitization in database operations."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create agents table
        await connector.execute("""
            CREATE TABLE agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                prompt_template TEXT,
                config TEXT,
                status TEXT,
                org_id TEXT,
                user_id TEXT,
                webhook_id TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Create agent with null bytes
        agent = Agent(
            name="Test\x00Agent",
            config={"llm": {"model": "test"}},
            prompt_template="Test\x00Prompt"
        )
        
        # Null bytes should not cause validation errors anymore
        errors = agent.validate()
        assert not any("contains null bytes" in error for error in errors)
        
        # Create the agent - null bytes should be sanitized
        created = await connector.create(agent)
        
        # Retrieve and verify null bytes were removed
        retrieved = await connector.get(Agent, created.id)
        assert "\x00" not in retrieved.name
        assert "\x00" not in retrieved.prompt_template
        assert retrieved.name == "TestAgent"  # Null byte removed
        assert retrieved.prompt_template == "TestPrompt"  # Null byte removed
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_limit_offset_validation(self):
        """Test LIMIT and OFFSET parameter validation."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Test negative limit
        with pytest.raises(ValidationError):
            await connector.list(Agent, limit=-1)
        
        # Test excessive limit
        with pytest.raises(ValidationError):
            await connector.list(Agent, limit=10001)
        
        # Test negative offset
        with pytest.raises(ValidationError):
            await connector.list(Agent, offset=-1)
        
        await connector.disconnect()


class TestConnectionSecurity:
    """Test connection security features."""
    
    @pytest.mark.asyncio
    async def test_connection_state_validation(self):
        """Test that operations fail without connection."""
        connector = SQLiteConnector(':memory:')
        # Don't connect
        
        agent = Agent(name="Test", config={"llm": {"model": "test"}}, prompt_template="Test")
        
        # All operations should fail
        with pytest.raises(RuntimeError) as exc_info:
            await connector.create(agent)
        assert "Not connected" in str(exc_info.value)
        
        with pytest.raises(RuntimeError) as exc_info:
            await connector.get(Agent, "test-id")
        assert "Not connected" in str(exc_info.value)
        
        with pytest.raises(RuntimeError) as exc_info:
            await connector.update(agent)
        assert "Not connected" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_concurrent_access_safety(self):
        """Test thread safety with concurrent operations."""
        connector = SQLiteConnector(':memory:')
        await connector.connect()
        
        # Create agents table with all required columns
        await connector.execute("""
            CREATE TABLE agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                prompt_template TEXT,
                config TEXT,
                status TEXT,
                org_id TEXT,
                user_id TEXT,
                webhook_id TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Define concurrent operations
        async def create_agent(i):
            agent = Agent(
                name=f"Agent {i}",
                config={"llm": {"model": "test"}},
                prompt_template=f"Prompt {i}"
            )
            return await connector.create(agent)
        
        # Run multiple operations concurrently
        tasks = [create_agent(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all agents were created
        assert len(results) == 10
        
        # Check database consistency
        count_result = await connector.fetch_one("SELECT COUNT(*) as count FROM agents")
        assert count_result['count'] == 10
        
        await connector.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])