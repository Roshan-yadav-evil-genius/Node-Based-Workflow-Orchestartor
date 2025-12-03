import structlog
from typing import Dict, List, Any
from core.graph import WorkflowGraph
from rich import print

logger = structlog.get_logger(__name__)

class WorkflowLoader:
    """
    Class responsible for loading and parsing workflow JSON, building graph structure.
    Follows Single Responsibility Principle - only handles workflow loading and parsing.
    """
    
    def __init__(self):
        """Initialize WorkflowLoader with a new WorkflowGraph instance."""
        self.workflow_graph = WorkflowGraph()
    
    def load_workflow(self, workflow_json: Dict[str, Any]) -> WorkflowGraph:
        """
        Load workflow from JSON definition and build graph structure.
        
        Args:
            workflow_json: Dictionary containing workflow definition (React Flow JSON format)
            
        Returns:
            WorkflowGraph object containing linked WorkflowNode instances and BaseNode instances
        """
        logger.info("[WorkflowLoader] Loading workflow...")

        # Reset graph for new workflow
        self.workflow_graph = WorkflowGraph()
        
        self._add_nodes(workflow_json.get("nodes", []))
        self._connect_nodes(workflow_json.get("edges", []))
        self._log_producer_nodes()
        
        # get WorkflowNode instance and print dict so we are going to get inherited dict
        first_node_id = self.workflow_graph.get_first_node_id()
        if first_node_id:
            first_node = self.workflow_graph.node_map[first_node_id]
            logger.info(f"[WorkflowLoader] Workflow Loaded Successfully",graph=first_node.to_dict())
        else:
            logger.error("[WorkflowLoader] No first node found in the workflow")

        return self.workflow_graph
    
    def _add_nodes(self, nodes: List[Dict[str, Any]]):
        """
        Add all nodes from the workflow JSON to the graph.
        
        Args:
            nodes: List of node definition dictionaries
        """
        for node_def in nodes:
            try:
                self.workflow_graph.add_node(node_def)
            except ValueError as e:
                logger.warning(f"[WorkflowLoader] Could not add node: {e}")
    
    def _connect_nodes(self, edges: List[Dict[str, Any]]):
        """
        Connect nodes in the graph using edge definitions.
        
        Args:
            edges: List of edge definition dictionaries
        """
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            source_handle = edge.get("sourceHandle")
            
            if source and target:
                key = self._normalize_edge_key(source_handle)
                
                try:
                    self.workflow_graph.connect_nodes(source, target, key)
                except ValueError as e:
                    logger.warning(f"[WorkflowLoader] Could not connect {source} -> {target}: {e}")
    
    def _normalize_edge_key(self, source_handle: Any) -> str:
        """
        Normalize edge key from sourceHandle to lowercase format.
        
        Args:
            source_handle: Source handle value (Yes/No label or null)
            
        Returns:
            Normalized key string ("yes", "no", or "default")
        """
        if source_handle:
            return source_handle.lower()
        return "default"
    
    def _log_producer_nodes(self):
        """
        Log all producer nodes found in the workflow graph.
        """
        producer_nodes = self.workflow_graph.get_producer_nodes()
        for producer_node in producer_nodes:
            base_node = self.workflow_graph.get_base_node(producer_node.id)
            if base_node:
                logger.info(f"[WorkflowLoader] Found ProducerNode: {producer_node.id} of type {base_node.__class__.__name__}({base_node.identifier()})")
