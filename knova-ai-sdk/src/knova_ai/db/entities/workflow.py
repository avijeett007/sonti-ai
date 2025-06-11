"""Workflow entity model."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from ..base import BaseEntity


@dataclass
class Workflow(BaseEntity):
    """Workflow entity representing a multi-agent workflow."""
    
    name: str = ""
    description: Optional[str] = None
    definition: Dict[str, Any] = field(default_factory=dict)  # Nodes and edges
    version: int = 1
    is_active: bool = True
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    
    # Legacy field mapping
    graph_data: Optional[Dict[str, Any]] = None  # Maps to definition
    
    def __post_init__(self):
        """Handle legacy field mapping."""
        if self.graph_data and not self.definition:
            self.definition = self.graph_data
        elif self.definition and not self.graph_data:
            self.graph_data = self.definition
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "workflows"
    
    def validate(self) -> List[str]:
        """Validate the workflow entity."""
        errors = super().validate()
        
        if not self.name:
            errors.append("Workflow name is required")
        
        if not self.definition:
            errors.append("Workflow definition is required")
        
        # Validate definition structure
        if self.definition:
            if "nodes" not in self.definition:
                errors.append("Workflow definition must contain 'nodes'")
            elif not isinstance(self.definition.get("nodes"), list):
                errors.append("Workflow nodes must be a list")
            
            if "edges" not in self.definition:
                errors.append("Workflow definition must contain 'edges'")
            elif not isinstance(self.definition.get("edges"), list):
                errors.append("Workflow edges must be a list")
        
        if self.version < 1:
            errors.append("Version must be at least 1")
        
        return errors
    
    def get_node_count(self) -> int:
        """Get the number of nodes in the workflow."""
        if self.definition and "nodes" in self.definition:
            return len(self.definition["nodes"])
        return 0
    
    def get_edge_count(self) -> int:
        """Get the number of edges in the workflow."""
        if self.definition and "edges" in self.definition:
            return len(self.definition["edges"])
        return 0
    
    def increment_version(self):
        """Increment the workflow version."""
        self.version += 1
        self.update_timestamp()