import asyncio
import structlog
from typing import Dict, List, Any
from Nodes.Core.BaseNode import BaseNode
from Nodes.Core.Data import NodeOutput
from core.graph import WorkflowGraph
from core.graph_traverser import GraphTraverser
from core.workflow_loader import WorkflowLoader
from core.workflow_node import WorkflowNode
from core.node_factory import NodeFactory
from execution.loop_manager import LoopManager
from storage.data_store import DataStore

logger = structlog.get_logger(__name__)


class WorkflowOrchestrator:
    """
    Central coordination system for workflow execution.
    Follows Single Responsibility Principle - only handles coordination and lifecycle management.
    """

    def __init__(self):
        self.data_store = DataStore.set_shared_instance(DataStore())
        self.loop_managers: List[LoopManager] = []
        self.workflow_graph = WorkflowGraph()
        self.graph_traverser = GraphTraverser(self.workflow_graph)
        self.workflow_loader = WorkflowLoader(self.workflow_graph, NodeFactory())

    def create_loop(
        self, start_workflow_node: WorkflowNode, end_workflow_node: WorkflowNode
    ):
        """
        Create a loop from starting producer WorkflowNode to ending NonBlockingNode WorkflowNode.

        Args:
            start_workflow_node: Starting producer WorkflowNode
            end_workflow_node: Ending NonBlockingNode WorkflowNode
        """
        producer = start_workflow_node.instance
        chain = self.graph_traverser.build_chain_from_start_to_end(
            start_workflow_node, end_workflow_node
        )

        if not producer or not chain:
            raise ValueError(
                f"Invalid loop: producer or chain is empty for producer {start_workflow_node.id}"
            )

        manager = LoopManager(producer, chain)
        self.loop_managers.append(manager)

    async def run_production(self):
        """
        Start all loops.
        """
        logger.info("Starting Production Mode...")
        tasks = [manager.start() for manager in self.loop_managers]
        if not tasks:
            logger.info("No loops to run.")
            return
        await asyncio.gather(*tasks)

    async def run_development_node(
        self, node_id: str, input_data: NodeOutput
    ) -> NodeOutput:
        """
        Execute a single node directly (Development Mode).
        """
        logger.info(f"Development Mode: Executing node {node_id}")
        node = self.workflow_graph.get_node_instance(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        # In real dev mode, we would check Redis for upstream dependencies here

        return await node.execute(previous_node_output=input_data)

    def load_workflow(self, workflow_json: Dict[str, Any]):
        """
        Load workflow from JSON definition.
        Delegates to WorkflowLoader and uses GraphTraverser for traversal.
        """
        # Delegate workflow loading to WorkflowLoader
        self.workflow_loader.load_workflow(workflow_json)

        first_node_id = self.graph_traverser.get_first_node_id()
        if first_node_id:
            first_node = self.workflow_graph.node_map[first_node_id]
            logger.info(
                f"Workflow Loaded Successfully",
                graph=first_node.to_dict(),
            )
        else:
            raise ValueError("No first node found in the workflow")

        # Find loops using GraphTraverser
        loops = self.graph_traverser.find_loops()
        logger.debug(f"Found {len(loops)} loops")

        # Create loops from traversal results
        for start_node, end_node in loops:
            try:
                self.create_loop(start_node, end_node)
                logger.info(
                    f"Created Loop",
                    start_node_id=start_node.id,
                    end_node_id=end_node.id,
                )
            except ValueError as e:
                logger.warning(
                    f"Failed to create loop",
                    error=str(e),
                    start_node_id=start_node.id,
                    end_node_id=end_node.id,
                )
