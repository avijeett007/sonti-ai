"""Multi-agent workflow implementation for Knova AI"""

from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4

from .base import Agent
from .voice import VoiceAgent


class WorkflowNode:
    """Node in a workflow graph"""
    
    def __init__(self, node_id: str, node_type: str, data: Dict[str, Any]):
        self.id = node_id
        self.type = node_type
        self.data = data
        
        
class WorkflowEdge:
    """Edge connecting workflow nodes"""
    
    def __init__(self, source: str, target: str, condition: Optional[str] = None):
        self.source = source
        self.target = target
        self.condition = condition
        

class WorkflowAgent(Agent):
    """Multi-agent workflow orchestrator"""
    
    def __init__(self, client, config: Dict[str, Any]):
        config["type"] = "workflow"
        super().__init__(client, config)
        
        self.description = config.get("description", "")
        self.nodes: List[WorkflowNode] = []
        self.edges: List[WorkflowEdge] = []
        self.start_node: Optional[str] = None
        
    def add_agent_node(
        self,
        agent: VoiceAgent,
        position: Optional[Tuple[float, float]] = None
    ) -> str:
        """Add an agent node to the workflow"""
        node_id = f"agent_{str(uuid4())[:8]}"
        
        node = WorkflowNode(
            node_id=node_id,
            node_type="agent",
            data={
                "agent_id": agent.id,
                "agent_name": agent.name,
                "position": position or (0, 0)
            }
        )
        
        self.nodes.append(node)
        
        # First node becomes start node
        if not self.start_node:
            self.start_node = node_id
            
        return node_id
        
    def add_condition_node(
        self,
        name: str,
        condition_type: str = "keyword",
        condition_value: Any = None,
        position: Optional[Tuple[float, float]] = None
    ) -> str:
        """Add a condition node to the workflow"""
        node_id = f"condition_{str(uuid4())[:8]}"
        
        node = WorkflowNode(
            node_id=node_id,
            node_type="condition",
            data={
                "name": name,
                "condition_type": condition_type,
                "condition_value": condition_value,
                "position": position or (0, 0)
            }
        )
        
        self.nodes.append(node)
        return node_id
        
    def add_tool_node(
        self,
        tool_name: str,
        tool_config: Dict[str, Any],
        position: Optional[Tuple[float, float]] = None
    ) -> str:
        """Add a tool/function node to the workflow"""
        node_id = f"tool_{str(uuid4())[:8]}"
        
        node = WorkflowNode(
            node_id=node_id,
            node_type="tool",
            data={
                "tool_name": tool_name,
                "tool_config": tool_config,
                "position": position or (0, 0)
            }
        )
        
        self.nodes.append(node)
        return node_id
        
    def connect_nodes(
        self,
        source_id: str,
        target_id: str,
        condition: Optional[str] = None
    ):
        """Connect two nodes with an edge"""
        edge = WorkflowEdge(
            source=source_id,
            target=target_id,
            condition=condition
        )
        
        self.edges.append(edge)
        
    def set_start_node(self, node_id: str):
        """Set the starting node for the workflow"""
        # Verify node exists
        if not any(node.id == node_id for node in self.nodes):
            raise ValueError(f"Node {node_id} not found in workflow")
            
        self.start_node = node_id
        
    def to_deployment_config(self) -> Dict[str, Any]:
        """Convert to deployment configuration"""
        return {
            "id": self.id,
            "name": self.name,
            "type": "workflow",
            "description": self.description,
            "graph": {
                "nodes": [
                    {
                        "id": node.id,
                        "type": node.type,
                        "data": node.data
                    }
                    for node in self.nodes
                ],
                "edges": [
                    {
                        "source": edge.source,
                        "target": edge.target,
                        "condition": edge.condition
                    }
                    for edge in self.edges
                ],
                "start_node": self.start_node
            }
        }
        
    async def test(self, input_text: str) -> str:
        """Test the workflow with sample input"""
        # For testing, just validate the workflow structure
        if not self.start_node:
            return "Error: No start node defined"
            
        if not self.nodes:
            return "Error: No nodes in workflow"
            
        # Simple validation
        node_ids = {node.id for node in self.nodes}
        
        for edge in self.edges:
            if edge.source not in node_ids:
                return f"Error: Edge source {edge.source} not found"
            if edge.target not in node_ids:
                return f"Error: Edge target {edge.target} not found"
                
        return f"Workflow '{self.name}' is valid with {len(self.nodes)} nodes and {len(self.edges)} edges"
        
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate workflow structure"""
        if not self.start_node:
            return False, "No start node defined"
            
        if not self.nodes:
            return False, "No nodes in workflow"
            
        # Check all edges reference valid nodes
        node_ids = {node.id for node in self.nodes}
        
        for edge in self.edges:
            if edge.source not in node_ids:
                return False, f"Edge source {edge.source} not found"
            if edge.target not in node_ids:
                return False, f"Edge target {edge.target} not found"
                
        # Check for cycles (simple DFS)
        visited = set()
        stack = set()
        
        def has_cycle(node_id: str) -> bool:
            if node_id in stack:
                return True
            if node_id in visited:
                return False
                
            visited.add(node_id)
            stack.add(node_id)
            
            # Get outgoing edges
            for edge in self.edges:
                if edge.source == node_id:
                    if has_cycle(edge.target):
                        return True
                        
            stack.remove(node_id)
            return False
            
        if has_cycle(self.start_node):
            return False, "Workflow contains a cycle"
            
        return True, None
        
    def to_react_flow_data(self) -> Dict[str, Any]:
        """Convert to React Flow format for visualization"""
        return {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type,
                    "data": node.data,
                    "position": node.data.get("position", {"x": 0, "y": 0})
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "id": f"{edge.source}-{edge.target}",
                    "source": edge.source,
                    "target": edge.target,
                    "label": edge.condition,
                    "type": "smoothstep"
                }
                for edge in self.edges
            ]
        }