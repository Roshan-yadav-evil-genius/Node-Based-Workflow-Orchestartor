from typing import Dict, List, Optional
from Nodes.Core.BaseNode import BaseNode
from Nodes.Core.BaseNode import ProducerNode, NonBlockingNode
from core.workflow_node import WorkflowNode


class WorkflowGraph:
    """
    Class to hold workflow graph structure with linked WorkflowNode instances.
    Supports incremental building and provides utility methods for traversal and querying.
    """

    def __init__(self):
        self.node_map: Dict[str, WorkflowNode] = {}  # Linked graph structure for traversal
        self.base_nodes: Dict[str, BaseNode] = {}  # Executable node instances (for execution)

    def add_node(self, workflow_node: WorkflowNode, base_node: BaseNode):
        """
        Add a node to the graph.
        
        Args:
            workflow_node: WorkflowNode instance to add
            base_node: BaseNode instance for execution
        """
        if workflow_node.id in self.node_map:
            raise ValueError(f"Node with id '{workflow_node.id}' already exists in the graph")
        
        self.node_map[workflow_node.id] = workflow_node
        self.base_nodes[workflow_node.id] = base_node

    def add_node_at_end_of(self, node_id: str, workflow_node: WorkflowNode, base_node: BaseNode, key: str = "default"):
        """
        Add a node at the end of a specific node.
        
        Args:
            node_id: ID of the node to add after
            workflow_node: WorkflowNode instance to add
            base_node: BaseNode instance for execution
            key: Key to use for the connection (default: "default")
        """
        if node_id not in self.node_map:
            raise ValueError(f"Node with id '{node_id}' not found in the graph")
        
        # Add the new node first
        self.add_node(workflow_node, base_node)
        
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


    def get_producer_nodes(self) -> List[WorkflowNode]:
        """
        Get all producer WorkflowNodes.
        
        Returns:
            List of producer WorkflowNodes
        """
        return [self.node_map[node_id] for node_id in self.producer_node_ids]
    
    @property
    def producer_node_ids(self) -> List[str]:
        """
        Get all producer node IDs.
        
        Returns:
            List of producer node IDs
        """
        return [node_id for node_id, node_instance in self.base_nodes.items() if isinstance(node_instance, ProducerNode)]

    def get_first_node_id(self) -> Optional[str]:
        """
        Get the ID of the first node in the graph.
        A first node is defined as a node with no incoming edges (root node).
        If no such node exists, returns the first producer node ID.
        
        Returns:
            ID of the first node, or None if graph is empty
        """
        if not self.node_map:
            return None
        
        # Find all nodes that are targets of edges (have incoming edges)
        nodes_with_incoming_edges = set()
        for node in self.node_map.values():
            for next_node in node.next.values():
                nodes_with_incoming_edges.add(next_node.id)
        
        # Find nodes with no incoming edges (root nodes)
        root_nodes = [node_id for node_id in self.node_map.keys() if node_id not in nodes_with_incoming_edges]
        
        # Return first root node if exists
        if root_nodes:
            return root_nodes[0]
        
        # If no root nodes, return first producer node
        producer_ids = self.producer_node_ids
        if producer_ids:
            return producer_ids[0]
        
        # If no producer nodes, return first node in node_map
        return list(self.node_map.keys())[0] if self.node_map else None

    def get_all_next(self, node_id: str) -> Dict[str, WorkflowNode]:
        """
        Get all next nodes.
        
        Args:
            node_id: ID of the source node
            
        Returns:
            Dictionary of key -> WorkflowNode mappings, or empty dict if none
        """
        if node_id not in self.node_map:
            return {}
        
        node = self.node_map[node_id]
        return node.next.copy()

    def find_non_blocking_nodes(self) -> List[WorkflowNode]:
        """
        Find all non-blocking nodes.
        
        Returns:
            List of non-blocking WorkflowNodes
        """
        non_blocking_nodes = []
        for node_id, base_node in self.base_nodes.items():
            if isinstance(base_node, NonBlockingNode) and node_id in self.node_map:
                non_blocking_nodes.append(self.node_map[node_id])
        return non_blocking_nodes

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """
        Get WorkflowNode by ID.
        
        Args:
            node_id: ID of the node to retrieve
            
        Returns:
            WorkflowNode or None if not found
        """
        return self.node_map.get(node_id)

    def get_base_node(self, node_id: str) -> Optional[BaseNode]:
        """
        Get BaseNode instance by ID.
        
        Args:
            node_id: ID of the node to retrieve
            
        Returns:
            BaseNode or None if not found
        """
        return self.base_nodes.get(node_id)

