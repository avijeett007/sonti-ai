"""Webhook entity model."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from ..base import BaseEntity


@dataclass
class Webhook(BaseEntity):
    """Webhook entity for event notifications."""
    
    url: str = ""
    events: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    secret: Optional[str] = None  # For signature validation
    retry_config: Dict[str, Any] = field(default_factory=lambda: {
        "max_attempts": 3,
        "backoff_seconds": [1, 5, 30]
    })
    is_active: bool = True
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Legacy field mapping
    active: Optional[bool] = None  # Maps to is_active
    
    def __post_init__(self):
        """Handle legacy field mapping."""
        if self.active is not None and self.is_active != self.active:
            self.is_active = self.active
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "webhooks"
    
    def validate(self) -> List[str]:
        """Validate the webhook entity."""
        errors = super().validate()
        
        if not self.url:
            errors.append("Webhook URL is required")
        elif not (self.url.startswith("http://") or self.url.startswith("https://")):
            errors.append("Webhook URL must start with http:// or https://")
        
        if not self.events:
            errors.append("At least one event must be specified")
        
        # Validate events
        valid_events = [
            "agent.started", "agent.stopped", "agent.error",
            "session.started", "session.ended", "session.error",
            "workflow.started", "workflow.completed", "workflow.error",
            "telemetry", "call.started", "call.ended", "call.error"
        ]
        
        for event in self.events:
            if event not in valid_events:
                errors.append(f"Invalid event '{event}'. Must be one of: {', '.join(valid_events)}")
        
        # Validate assignment
        if self.agent_id and self.workflow_id:
            errors.append("Webhook can only be assigned to either an agent or workflow, not both")
        
        # Validate retry config
        if self.retry_config:
            if "max_attempts" in self.retry_config:
                max_attempts = self.retry_config["max_attempts"]
                if not isinstance(max_attempts, int) or max_attempts < 0:
                    errors.append("retry_config.max_attempts must be a non-negative integer")
            
            if "backoff_seconds" in self.retry_config:
                backoff = self.retry_config["backoff_seconds"]
                if not isinstance(backoff, list) or not all(isinstance(x, (int, float)) for x in backoff):
                    errors.append("retry_config.backoff_seconds must be a list of numbers")
        
        return errors
    
    def subscribes_to(self, event: str) -> bool:
        """Check if the webhook subscribes to a specific event."""
        return event in self.events
    
    def get_max_attempts(self) -> int:
        """Get the maximum retry attempts."""
        return self.retry_config.get("max_attempts", 3)
    
    def get_backoff_seconds(self) -> List[int]:
        """Get the backoff seconds for retries."""
        return self.retry_config.get("backoff_seconds", [1, 5, 30])