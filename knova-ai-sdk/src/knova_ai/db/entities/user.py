"""User entity model."""

from dataclasses import dataclass, field
from typing import Optional, List
from ..base import BaseEntity


@dataclass
class User(BaseEntity):
    """User entity representing a platform user."""
    
    email: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "member"
    org_id: Optional[str] = None  # Organization ID for multi-tenant support
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "users"
    
    def validate(self) -> List[str]:
        """Validate the user entity."""
        errors = super().validate()
        
        if not self.email:
            errors.append("Email is required")
        elif "@" not in self.email:
            errors.append("Invalid email format")
        
        valid_roles = ["admin", "member", "viewer"]
        if self.role not in valid_roles:
            errors.append(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        
        return errors
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else self.email.split("@")[0]