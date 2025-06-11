"""Phone Number entity model."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from ..base import BaseEntity


@dataclass
class PhoneNumber(BaseEntity):
    """Phone Number entity for managing phone numbers."""
    
    number: str = ""
    sip_trunk_id: Optional[str] = None
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    display_name: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)  # voice, sms, mms
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "phone_numbers"
    
    def validate(self) -> List[str]:
        """Validate the phone number entity."""
        errors = super().validate()
        
        if not self.number:
            errors.append("Phone number is required")
        elif not self.number.startswith("+"):
            errors.append("Phone number must be in E.164 format (starting with +)")
        
        # Validate capabilities
        valid_capabilities = ["voice", "sms", "mms"]
        for capability in self.capabilities:
            if capability not in valid_capabilities:
                errors.append(f"Invalid capability '{capability}'. Must be one of: {', '.join(valid_capabilities)}")
        
        # Validate assignment
        assignments = [self.agent_id, self.workflow_id]
        assigned_count = sum(1 for x in assignments if x is not None)
        if assigned_count > 1:
            errors.append("Phone number can only be assigned to either an agent or workflow, not both")
        
        return errors
    
    def supports_voice(self) -> bool:
        """Check if the phone number supports voice calls."""
        return "voice" in self.capabilities
    
    def supports_sms(self) -> bool:
        """Check if the phone number supports SMS."""
        return "sms" in self.capabilities
    
    def supports_mms(self) -> bool:
        """Check if the phone number supports MMS."""
        return "mms" in self.capabilities
    
    def get_formatted_number(self) -> str:
        """Get a formatted version of the phone number."""
        # Basic formatting for US numbers
        if self.number.startswith("+1") and len(self.number) == 12:
            area = self.number[2:5]
            prefix = self.number[5:8]
            line = self.number[8:12]
            return f"+1 ({area}) {prefix}-{line}"
        return self.number
    
    def is_assigned(self) -> bool:
        """Check if the phone number is assigned to an agent or workflow."""
        return self.agent_id is not None or self.workflow_id is not None