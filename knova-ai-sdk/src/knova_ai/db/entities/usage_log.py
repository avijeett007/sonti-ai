"""Usage Log entity model."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..base import BaseEntity


@dataclass
class UsageLog(BaseEntity):
    """Usage Log entity for tracking resource usage."""
    
    license_key: Optional[str] = None
    usage_type: str = ""  # agents, calls, storage, tokens, etc.
    usage_count: int = 1
    resource_id: Optional[str] = None  # ID of the resource being tracked
    metadata: Dict[str, Any] = field(default_factory=dict)
    recorded_at: Optional[datetime] = None
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "license_usage"
    
    def validate(self) -> List[str]:
        """Validate the usage log entity."""
        errors = super().validate()
        
        if not self.usage_type:
            errors.append("Usage type is required")
        
        valid_usage_types = [
            "agents", "calls", "storage", "tokens", 
            "knowledge_base_queries", "function_calls",
            "webhook_deliveries", "sms", "transcription_minutes"
        ]
        
        if self.usage_type not in valid_usage_types:
            errors.append(f"Invalid usage type. Must be one of: {', '.join(valid_usage_types)}")
        
        if self.usage_count < 0:
            errors.append("Usage count cannot be negative")
        
        return errors
    
    def get_usage_description(self) -> str:
        """Get a human-readable description of the usage."""
        descriptions = {
            "agents": "Agent created",
            "calls": "Phone call",
            "storage": "Storage used (MB)",
            "tokens": "LLM tokens used",
            "knowledge_base_queries": "Knowledge base query",
            "function_calls": "Function call executed",
            "webhook_deliveries": "Webhook delivered",
            "sms": "SMS sent",
            "transcription_minutes": "Minutes transcribed"
        }
        
        base_desc = descriptions.get(self.usage_type, self.usage_type)
        
        if self.usage_count > 1:
            return f"{base_desc} x{self.usage_count}"
        return base_desc
    
    def calculate_cost(self, pricing: Dict[str, float]) -> float:
        """Calculate the cost based on pricing configuration."""
        unit_price = pricing.get(self.usage_type, 0.0)
        return unit_price * self.usage_count