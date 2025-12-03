from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from Nodes.Core.BaseNode import BaseNode
from Nodes.Core.NodeConfig import NodeConfig
from Nodes.Core.ProducerNode import ProducerNode
from Nodes.Core.NonBlockingNode import NonBlockingNode
from core.node_factory import NodeFactory
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class WorkflowNode:
    id: str
    next: Dict[str, "WorkflowNode"] = field(default_factory=dict)

    def add_next(self, node: "WorkflowNode", key: str = "default"):
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


class WorkflowGraph:
    """
    Class to hold workflow graph structure with linked WorkflowNode instances.
    Supports incremental building and provides utility methods for traversal and querying.
    """

    def __init__(self):
        self.node_map: Dict[str, WorkflowNode] = {}  # Linked graph structure for traversal
        self.base_nodes: Dict[str, BaseNode] = {}  # Executable node instances (for execution)
        self.node_factory: NodeFactory = NodeFactory()

    def add_node(self, node_def: Dict[str, Any]):
        """
        Add a node to the graph from a node definition dictionary.
        Handles all processing, initialization, and creation of WorkflowNode and BaseNode.
        
        Args:
            node_def: Dictionary containing node definition with keys: id, type, data
        """
        node_id = node_def["id"]
        node_type = node_def["type"]
        node_data = node_def.get("data", {})
        
        if node_id in self.node_map:
            raise ValueError(f"Node with id '{node_id}' already exists in the graph")
        
        # Extract config data
        config_data = node_data.get("config", {})
        config_data["node_id"] = node_id
        config_data["node_name"] = node_id  # Use ID as name for now
        
        # Create NodeConfig
        config = NodeConfig(**config_data)
        
        # Create BaseNode instance using factory
        node_instance = self.node_factory.create_node(node_type, config)
        

        
        # Add BaseNode if created successfully
        if node_instance:
            self.node_map[node_id] = WorkflowNode(id=node_id)
            self.base_nodes[node_id] = node_instance

            logger.info(f"[WorkflowGraph] Registered node: {node_id} of type {node_instance.__class__.__name__}({node_type})")
        else:
            logger.warning(f"[WorkflowGraph] Node {node_id} of type {node_type} could not be instantiated")

    def add_node_at_end_of(self, node_id: str, node_def: Dict[str, Any], key: str = "default"):
        """
        Add a node at the end of a specific node.
        
        Args:
            node_id: ID of the node to add after
            node_def: Dictionary containing node definition with keys: id, type, data
            key: Key to use for the connection (default: "default")
        """
        if node_id not in self.node_map:
            raise ValueError(f"Node with id '{node_id}' not found in the graph")
        
        # Add the new node first (this will create both WorkflowNode and BaseNode)
        self.add_node(node_def)
        
        # Get the newly created WorkflowNode
        new_node_id = node_def["id"]
        new_node = self.node_map[new_node_id]
        
        # Connect it to the specified node
        self.node_map[node_id].add_next(new_node, key)

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

    def get_edge_map(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get edge_map representation for backward compatibility.
        
        Returns:
            Dictionary mapping source node IDs to list of edge dictionaries with target and label
        """
        edge_map: Dict[str, List[Dict[str, str]]] = {}
        
        for node_id, node in self.node_map.items():
            if node.next:
                edges = []
                for key, next_node in node.next.items():
                    # Convert lowercase keys back to capitalized format for backward compatibility
                    if key == "default":
                        label = None
                    elif key == "yes":
                        label = "Yes"
                    elif key == "no":
                        label = "No"
                    else:
                        label = key  # Keep other keys as-is
                    
                    edges.append({
                        "target": next_node.id,
                        "label": label
                    })
                if edges:
                    edge_map[node_id] = edges
        
        return edge_map
