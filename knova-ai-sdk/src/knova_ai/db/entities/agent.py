"""Agent and API Key entity models."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from ..base import BaseEntity


@dataclass
class Agent(BaseEntity):
    """Agent entity representing an AI agent configuration."""
    
    name: str = ""
    config: Dict[str, Any] = field(default_factory=dict)  # LLM, STT, TTS settings
    prompt_template: Optional[str] = None
    status: str = "active"
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    webhook_id: Optional[str] = None
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "agents"
    
    def validate(self) -> List[str]:
        """Validate the agent entity."""
        errors = super().validate()
        
        if not self.name:
            errors.append("Agent name is required")
        
        if not self.config:
            errors.append("Agent configuration is required")
        
        valid_statuses = ["active", "inactive", "paused", "draft"]
        if self.status not in valid_statuses:
            errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Validate config structure
        if self.config:
            required_keys = ["llm"]
            for key in required_keys:
                if key not in self.config:
                    errors.append(f"Missing required configuration key: {key}")
        
        return errors
    
    def is_active(self) -> bool:
        """Check if the agent is active."""
        return self.status == "active"


@dataclass
class ApiKey(BaseEntity):
    """API Key entity for authentication."""
    
    key: str = ""
    name: str = ""
    user_id: str = ""
    permissions: List[str] = field(default_factory=list)
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    is_active: bool = True
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "api_keys"
    
    def validate(self) -> List[str]:
        """Validate the API key entity."""
        errors = super().validate()
        
        if not self.key:
            errors.append("API key is required")
        
        if not self.name:
            errors.append("API key name is required")
        
        if not self.user_id:
            errors.append("User ID is required")
        
        return errors
    
    def has_permission(self, permission: str) -> bool:
        """Check if the API key has a specific permission."""
        return permission in self.permissions or "*" in self.permissions