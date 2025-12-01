"""
Workflow loader for parsing React Flow JSON and building executable graphs.

This module handles loading workflow definitions from React Flow JSON format
and constructing an executable workflow graph, following the Single Responsibility Principle.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from domain import NodeType
from node_factory import NodeFactory
from nodes import BaseNode


@dataclass
class Edge:
    """Represents a connection between two nodes in the workflow."""
    source: str
    target: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None


@dataclass
class WorkflowGraph:
    """
    Executable workflow graph representation.
    
    Contains nodes and edges parsed from React Flow JSON, with methods
    for querying the graph structure.
    """
    nodes: Dict[str, BaseNode] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    
    def get_downstream_nodes(self, node_id: str) -> List[str]:
        """
        Get immediate downstream nodes for a given node.
        
        Args:
            node_id: Source node identifier
            
        Returns:
            List[str]: List of target node IDs
        """
        return [
            edge.target
            for edge in self.edges
            if edge.source == node_id
        ]
    
    def get_upstream_nodes(self, node_id: str) -> List[str]:
        """
        Get immediate upstream nodes for a given node.
        
        Args:
            node_id: Target node identifier
            
        Returns:
            List[str]: List of source node IDs
        """
        return [
            edge.source
            for edge in self.edges
            if edge.target == node_id
        ]
    
    def get_producer_nodes(self) -> List[str]:
        """
        Get all producer nodes (loop entry points).
        
        A node is considered a producer if:
        1. It has no upstream nodes, OR
        2. It is explicitly marked as type 'producer' or 'queue-reader'
        
        Returns:
            List[str]: List of producer node IDs
        """
        producers = []
        
        for node_id, node in self.nodes.items():
            # Check if node has no upstream nodes
            upstream = self.get_upstream_nodes(node_id)
            if not upstream:
                producers.append(node_id)
            # Check if node type is producer or queue-reader
            elif hasattr(node, 'node_config'):
                node_type = node.node_config.node_type.lower()
                if node_type in ['producer', 'queue-reader', 'queuereader']:
                    producers.append(node_id)
        
        return producers
    
    def get_node_chain(self, producer_id: str) -> List[str]:
        """
        Get ordered chain of nodes from producer to non-blocking node.
        
        Traverses the graph from the producer node following edges until
        a non-blocking node is reached (which marks the end of the iteration).
        
        Args:
            producer_id: Starting producer node ID
            
        Returns:
            List[str]: Ordered list of node IDs in the chain
        """
        if producer_id not in self.nodes:
            return []
        
        chain = [producer_id]
        current_id = producer_id
        
        while True:
            downstream = self.get_downstream_nodes(current_id)
            
            if not downstream:
                # No more nodes in chain
                break
            
            # For simplicity, take the first downstream node
            # In a more complex graph, we might need to handle branching
            next_id = downstream[0]
            
            # Check if next node is non-blocking (iteration end)
            next_node = self.nodes.get(next_id)
            if next_node and hasattr(next_node, 'node_config'):
                node_type = next_node.node_config.node_type.lower()
                if node_type in ['non-blocking', 'nonblocking', 'queue']:
                    chain.append(next_id)
                    break
            
            chain.append(next_id)
            current_id = next_id
        
        return chain
    
    def get_node(self, node_id: str) -> Optional[BaseNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def has_node(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self.nodes


class WorkflowLoader:
    """
    Loads and parses workflow definitions from React Flow JSON format.
    
    Converts React Flow JSON structure into an executable WorkflowGraph
    with instantiated node objects.
    """
    
    def __init__(self, queue_manager=None):
        """
        Initialize WorkflowLoader.
        
        Args:
            queue_manager: Optional QueueManager instance for queue nodes
        """
        self._queue_manager = queue_manager
        self._node_factory = NodeFactory()
    
    def load_from_json(self, json_data: Dict) -> WorkflowGraph:
        """
        Parse React Flow JSON and build WorkflowGraph.
        
        Expected JSON structure:
        {
            "nodes": [
                {
                    "id": "node-1",
                    "type": "producer",
                    "data": {
                        "execution_pool": "async",
                        "config": {...}
                    }
                },
                ...
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "source": "node-1",
                    "target": "node-2",
                    "sourceHandle": "...",
                    "targetHandle": "..."
                },
                ...
            ]
        }
        
        Args:
            json_data: React Flow JSON dictionary
            
        Returns:
            WorkflowGraph: Executable workflow graph
            
        Raises:
            ValueError: If JSON structure is invalid
        """
        if not isinstance(json_data, dict):
            raise ValueError("JSON data must be a dictionary")
        
        nodes_data = json_data.get("nodes", [])
        edges_data = json_data.get("edges", [])
        
        if not isinstance(nodes_data, list):
            raise ValueError("'nodes' must be a list")
        if not isinstance(edges_data, list):
            raise ValueError("'edges' must be a list")
        
        # Build nodes dictionary
        nodes = {}
        for node_data in nodes_data:
            node_id = node_data.get("id")
            if not node_id:
                raise ValueError("Node missing 'id' field")
            
            node_type = node_data.get("type", "blocking")  # Default to blocking
            data = node_data.get("data", {})
            
            # Create node instance
            try:
                node = self._node_factory.create_node(
                    node_type=node_type,
                    node_id=node_id,
                    node_config_dict=data,
                    queue_manager=self._queue_manager
                )
                nodes[node_id] = node
            except Exception as e:
                raise ValueError(f"Failed to create node '{node_id}': {e}") from e
        
        # Build edges list
        edges = []
        for edge_data in edges_data:
            source = edge_data.get("source")
            target = edge_data.get("target")
            
            if not source or not target:
                raise ValueError("Edge missing 'source' or 'target' field")
            
            edge = Edge(
                source=source,
                target=target,
                source_handle=edge_data.get("sourceHandle"),
                target_handle=edge_data.get("targetHandle")
            )
            edges.append(edge)
        
        # Validate graph
        for edge in edges:
            if edge.source not in nodes:
                raise ValueError(f"Edge references unknown source node: {edge.source}")
            if edge.target not in nodes:
                raise ValueError(f"Edge references unknown target node: {edge.target}")
        
        return WorkflowGraph(nodes=nodes, edges=edges)
