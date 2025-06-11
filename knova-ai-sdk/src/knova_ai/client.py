"""Main SDK client for Knova AI"""

import os
import asyncio
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

import aiohttp
from pydantic import BaseModel, Field

from .license import LicenseValidator
from .telemetry import TelemetryCollector
from .config import ConfigManager
from .agents.voice import VoiceAgent
from .agents.workflow import WorkflowAgent
from .db import get_connector, BaseConnector
from .db.entities import Agent, User, KnowledgeBase, Document
from .db.migrations import MigrationManager
from .db.utils import get_database_type, get_env_database_url


class KnovaAI:
    """Main client for interacting with Knova AI platform"""
    
    def __init__(
        self,
        license_key: str,
        api_url: Optional[str] = None,
        telemetry_enabled: bool = True,
        config_dir: Optional[Path] = None,
        database_url: Optional[str] = None,
        database_type: Optional[str] = None
    ):
        """
        Initialize Knova AI client
        
        Args:
            license_key: Your Knova AI license key (free tier available)
            api_url: Optional API URL override
            telemetry_enabled: Enable/disable telemetry collection
            config_dir: Optional directory for local configuration storage
            database_url: Optional database connection URL
            database_type: Optional database type (sqlite, postgresql, supabase, neondb)
        """
        self.license_key = license_key
        self.api_url = api_url or os.getenv("KNOVA_API_URL", "https://api.knova.ai")
        self.telemetry_enabled = telemetry_enabled
        
        # Initialize components
        self.config = ConfigManager(config_dir or Path.home() / ".knova")
        self.license_validator = LicenseValidator(self.api_url, license_key)
        self.telemetry = TelemetryCollector(self.api_url, license_key) if telemetry_enabled else None
        
        # Database configuration
        self.database_url = database_url or get_env_database_url() or str(self.config.config_dir / "knova.db")
        self.database_type = database_type or get_database_type(self.database_url)
        self.db: Optional[BaseConnector] = None
        self.migration_manager: Optional[MigrationManager] = None
        
        # Session for API calls
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Validate license on init
        self._license_valid = False
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def initialize(self):
        """Initialize the client and validate license"""
        self._session = aiohttp.ClientSession()
        
        # Initialize database connection
        self.db = get_connector(self.database_type, self.database_url)
        await self.db.connect()
        
        # Initialize migration manager
        self.migration_manager = MigrationManager(self.db)
        
        # Run migrations if needed
        await self.migration_manager.migrate()
        
        # Validate license
        try:
            self._license_valid = await self.license_validator.validate()
            if not self._license_valid:
                raise ValueError("Invalid license key")
        except Exception as e:
            # Check if we have a cached valid license for offline mode
            if self.config.has_valid_cached_license(self.license_key):
                self._license_valid = True
            else:
                raise ValueError(f"License validation failed: {e}")
                
        # Start telemetry if enabled
        if self.telemetry:
            await self.telemetry.start()
            
    async def close(self):
        """Close the client and cleanup resources"""
        if self._session:
            await self._session.close()
            
        if self.telemetry:
            await self.telemetry.stop()
            
        if self.db:
            await self.db.disconnect()
            
    def create_agent(
        self,
        name: str,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4",
        stt_provider: str = "deepgram",
        tts_provider: str = "elevenlabs",
        prompt: Optional[str] = None,
        tools: Optional[List[str]] = None,
        knowledge_base_id: Optional[str] = None,
        **kwargs
    ) -> VoiceAgent:
        """
        Create a new voice agent
        
        Args:
            name: Agent name
            llm_provider: LLM provider (openai, google, azure, aws, anthropic)
            llm_model: Model name for the LLM
            stt_provider: Speech-to-text provider
            tts_provider: Text-to-speech provider
            prompt: Optional custom prompt template
            tools: Optional list of tool/function names
            knowledge_base_id: Optional knowledge base ID
            **kwargs: Additional provider-specific configuration
            
        Returns:
            VoiceAgent instance
        """
        agent_config = {
            "name": name,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "stt_provider": stt_provider,
            "tts_provider": tts_provider,
            "prompt": prompt,
            "tools": tools or [],
            "knowledge_base_id": knowledge_base_id,
            **kwargs
        }
        
        # Track agent creation
        if self.telemetry:
            asyncio.create_task(self.telemetry.track_event("agent_created", agent_config))
            
        return VoiceAgent(self, agent_config)
        
    def create_workflow(
        self,
        name: str,
        description: Optional[str] = None
    ) -> WorkflowAgent:
        """
        Create a new multi-agent workflow
        
        Args:
            name: Workflow name
            description: Optional workflow description
            
        Returns:
            WorkflowAgent instance
        """
        workflow_config = {
            "name": name,
            "description": description,
            "nodes": [],
            "edges": []
        }
        
        # Track workflow creation
        if self.telemetry:
            asyncio.create_task(self.telemetry.track_event("workflow_created", workflow_config))
            
        return WorkflowAgent(self, workflow_config)
        
    async def deploy_agent(self, agent: VoiceAgent) -> Dict[str, Any]:
        """
        Deploy an agent to the platform
        
        Args:
            agent: VoiceAgent instance to deploy
            
        Returns:
            Deployment information including endpoints
        """
        if not self._license_valid:
            raise ValueError("Invalid license key")
            
        # Prepare deployment request
        deployment_data = agent.to_deployment_config()
        
        # Make API call to deploy
        async with self._session.post(
            f"{self.api_url}/v1/agents/deploy",
            json=deployment_data,
            headers={"Authorization": f"Bearer {self.license_key}"}
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise ValueError(f"Deployment failed: {error}")
                
            result = await response.json()
            
        # Track deployment
        if self.telemetry:
            await self.telemetry.track_event("agent_deployed", {
                "agent_id": result.get("agent_id"),
                "name": agent.name
            })
            
        return result
        
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents for this license"""
        if not self._license_valid:
            raise ValueError("Invalid license key")
            
        async with self._session.get(
            f"{self.api_url}/v1/agents",
            headers={"Authorization": f"Bearer {self.license_key}"}
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise ValueError(f"Failed to list agents: {error}")
                
            return await response.json()
            
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        if not self._license_valid:
            raise ValueError("Invalid license key")
            
        async with self._session.delete(
            f"{self.api_url}/v1/agents/{agent_id}",
            headers={"Authorization": f"Bearer {self.license_key}"}
        ) as response:
            if response.status != 204:
                error = await response.text()
                raise ValueError(f"Failed to delete agent: {error}")
                
        # Track deletion
        if self.telemetry:
            await self.telemetry.track_event("agent_deleted", {"agent_id": agent_id})
            
        return True
        
    async def create_knowledge_base(
        self,
        name: str,
        description: Optional[str] = None,
        vector_store: str = "qdrant"
    ) -> Dict[str, Any]:
        """Create a new knowledge base"""
        if not self._license_valid:
            raise ValueError("Invalid license key")
            
        kb_data = {
            "name": name,
            "description": description,
            "vector_store": vector_store
        }
        
        async with self._session.post(
            f"{self.api_url}/v1/knowledge-bases",
            json=kb_data,
            headers={"Authorization": f"Bearer {self.license_key}"}
        ) as response:
            if response.status != 201:
                error = await response.text()
                raise ValueError(f"Failed to create knowledge base: {error}")
                
            return await response.json()
            
    async def upload_document(
        self,
        knowledge_base_id: str,
        file_path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload a document to a knowledge base"""
        if not self._license_valid:
            raise ValueError("Invalid license key")
            
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=file_path.name)
            if metadata:
                data.add_field('metadata', str(metadata))
                
            async with self._session.post(
                f"{self.api_url}/v1/knowledge-bases/{knowledge_base_id}/documents",
                data=data,
                headers={"Authorization": f"Bearer {self.license_key}"}
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    raise ValueError(f"Failed to upload document: {error}")
                    
                return await response.json()
                
    # Database-backed methods
    
    async def save_agent_to_db(self, agent: VoiceAgent) -> Agent:
        """Save an agent to the local database"""
        agent_entity = Agent(
            name=agent.name,
            config=agent.config,
            prompt_template=agent.config.get("prompt"),
            status="draft"
        )
        
        return await self.db.create(agent_entity)
        
    async def get_agent_from_db(self, agent_id: str) -> Optional[Agent]:
        """Get an agent from the local database"""
        return await self.db.get(Agent, agent_id)
        
    async def list_agents_from_db(self, status: Optional[str] = None) -> List[Agent]:
        """List agents from the local database"""
        filters = {"status": status} if status else None
        return await self.db.list(Agent, filters=filters)
        
    async def update_agent_in_db(self, agent: Agent) -> Agent:
        """Update an agent in the local database"""
        return await self.db.update(agent)
        
    async def delete_agent_from_db(self, agent_id: str) -> bool:
        """Delete an agent from the local database"""
        return await self.db.delete(Agent, agent_id)
        
    async def save_knowledge_base_to_db(self, name: str, vector_config: Dict[str, Any]) -> KnowledgeBase:
        """Save a knowledge base to the local database"""
        kb = KnowledgeBase(
            name=name,
            vector_store_config=vector_config
        )
        
        return await self.db.create(kb)
        
    async def save_document_to_db(self, kb_id: str, filename: str, content: str, metadata: Optional[Dict] = None) -> Document:
        """Save a document to the local database"""
        doc = Document(
            knowledge_base_id=kb_id,
            filename=filename,
            content=content,
            metadata=metadata or {}
        )
        
        return await self.db.create(doc)
        
    async def list_documents_from_db(self, kb_id: str) -> List[Document]:
        """List documents in a knowledge base"""
        return await self.db.list(Document, filters={"knowledge_base_id": kb_id})
        
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get database migration status"""
        if not self.migration_manager:
            return {"error": "Migration manager not initialized"}
            
        return await self.migration_manager.status()
        
    async def run_migrations(self, target_version: Optional[str] = None) -> int:
        """Run pending database migrations"""
        if not self.migration_manager:
            raise RuntimeError("Migration manager not initialized")
            
        return await self.migration_manager.migrate(target_version)