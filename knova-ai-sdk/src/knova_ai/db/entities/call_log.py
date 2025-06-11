"""Call Log entity model."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..base import BaseEntity


@dataclass
class CallLog(BaseEntity):
    """Call Log entity for tracking phone calls."""
    
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    phone_number: Optional[str] = None
    direction: str = "inbound"  # inbound or outbound
    status: str = "initiated"
    duration_seconds: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "call_logs"
    
    def validate(self) -> List[str]:
        """Validate the call log entity."""
        errors = super().validate()
        
        valid_directions = ["inbound", "outbound"]
        if self.direction not in valid_directions:
            errors.append(f"Invalid direction. Must be one of: {', '.join(valid_directions)}")
        
        valid_statuses = ["initiated", "ringing", "answered", "completed", "failed", "busy", "no_answer"]
        if self.status not in valid_statuses:
            errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        if self.duration_seconds is not None and self.duration_seconds < 0:
            errors.append("Duration cannot be negative")
        
        if self.started_at and self.ended_at:
            if self.started_at > self.ended_at:
                errors.append("Start time cannot be after end time")
        
        return errors
    
    def is_completed(self) -> bool:
        """Check if the call is completed."""
        return self.status == "completed"
    
    def is_failed(self) -> bool:
        """Check if the call failed."""
        return self.status in ["failed", "busy", "no_answer"]
    
    def calculate_duration(self) -> Optional[int]:
        """Calculate call duration from timestamps."""
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds())
        return self.duration_seconds
    
    def get_formatted_duration(self) -> str:
        """Get formatted duration string."""
        seconds = self.duration_seconds or self.calculate_duration()
        if seconds is None:
            return "N/A"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"