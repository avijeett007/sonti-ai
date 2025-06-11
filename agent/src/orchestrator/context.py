"""Workflow context management"""

from typing import Dict, Any, Optional


class WorkflowContext:
    """Manages context passing between workflow nodes"""
    
    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._node_outputs: Dict[str, Any] = {}
        
    def set(self, key: str, value: Any):
        """Set a context value"""
        self._context[key] = value
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a context value"""
        return self._context.get(key, default)
        
    def update(self, data: Dict[str, Any]):
        """Update context with multiple values"""
        self._context.update(data)
        
    def set_node_output(self, node_id: str, output: Any):
        """Store output from a node"""
        self._node_outputs[node_id] = output
        
    def get_node_output(self, node_id: str) -> Optional[Any]:
        """Get output from a specific node"""
        return self._node_outputs.get(node_id)
        
    def clear(self):
        """Clear all context"""
        self._context.clear()
        self._node_outputs.clear()
        
    def to_dict(self) -> Dict[str, Any]:
        """Export context as dictionary"""
        return {
            "context": self._context.copy(),
            "node_outputs": self._node_outputs.copy()
        }