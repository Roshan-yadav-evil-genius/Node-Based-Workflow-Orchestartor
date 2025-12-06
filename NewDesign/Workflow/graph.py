from typing import Dict, List, Optional

import structlog
from Node.Core.Node.Core.BaseNode import BaseNode
from .utils import node_type
from .workflow_node import WorkflowNode

logger = structlog.get_logger(__name__)

class WorkflowGraph:
    """
    Class to hold workflow graph structure with linked WorkflowNode instances.
    Follows Single Responsibility Principle - only handles graph structure management.
    """

    def __init__(self):
        self.node_map: Dict[str, WorkflowNode] = (
            {}
        )  # Linked graph structure for traversal

    def add_node(self, workflow_node: WorkflowNode):
        """
        Add a node to the graph.

        Args:
            workflow_node: WorkflowNode instance to add
        """
        if workflow_node.id in self.node_map:
            raise ValueError(
                f"Node with id '{workflow_node.id}' already exists in the graph"
            )

        self.node_map[workflow_node.id] = workflow_node
        logger.info(f"WorkflowNode Added To Graph", node_id=workflow_node.id, base_node_type=node_type(workflow_node.instance), identifier=f"{workflow_node.instance.__class__.__name__}({workflow_node.instance.identifier()})")

    def add_node_at_end_of(
        self, node_id: str, workflow_node: WorkflowNode, key: str = "default"
    ):
        """
        Add a node at the end of a specific node.

        Args:
            node_id: ID of the node to add after
            workflow_node: WorkflowNode instance to add
            key: Key to use for the connection (default: "default")
        """
        if node_id not in self.node_map:
            raise ValueError(f"Node with id '{node_id}' not found in the graph")

        # Add the new node first
        self.add_node(workflow_node)

        # Connect it to the specified node
        self.node_map[node_id].add_next(workflow_node, key)

    def connect_nodes(self, from_id: str, to_id: str, key: str = "default"):
        """
        Connect two existing nodes.

        MULTIPLE BRANCH SUPPORT:
        This method calls WorkflowNode.add_next(), which APPENDS to a list instead of
        overwriting. This enables multiple edges with the same key to be stored.
        
        EXAMPLE: If called twice with same from_id and key:
        - First call: connect_nodes("1", "10", "default") → {"default": [node_10]}
        - Second call: connect_nodes("1", "14", "default") → {"default": [node_10, node_14]}
        
        This is the mechanism that allows workflow1.json to store both branches.

        Args:
            from_id: ID of the source node
            to_id: ID of the target node
            key: Key to use for the connection (default: "default")
                 For logical nodes: "yes" or "no"
                 For non-logical nodes: typically "default"
        """
        if from_id not in self.node_map:
            raise ValueError(f"Node with id '{from_id}' not found in the graph")
        if to_id not in self.node_map:
            raise ValueError(f"Node with id '{to_id}' not found in the graph")

        # add_next() appends to list - this is the key mechanism for multiple branches
        # If key exists, node is appended; if not, new list is created
        self.node_map[from_id].add_next(self.node_map[to_id], key)

        logger.info(f"Connected Nodes", from_id=from_id, to_id=to_id, key=key)

    def get_all_next(self, node_id: str) -> Dict[str, List[WorkflowNode]]:
        """
        Get all next nodes.

        RETURN TYPE CHANGE:
        Changed from Dict[str, WorkflowNode] to Dict[str, List[WorkflowNode]]
        to support multiple branches per key.

        Args:
            node_id: ID of the source node

        Returns:
            Dictionary mapping branch keys to lists of WorkflowNodes
            Example: {"default": [node_10, node_14], "yes": [node_20]}
            Empty dict if node not found or has no next nodes
        """
        if node_id not in self.node_map:
            return {}

        node = self.node_map[node_id]
        # Return copy to prevent external modification
        return node.next.copy()

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """
        Get WorkflowNode by ID.

        Args:
            node_id: ID of the node to retrieve

        Returns:
            WorkflowNode or None if not found
        """
        return self.node_map.get(node_id)

    def get_node_instance(self, node_id: str) -> Optional[BaseNode]:
        """
        Get BaseNode instance by ID.

        Args:
            node_id: ID of the node to retrieve

        Returns:
            BaseNode or None if not found
        """
        workflow_node = self.node_map.get(node_id)
        return workflow_node.instance if workflow_node else None

    def get_upstream_nodes(self, node_id: str) -> List[WorkflowNode]:
        """
        Get all upstream (parent) nodes that have this node as their next node.

        MULTIPLE BRANCH SUPPORT:
        Must iterate through lists because a node can appear in multiple branch lists.
        The nested loop structure is necessary to check all nodes in all branches.

        Args:
            node_id: ID of the target node

        Returns:
            List of upstream WorkflowNodes that point to this node
        """
        if node_id not in self.node_map:
            return []
        
        upstream_nodes = []
        
        # OUTER LOOP: Iterate through all workflow nodes in the graph
        for workflow_node in self.node_map.values():
            # MIDDLE LOOP: Iterate through all branch keys (e.g., "default", "yes", "no")
            # Each key maps to a list of WorkflowNodes
            for next_nodes_list in workflow_node.next.values():
                # INNER LOOP: Iterate through all nodes in this branch list
                # REASON: Must check all nodes in all branches to find if any point to target
                for next_node in next_nodes_list:
                    if next_node.id == node_id:
                        # Found upstream connection - add parent node
                        upstream_nodes.append(workflow_node)
                        # Break out of inner and middle loops, continue outer loop
                        break
                else:
                    # Continue to next branch list if target not found in this list
                    continue
                # Break out of middle loop if target was found
                break
        
        return upstream_nodes
