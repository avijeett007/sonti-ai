"""Knowledge Base entity model."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from ..base import BaseEntity


@dataclass
class KnowledgeBase(BaseEntity):
    """Knowledge Base entity for storing agent knowledge."""
    
    name: str = ""
    agent_id: Optional[str] = None
    vector_store_config: Dict[str, Any] = field(default_factory=dict)
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "knowledge_bases"
    
    def validate(self) -> List[str]:
        """Validate the knowledge base entity."""
        errors = super().validate()
        
        if not self.name:
            errors.append("Knowledge base name is required")
        
        # Validate vector store config if provided
        if self.vector_store_config:
            valid_providers = ["qdrant", "pinecone", "weaviate", "chroma"]
            provider = self.vector_store_config.get("provider")
            
            if provider and provider not in valid_providers:
                errors.append(f"Invalid vector store provider. Must be one of: {', '.join(valid_providers)}")
        
        return errors
    
    def get_vector_provider(self) -> Optional[str]:
        """Get the vector store provider."""
        return self.vector_store_config.get("provider") if self.vector_store_config else None
    
    def get_collection_name(self) -> str:
        """Get the vector collection name."""
        if self.vector_store_config and "collection_name" in self.vector_store_config:
            return self.vector_store_config["collection_name"]
        # Default collection name based on knowledge base ID
        return f"kb_{self.id.replace('-', '_')}"