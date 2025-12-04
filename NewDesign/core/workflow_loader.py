from typing import Any, Dict, List, Optional
import structlog
from Nodes.Core import (
    BaseNode,
    BlockingNode,
    NonBlockingNode,
    ProducerNode,
    LogicalNode,
)
from Nodes.Core.Data import NodeConfig
from core.graph import WorkflowGraph
from core.node_factory import NodeFactory
from core.utils import BranchKeyNormalizer
from core.workflow_node import WorkflowNode
from core.graph_traverser import GraphTraverser

logger = structlog.get_logger(__name__)


class WorkflowLoader:
    """
    Handles loading workflow from JSON definitions.
    Follows Single Responsibility Principle - only handles workflow loading and parsing.
    """

    def __init__(self, graph: WorkflowGraph, node_factory: NodeFactory):
        """
        Initialize WorkflowLoader with dependencies.

        Args:
            graph: WorkflowGraph instance to populate
            node_factory: NodeFactory instance for creating nodes
        """
        self.graph = graph
        self.node_factory = node_factory

    def load_workflow(self, workflow_json: Dict[str, Any]) -> None:
        """
        Load workflow from JSON definition and build graph structure.

        Args:
            workflow_json: Dictionary containing workflow definition (React Flow JSON format)
        """
        logger.info("Loading workflow...")

        self._add_nodes(workflow_json.get("nodes", []))
        self._connect_nodes(workflow_json.get("edges", []))


    def _add_nodes(self, nodes: List[Dict[str, Any]]):
        """
        Add all nodes from the workflow JSON to the graph.

        Args:
            nodes: List of node definition dictionaries
        """
        for node_def in nodes:
            try:
                # Build node directly (merged from NodeBuilder)
                workflow_node_instance = self._get_workflow_node_instance(node_def)
                if workflow_node_instance:
                    self.graph.add_node(workflow_node_instance)
                else:
                    logger.warning(
                        f"Node {node_def.get('id')} of type {node_def.get('type')} could not be instantiated"
                    )
            except ValueError as e:
                logger.warning(f"Could not add node: {e}")

    def _get_workflow_node_instance(
        self, node_def: Dict[str, Any]
    ) -> Optional[WorkflowNode]:
        """
        Build WorkflowNode and BaseNode from node definition.

        Args:
            node_def: Dictionary containing node definition with keys: id, type, data

        Returns:
            WorkflowNode if successful, None otherwise
        """

        # Create NodeConfig
        node_config = NodeConfig(**node_def)

        # Create BaseNode instance using factory
        base_node_instance = self.node_factory.create_node(node_config)

        if not base_node_instance:
            return None


        # Create WorkflowNode instance
        workflow_node_instance = WorkflowNode(
            id=node_config.id, instance=base_node_instance
        )

        return workflow_node_instance


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
                key = BranchKeyNormalizer.normalize_to_lowercase(source_handle)

                try:
                    self.graph.connect_nodes(source, target, key)
                except ValueError as e:
                    logger.warning(
                        f"Could not connect {source} -> {target}: {e}"
                    )

    def _log_workflow_graph(self):
        """
        Log the workflow graph.
        """
        traverser = GraphTraverser(self.graph)
        first_node_id = traverser.get_first_node_id()
        if first_node_id:
            first_node = self.graph.node_map[first_node_id]
            logger.info(
                f"Workflow Loaded Successfully",
                graph=first_node.to_dict(),
            )
        else:
            logger.error("No first node found in the workflow")
