from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class WorkflowNode:
    """
    Data structure representing a node in the workflow graph.
    Contains only node data and connection management.
    """
    id: str
    next: Dict[str, "WorkflowNode"] = field(default_factory=dict)

    def add_next(self, node: "WorkflowNode", key: str = "default"):
        """
        Add a next node connection.
        
        Args:
            node: WorkflowNode to connect to
            key: Connection key (default: "default")
        """
        self.next[key] = node
    
    def to_dict(self, visited: Optional[set] = None) -> Dict[str, Any]:
        """
        Convert WorkflowNode to dictionary for serialization.
        Handles recursive references by tracking visited nodes.
        
        Args:
            visited: Set of visited node IDs to prevent infinite recursion
            
        Returns:
            Dictionary representation of the WorkflowNode
        """
        if visited is None:
            visited = set()
        
        # Prevent infinite recursion in circular graphs
        if self.id in visited:
            return {"id": self.id, "next": {}, "_circular_reference": True}
        
        visited.add(self.id)
        
        # Serialize next nodes recursively
        next_dict = {}
        for key, next_node in self.next.items():
            next_dict[key] = next_node.to_dict(visited.copy())
        
        return {
            "id": self.id,
            "next": next_dict
        }
