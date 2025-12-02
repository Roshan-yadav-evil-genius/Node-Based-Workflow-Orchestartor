from typing import Dict, List, Any
from Nodes.BaseNode import BaseNode
from Nodes.NodeConfig import NodeConfig
from Nodes.ProducerNode import ProducerNode
from NodeFactory import NodeFactory
from WorkflowGraph import WorkflowGraph
from rich import print

class WorkflowLoader:
    """
    Class responsible for loading and parsing workflow JSON, building graph structure.
    Follows Single Responsibility Principle - only handles workflow loading and parsing.
    """
    
    def __init__(self, node_factory: NodeFactory = None):
        """
        Initialize WorkflowLoader.
        
        Args:
            node_factory: NodeFactory instance (creates default if not provided)
        """
        self.node_factory = node_factory or NodeFactory()
    
    def load_workflow(self, workflow_json: Dict[str, Any]) -> WorkflowGraph:
        """
        Load workflow from JSON definition and build graph structure.
        
        Args:
            workflow_json: Dictionary containing workflow definition (React Flow JSON format)
            
        Returns:
            WorkflowGraph object containing nodes, edge_map, and producer_nodes
        """
        print("[WorkflowLoader] Loading workflow...")
        
        # 1. Instantiate Nodes
        nodes: Dict[str, BaseNode] = {}
        for node_def in workflow_json.get("nodes", []):
            node_id = node_def["id"]
            node_type = node_def["type"]
            config_data = node_def["data"].get("config", {})
            config_data["node_id"] = node_id
            config_data["node_name"] = node_id  # Use ID as name for now
            
            config = NodeConfig(**config_data)
            
            # Use factory to create node instance
            node_instance = self.node_factory.create_node(node_type, config)
            if node_instance:
                nodes[node_id] = node_instance
                print(f"[WorkflowLoader] Registered node: {node_id} of type {node_instance.__class__.__name__}({node_type})")
        
        # 2. Build edge map from workflow edges with metadata
        edge_map = self._build_edge_map(workflow_json.get("edges", []))
        
        # 3. Find all ProducerNodes dynamically
        producer_nodes: List[str] = []
        for node_id, node in nodes.items():
            if isinstance(node, ProducerNode):
                producer_nodes.append(node_id)
                print(f"[WorkflowLoader] Found ProducerNode: {node_id} of type {node.__class__.__name__}({node.identifier()})")
        
        return WorkflowGraph(
            nodes=nodes,
            edge_map=edge_map,
            producer_nodes=producer_nodes
        )
    
    def _build_edge_map(self, edges: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
        """
        Build edge map from workflow edges with metadata.
        
        Args:
            edges: List of edge dictionaries from workflow JSON
            
        Returns:
            Dictionary mapping source node IDs to list of edge dictionaries with target and label
        """
        edge_map: Dict[str, List[Dict[str, str]]] = {}  # source -> [{"target": ..., "label": ...}]
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            source_handle = edge.get("sourceHandle")  # Yes/No label or null
            if source and target:
                if source not in edge_map:
                    edge_map[source] = []
                edge_map[source].append({
                    "target": target,
                    "label": source_handle if source_handle else None
                })
        return edge_map
