"""
WorkflowNode - Core Data Structure for Workflow Graph

ARCHITECTURAL CHANGE: Multiple Branch Support
=============================================
Previously, WorkflowNode.next was Dict[str, WorkflowNode], meaning only one node
could be stored per key. This prevented multiple outgoing edges with the same key
(e.g., multiple "default" branches) from being stored.

CHANGE: next is now Dict[str, List[WorkflowNode]]
- Allows multiple nodes per key (e.g., multiple "default" branches)
- When multiple edges share the same key, they are stored as a list
- Example: workflow1.json has two edges from node "1" with sourceHandle=null
  Both normalize to "default" key and are stored as a list: ["node_10", "node_14"]

EXECUTION BEHAVIOR:
- Logical nodes: Select first node from list for chosen branch key ("yes"/"no")
- Non-logical nodes: Execute ALL nodes in list sequentially
- Backward compatible: Single-node lists behave like old single-node structure
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from Nodes.Core.BaseNode import BaseNode


@dataclass
class WorkflowNode:
    """
    Data structure representing a node in the workflow graph.
    Contains only node data and connection management.
    
    ARCHITECTURE:
    - id: Unique identifier for the node
    - instance: The actual BaseNode implementation (ProducerNode, BlockingNode, etc.)
    - next: Dictionary mapping branch keys to lists of next WorkflowNodes
            Key examples: "default", "yes", "no" (for logical branches)
            Value: List of WorkflowNodes (supports multiple branches per key)
    
    MULTIPLE BRANCH SUPPORT:
    The 'next' field uses Dict[str, List[WorkflowNode]] instead of Dict[str, WorkflowNode]
    to support multiple outgoing edges with the same key. This is essential for workflows
    like workflow1.json where node "1" has two edges both with sourceHandle=null, which
    both normalize to the "default" key.
    """
    id: str
    instance: BaseNode
    
    # ARCHITECTURAL CHANGE: Changed from Dict[str, WorkflowNode] to Dict[str, List[WorkflowNode]]
    # REASON: Support multiple outgoing edges with same key (e.g., multiple "default" branches)
    # EXAMPLE: workflow1.json - node "1" has two edges both with sourceHandle=null
    #          Both normalize to "default" key and are stored as: {"default": [node_10, node_14]}
    next: Dict[str, List["WorkflowNode"]] = field(default_factory=dict)

    def add_next(self, node: "WorkflowNode", key: str = "default"):
        """
        Add a next node connection.
        
        BEHAVIOR: Appends to list instead of overwriting
        - If key doesn't exist: Creates new list with the node
        - If key exists: Appends node to existing list
        - This allows multiple edges from same source with same key
        
        EXAMPLE: workflow1.json
        - First edge from node "1" to node "10": creates {"default": [node_10]}
        - Second edge from node "1" to node "14": appends, becomes {"default": [node_10, node_14]}
        
        Args:
            node: WorkflowNode to connect to
            key: Connection key (default: "default")
                  For logical nodes: "yes" or "no"
                  For non-logical nodes: typically "default"
        """
        # If key doesn't exist, create new list
        if key not in self.next:
            self.next[key] = []
        # Append to list (allows multiple nodes per key)
        # This is the key change: we append instead of overwriting
        self.next[key].append(node)
    
    def get_all_next_nodes(self) -> List["WorkflowNode"]:
        """
        Get all next nodes flattened from all branches.
        
        PURPOSE: Helper method to get all downstream nodes regardless of branch key.
        Useful for traversal operations that need to process all branches.
        
        EXAMPLE: If next = {"default": [node_10, node_14], "yes": [node_20]}
                 Returns: [node_10, node_14, node_20]
        
        Returns:
            List of all WorkflowNode instances from all branches, flattened
        """
        all_nodes = []
        # Iterate through all branch keys (e.g., "default", "yes", "no")
        for node_list in self.next.values():
            # Extend with all nodes in this branch list
            all_nodes.extend(node_list)
        return all_nodes
    
    def to_dict(self, visited: Optional[set] = None) -> Dict[str, Any]:
        """
        Convert WorkflowNode to dictionary for serialization.
        Handles recursive references by tracking visited nodes.

        SERIALIZATION STRATEGY:
        - Single-item lists: Serialize as single object (backward compatibility)
        - Multi-item lists: Serialize as array of objects
        - This maintains compatibility with code expecting single nodes while
          supporting the new multiple branch structure
        
        EXAMPLE OUTPUT:
        - Single branch: {"id": "1", "next": {"default": {"id": "10", "next": {}}}}
        - Multiple branches: {"id": "1", "next": {"default": [{"id": "10", ...}, {"id": "14", ...}]}}

        Args:
            visited: Set of visited node IDs to prevent infinite recursion

        Returns:
            Dictionary representation of the WorkflowNode
        """
        if visited is None:
            visited = set()

        # Prevent infinite recursion in circular graphs
        # If we've seen this node before, return a marker instead of recursing
        if self.id in visited:
            return {"id": self.id, "next": {}, "_circular_reference": True}

        visited.add(self.id)

        # Serialize next nodes recursively
        next_dict = {}
        for key, next_nodes_list in self.next.items():
            # BACKWARD COMPATIBILITY: Single-item lists serialize as single object
            # This ensures existing code that expects single nodes continues to work
            if len(next_nodes_list) == 1:
                # Single node: serialize as object (not array)
                next_dict[key] = next_nodes_list[0].to_dict(visited.copy())
            else:
                # Multiple nodes: serialize as array
                # This clearly indicates multiple branches exist
                next_dict[key] = [node.to_dict(visited.copy()) for node in next_nodes_list]

        return {
            "id": self.id,
            "next": next_dict
        }
