"""SIP Trunk entity model."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from ..base import BaseEntity


@dataclass
class SipTrunk(BaseEntity):
    """SIP Trunk entity for telephony configuration."""
    
    provider: str = ""  # twilio, telnyx, plivo
    config: Dict[str, Any] = field(default_factory=dict)  # Encrypted credentials
    phone_numbers: List[str] = field(default_factory=list)
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None
    is_active: bool = True
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "sip_configs"
    
    def validate(self) -> List[str]:
        """Validate the SIP trunk entity."""
        errors = super().validate()
        
        valid_providers = ["twilio", "telnyx", "plivo"]
        if not self.provider:
            errors.append("Provider is required")
        elif self.provider not in valid_providers:
            errors.append(f"Invalid provider. Must be one of: {', '.join(valid_providers)}")
        
        if not self.config:
            errors.append("Configuration is required")
        
        # Provider-specific validation
        if self.provider == "twilio" and self.config:
            required_keys = ["account_sid", "auth_token"]
            for key in required_keys:
                if key not in self.config:
                    errors.append(f"Twilio config missing required key: {key}")
        
        elif self.provider == "telnyx" and self.config:
            required_keys = ["api_key"]
            for key in required_keys:
                if key not in self.config:
                    errors.append(f"Telnyx config missing required key: {key}")
        
        elif self.provider == "plivo" and self.config:
            required_keys = ["auth_id", "auth_token"]
            for key in required_keys:
                if key not in self.config:
                    errors.append(f"Plivo config missing required key: {key}")
        
        return errors
    
    def add_phone_number(self, phone_number: str):
        """Add a phone number to the SIP trunk."""
        if phone_number and phone_number not in self.phone_numbers:
            self.phone_numbers.append(phone_number)
            self.update_timestamp()
    
    def remove_phone_number(self, phone_number: str):
        """Remove a phone number from the SIP trunk."""
        if phone_number in self.phone_numbers:
            self.phone_numbers.remove(phone_number)
            self.update_timestamp()
    
    def get_display_name(self) -> str:
        """Get a display name for the SIP trunk."""
        if self.name:
            return self.name
        return f"{self.provider.title()} SIP Trunk"