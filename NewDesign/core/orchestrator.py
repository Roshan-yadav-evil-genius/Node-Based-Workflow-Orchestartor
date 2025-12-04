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
        
        In Development Mode:
        1. Checks Redis cache for upstream node outputs
        2. Uses cached output as input if available, otherwise uses provided input_data
        3. Executes the node
        4. Stores the output in Redis cache for downstream nodes
        """
        logger.info(f"Development Mode: Executing node {node_id}")
        node = self.workflow_graph.get_node_instance(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        # Check Redis cache for upstream dependencies
        upstream_nodes = self.workflow_graph.get_upstream_nodes(node_id)
        
        # If there are upstream nodes, try to get their cached outputs
        # For now, we'll use the first upstream node's output if available
        # In a more complex scenario, we might need to merge multiple upstream outputs
        if upstream_nodes:
            # Try to get cached output from the first upstream node
            # In a real implementation, you might want to handle multiple upstream nodes
            upstream_node_id = upstream_nodes[0].id
            cached_output = await self.data_store.get_cache(f"{upstream_node_id}_output")
            
            if cached_output is not None:
                logger.info(
                    f"Development Mode: Using cached output from upstream node '{upstream_node_id}'"
                )
                # Use cached output as input
                if isinstance(cached_output, dict):
                    # If cached output is a dict, reconstruct NodeOutput from it
                    try:
                        input_data = NodeOutput(**cached_output)
                    except Exception as e:
                        logger.warning(
                            f"Development Mode: Failed to reconstruct NodeOutput from cache: {e}, using provided input_data"
                        )
                        # Keep the provided input_data if reconstruction fails
                else:
                    input_data = cached_output
            else:
                logger.debug(
                    f"Development Mode: No cached output found for upstream node '{upstream_node_id}', using provided input_data"
                )
        else:
            logger.debug(
                f"Development Mode: No upstream nodes found for '{node_id}', using provided input_data"
            )

        # Execute the node
        result = await node.execute(previous_node_output=input_data)
        
        # Store the output in Redis cache for downstream nodes
        cache_key = f"{node_id}_output"
        # Serialize NodeOutput to dict for caching using Pydantic's dict() method
        # Try model_dump() first (Pydantic v2), fall back to dict() (Pydantic v1)
        try:
            output_dict = result.model_dump() if hasattr(result, 'model_dump') else result.dict()
        except AttributeError:
            # Fallback: manually construct dict from fields
            output_dict = {
                "id": result.id,
                "data": result.data,
                "metadata": result.metadata
            }
        await self.data_store.set_cache(cache_key, output_dict)
        logger.info(f"Development Mode: Stored output for node '{node_id}' in cache")
        
        return result

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
