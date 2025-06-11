"""Base agent class for Knova AI"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Base configuration for all agents"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: str
    metadata: Dict[str, Any] = {}
    

class Agent(ABC):
    """Base class for all agent types"""
    
    def __init__(self, client, config: Dict[str, Any]):
        self.client = client
        self.config = AgentConfig(**config)
        self._id = self.config.id
        
    @property
    def id(self) -> str:
        """Get agent ID"""
        return self._id
        
    @property
    def name(self) -> str:
        """Get agent name"""
        return self.config.name
        
    @abstractmethod
    def to_deployment_config(self) -> Dict[str, Any]:
        """Convert agent to deployment configuration"""
        pass
        
    @abstractmethod
    async def test(self, input_text: str) -> str:
        """Test the agent with sample input"""
        pass
        
    async def save(self):
        """Save agent configuration"""
        # Cache locally
        self.client.config.cache_agent_config(self.id, self.config.model_dump())
        
        # Save to API if online
        if self.client._session:
            async with self.client._session.post(
                f"{self.client.api_url}/v1/agents",
                json=self.config.model_dump(),
                headers={"Authorization": f"Bearer {self.client.license_key}"}
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    raise ValueError(f"Failed to save agent: {error}")
                    
    async def load(self, agent_id: str):
        """Load agent configuration"""
        # Try API first
        if self.client._session:
            async with self.client._session.get(
                f"{self.client.api_url}/v1/agents/{agent_id}",
                headers={"Authorization": f"Bearer {self.client.license_key}"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.config = AgentConfig(**data)
                    self._id = agent_id
                    return
                    
        # Fall back to cache
        cached = self.client.config.get_cached_agent_config(agent_id)
        if cached:
            self.config = AgentConfig(**cached)
            self._id = agent_id
        else:
            raise ValueError(f"Agent {agent_id} not found")