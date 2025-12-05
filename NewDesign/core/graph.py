from typing import Dict, List, Optional

import structlog
from Nodes.Core.BaseNode import BaseNode
from core.utils import node_type
from core.workflow_node import WorkflowNode

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

        Args:
            from_id: ID of the source node
            to_id: ID of the target node
            key: Key to use for the connection (default: "default")
        """
        if from_id not in self.node_map:
            raise ValueError(f"Node with id '{from_id}' not found in the graph")
        if to_id not in self.node_map:
            raise ValueError(f"Node with id '{to_id}' not found in the graph")

        self.node_map[from_id].add_next(self.node_map[to_id], key)

        logger.info(f"Connected Nodes", from_id=from_id, to_id=to_id, key=key)

    def get_all_next(self, node_id: str) -> Dict[str, List[WorkflowNode]]:
        """
        Get all next nodes.

        Args:
            node_id: ID of the source node

        Returns:
            Dictionary of key -> List[WorkflowNode] mappings, or empty dict if none
        """
        if node_id not in self.node_map:
            return {}

        node = self.node_map[node_id]
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

        Args:
            node_id: ID of the target node

        Returns:
            List of upstream WorkflowNodes that point to this node
        """
        if node_id not in self.node_map:
            return []
        
        upstream_nodes = []
        for workflow_node in self.node_map.values():
            # Check if any of this node's next nodes is our target node
            for next_nodes_list in workflow_node.next.values():
                for next_node in next_nodes_list:
                    if next_node.id == node_id:
                        upstream_nodes.append(workflow_node)
                        break
                else:
                    continue
                break
        
        return upstream_nodes
