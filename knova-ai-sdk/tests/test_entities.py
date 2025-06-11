"""Unit tests for database entities."""

import pytest
from datetime import datetime
import json

from knova_ai.db.entities import (
    User, Agent, Workflow, KnowledgeBase, Document,
    SipTrunk, PhoneNumber, Webhook, CallLog, UsageLog
)


class TestUser:
    """Test User entity."""
    
    def test_user_creation(self):
        """Test creating a user entity."""
        user = User(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            role="member"
        )
        
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.role == "member"
        assert user.id is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_user_validation(self):
        """Test user validation."""
        # Valid user
        user = User(email="test@example.com")
        errors = user.validate()
        assert len(errors) == 0
        
        # Invalid email
        user = User(email="invalid-email")
        errors = user.validate()
        assert any("Invalid email" in e for e in errors)
        
        # Invalid role
        user = User(email="test@example.com", role="invalid")
        errors = user.validate()
        assert any("Invalid role" in e for e in errors)
    
    def test_user_full_name(self):
        """Test full name property."""
        user = User(email="test@example.com", first_name="John", last_name="Doe")
        assert user.full_name == "John Doe"
        
        user = User(email="test@example.com", first_name="John")
        assert user.full_name == "John"
        
        user = User(email="test@example.com")
        assert user.full_name == "test"
    
    def test_user_serialization(self):
        """Test user serialization."""
        user = User(
            email="test@example.com",
            first_name="John",
            last_name="Doe"
        )
        
        data = user.to_dict()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        
        # Test deserialization
        user2 = User.from_dict(data)
        assert user2.email == user.email
        assert user2.first_name == user.first_name
        assert user2.last_name == user.last_name


class TestAgent:
    """Test Agent entity."""
    
    def test_agent_creation(self):
        """Test creating an agent entity."""
        config = {
            "llm": {"provider": "openai", "model": "gpt-4"},
            "stt": {"provider": "deepgram"},
            "tts": {"provider": "elevenlabs"}
        }
        
        agent = Agent(
            name="Test Agent",
            config=config,
            prompt_template="You are a helpful assistant",
            status="active"
        )
        
        assert agent.name == "Test Agent"
        assert agent.config == config
        assert agent.prompt_template == "You are a helpful assistant"
        assert agent.status == "active"
    
    def test_agent_validation(self):
        """Test agent validation."""
        # Valid agent
        agent = Agent(name="Test", config={"llm": {}})
        errors = agent.validate()
        assert len(errors) == 0
        
        # Missing name
        agent = Agent(config={"llm": {}})
        errors = agent.validate()
        assert any("name is required" in e for e in errors)
        
        # Missing config
        agent = Agent(name="Test")
        errors = agent.validate()
        assert any("configuration is required" in e for e in errors)
        
        # Invalid status
        agent = Agent(name="Test", config={"llm": {}}, status="invalid")
        errors = agent.validate()
        assert any("Invalid status" in e for e in errors)
    
    def test_agent_is_active(self):
        """Test is_active method."""
        agent = Agent(name="Test", config={"llm": {}}, status="active")
        assert agent.is_active() is True
        
        agent.status = "inactive"
        assert agent.is_active() is False


class TestWorkflow:
    """Test Workflow entity."""
    
    def test_workflow_creation(self):
        """Test creating a workflow entity."""
        definition = {
            "nodes": [
                {"id": "1", "type": "agent", "data": {"name": "Agent 1"}},
                {"id": "2", "type": "agent", "data": {"name": "Agent 2"}}
            ],
            "edges": [
                {"source": "1", "target": "2"}
            ]
        }
        
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
            definition=definition
        )
        
        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert workflow.definition == definition
        assert workflow.version == 1
        assert workflow.is_active is True
    
    def test_workflow_validation(self):
        """Test workflow validation."""
        # Valid workflow
        workflow = Workflow(
            name="Test",
            definition={"nodes": [], "edges": []}
        )
        errors = workflow.validate()
        assert len(errors) == 0
        
        # Missing definition
        workflow = Workflow(name="Test")
        errors = workflow.validate()
        assert any("definition is required" in e for e in errors)
        
        # Missing nodes
        workflow = Workflow(name="Test", definition={"edges": []})
        errors = workflow.validate()
        assert any("must contain 'nodes'" in e for e in errors)
        
        # Invalid nodes type
        workflow = Workflow(name="Test", definition={"nodes": "invalid", "edges": []})
        errors = workflow.validate()
        assert any("nodes must be a list" in e for e in errors)
    
    def test_workflow_node_edge_count(self):
        """Test node and edge count methods."""
        definition = {
            "nodes": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
            "edges": [{"source": "1", "target": "2"}, {"source": "2", "target": "3"}]
        }
        
        workflow = Workflow(name="Test", definition=definition)
        assert workflow.get_node_count() == 3
        assert workflow.get_edge_count() == 2
    
    def test_workflow_version_increment(self):
        """Test version increment."""
        workflow = Workflow(name="Test", definition={"nodes": [], "edges": []})
        assert workflow.version == 1
        
        workflow.increment_version()
        assert workflow.version == 2


class TestKnowledgeBase:
    """Test KnowledgeBase entity."""
    
    def test_knowledge_base_creation(self):
        """Test creating a knowledge base entity."""
        vector_config = {
            "provider": "qdrant",
            "collection_name": "test_collection",
            "api_key": "test_key"
        }
        
        kb = KnowledgeBase(
            name="Test KB",
            agent_id="agent-123",
            vector_store_config=vector_config
        )
        
        assert kb.name == "Test KB"
        assert kb.agent_id == "agent-123"
        assert kb.vector_store_config == vector_config
    
    def test_knowledge_base_validation(self):
        """Test knowledge base validation."""
        # Valid KB
        kb = KnowledgeBase(name="Test")
        errors = kb.validate()
        assert len(errors) == 0
        
        # Missing name
        kb = KnowledgeBase()
        errors = kb.validate()
        assert any("name is required" in e for e in errors)
        
        # Invalid provider
        kb = KnowledgeBase(
            name="Test",
            vector_store_config={"provider": "invalid"}
        )
        errors = kb.validate()
        assert any("Invalid vector store provider" in e for e in errors)
    
    def test_get_vector_provider(self):
        """Test get_vector_provider method."""
        kb = KnowledgeBase(
            name="Test",
            vector_store_config={"provider": "qdrant"}
        )
        assert kb.get_vector_provider() == "qdrant"
        
        kb = KnowledgeBase(name="Test")
        assert kb.get_vector_provider() is None
    
    def test_get_collection_name(self):
        """Test get_collection_name method."""
        kb = KnowledgeBase(
            name="Test",
            vector_store_config={"collection_name": "custom_collection"}
        )
        assert kb.get_collection_name() == "custom_collection"
        
        kb = KnowledgeBase(name="Test")
        assert kb.get_collection_name().startswith("kb_")


class TestDocument:
    """Test Document entity."""
    
    def test_document_creation(self):
        """Test creating a document entity."""
        doc = Document(
            knowledge_base_id="kb-123",
            filename="test.pdf",
            content="Test content",
            embedding_id="emb-123",
            metadata={"author": "John Doe"}
        )
        
        assert doc.knowledge_base_id == "kb-123"
        assert doc.filename == "test.pdf"
        assert doc.content == "Test content"
        assert doc.embedding_id == "emb-123"
        assert doc.metadata == {"author": "John Doe"}
    
    def test_document_validation(self):
        """Test document validation."""
        # Valid document
        doc = Document(knowledge_base_id="kb-123", filename="test.pdf")
        errors = doc.validate()
        assert len(errors) == 0
        
        # Missing KB ID
        doc = Document(filename="test.pdf")
        errors = doc.validate()
        assert any("Knowledge base ID is required" in e for e in errors)
        
        # Missing filename
        doc = Document(knowledge_base_id="kb-123")
        errors = doc.validate()
        assert any("Filename is required" in e for e in errors)
    
    def test_get_file_extension(self):
        """Test get_file_extension method."""
        doc = Document(knowledge_base_id="kb-123", filename="test.pdf")
        assert doc.get_file_extension() == "pdf"
        
        doc = Document(knowledge_base_id="kb-123", filename="document.txt")
        assert doc.get_file_extension() == "txt"
        
        doc = Document(knowledge_base_id="kb-123", filename="noextension")
        assert doc.get_file_extension() == ""
    
    def test_get_mime_type(self):
        """Test get_mime_type method."""
        doc = Document(knowledge_base_id="kb-123", filename="test.pdf")
        assert doc.get_mime_type() == "application/pdf"
        
        doc = Document(knowledge_base_id="kb-123", filename="test.txt")
        assert doc.get_mime_type() == "text/plain"
        
        doc = Document(knowledge_base_id="kb-123", filename="test.unknown")
        assert doc.get_mime_type() == "application/octet-stream"
    
    def test_get_size_kb(self):
        """Test get_size_kb method."""
        doc = Document(
            knowledge_base_id="kb-123",
            filename="test.txt",
            content="A" * 1024  # 1KB of 'A's
        )
        assert doc.get_size_kb() == 1.0
        
        doc = Document(knowledge_base_id="kb-123", filename="test.txt")
        assert doc.get_size_kb() == 0.0


class TestWebhook:
    """Test Webhook entity."""
    
    def test_webhook_creation(self):
        """Test creating a webhook entity."""
        webhook = Webhook(
            url="https://example.com/webhook",
            events=["agent.started", "agent.stopped"],
            headers={"Authorization": "Bearer token"},
            secret="webhook-secret"
        )
        
        assert webhook.url == "https://example.com/webhook"
        assert webhook.events == ["agent.started", "agent.stopped"]
        assert webhook.headers == {"Authorization": "Bearer token"}
        assert webhook.secret == "webhook-secret"
        assert webhook.is_active is True
    
    def test_webhook_validation(self):
        """Test webhook validation."""
        # Valid webhook
        webhook = Webhook(
            url="https://example.com/webhook",
            events=["agent.started"]
        )
        errors = webhook.validate()
        assert len(errors) == 0
        
        # Missing URL
        webhook = Webhook(events=["agent.started"])
        errors = webhook.validate()
        assert any("URL is required" in e for e in errors)
        
        # Invalid URL
        webhook = Webhook(url="not-a-url", events=["agent.started"])
        errors = webhook.validate()
        assert any("must start with http://" in e for e in errors)
        
        # No events
        webhook = Webhook(url="https://example.com")
        errors = webhook.validate()
        assert any("At least one event" in e for e in errors)
        
        # Invalid event
        webhook = Webhook(url="https://example.com", events=["invalid.event"])
        errors = webhook.validate()
        assert any("Invalid event" in e for e in errors)
    
    def test_subscribes_to(self):
        """Test subscribes_to method."""
        webhook = Webhook(
            url="https://example.com",
            events=["agent.started", "agent.stopped"]
        )
        
        assert webhook.subscribes_to("agent.started") is True
        assert webhook.subscribes_to("agent.stopped") is True
        assert webhook.subscribes_to("workflow.started") is False
    
    def test_retry_config(self):
        """Test retry configuration methods."""
        webhook = Webhook(
            url="https://example.com",
            events=["agent.started"]
        )
        
        assert webhook.get_max_attempts() == 3
        assert webhook.get_backoff_seconds() == [1, 5, 30]
        
        # Custom retry config
        webhook = Webhook(
            url="https://example.com",
            events=["agent.started"],
            retry_config={"max_attempts": 5, "backoff_seconds": [2, 10, 60]}
        )
        
        assert webhook.get_max_attempts() == 5
        assert webhook.get_backoff_seconds() == [2, 10, 60]


if __name__ == "__main__":
    pytest.main([__file__])