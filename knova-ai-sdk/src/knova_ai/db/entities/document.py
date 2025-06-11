"""Document entity model."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from ..base import BaseEntity


@dataclass
class Document(BaseEntity):
    """Document entity for knowledge base content."""
    
    knowledge_base_id: str = ""
    filename: str = ""
    content: Optional[str] = None
    embedding_id: Optional[str] = None  # Reference to vector DB
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def table_name(cls) -> str:
        """Return the database table name."""
        return "documents"
    
    def validate(self) -> List[str]:
        """Validate the document entity."""
        errors = super().validate()
        
        if not self.knowledge_base_id:
            errors.append("Knowledge base ID is required")
        
        if not self.filename:
            errors.append("Filename is required")
        
        return errors
    
    def get_file_extension(self) -> str:
        """Get the file extension."""
        if "." in self.filename:
            return self.filename.split(".")[-1].lower()
        return ""
    
    def get_mime_type(self) -> str:
        """Get the MIME type based on file extension."""
        extension_mapping = {
            "pdf": "application/pdf",
            "txt": "text/plain",
            "md": "text/markdown",
            "html": "text/html",
            "json": "application/json",
            "csv": "text/csv",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "doc": "application/msword"
        }
        
        ext = self.get_file_extension()
        return extension_mapping.get(ext, "application/octet-stream")
    
    def get_size_kb(self) -> float:
        """Get document size in KB."""
        if self.content:
            return len(self.content.encode('utf-8')) / 1024
        return 0.0