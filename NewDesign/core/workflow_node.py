from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from Nodes.Core.BaseNode import BaseNode


@dataclass
class WorkflowNode:
    """
    Data structure representing a node in the workflow graph.
    Contains only node data and connection management.
    """
    id: str
    instance: BaseNode
    next: Dict[str, List["WorkflowNode"]] = field(default_factory=dict)

    def add_next(self, node: "WorkflowNode", key: str = "default"):
        """
        Add a next node connection.
        If key already exists, appends to the list (for multiple branches).
        
        Args:
            node: WorkflowNode to connect to
            key: Connection key (default: "default")
        """
        if key not in self.next:
            self.next[key] = []
        self.next[key].append(node)
    
    def get_all_next_nodes(self) -> List["WorkflowNode"]:
        """
        Get all next nodes flattened from all branches.
        
        Returns:
            List of all WorkflowNode instances from all branches
        """
        all_nodes = []
        for node_list in self.next.values():
            all_nodes.extend(node_list)
        return all_nodes
    
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
        for key, next_nodes_list in self.next.items():
            # Handle list of nodes - serialize single-item lists as single object for backward compatibility
            if len(next_nodes_list) == 1:
                next_dict[key] = next_nodes_list[0].to_dict(visited.copy())
            else:
                next_dict[key] = [node.to_dict(visited.copy()) for node in next_nodes_list]

        return {
            "id": self.id,
            "next": next_dict
        }
