import asyncio
import structlog
from typing import Dict, List, Optional
from Node.Core.Node.Core.BaseNode import ProducerNode, NonBlockingNode, ConditionalNode
from Node.Core.Node.Core.Data import NodeOutput
from ..flow_utils import node_type
from ..flow_node import FlowNode
from .pool_executor import PoolExecutor
from Node.Core.Node.Core.Data import ExecutionCompleted


logger = structlog.get_logger(__name__)


class FlowRunner:
    """
    Manages a single flow loop in Production Mode.
    """

    def __init__(self, producer_flow_node: FlowNode, executor: Optional[PoolExecutor] = None):
        self.producer_flow_node = producer_flow_node
        self.producer = producer_flow_node.instance
        self.executor = executor or PoolExecutor()
        self.running = False
        self.loop_count = 0

    async def start(self):
        self.running = True
        await self._init_nodes()
        
        while self.running:
            self.loop_count += 1
            try:
                producer = self.producer_flow_node.instance
                logger.info("Initiating node execution", node_id=self.producer_flow_node.id, node_type=f"{node_type(producer)}({producer.identifier()})")
                data = await self.executor.execute_in_pool(
                    producer.execution_pool, producer, NodeOutput(data={})
                )
                logger.info(
                    "Node execution completed",
                    node_id=self.producer_flow_node.id,
                    node_type=f"{node_type(producer)}({producer.identifier()})",
                    output=data.data,
                )

                if isinstance(data, ExecutionCompleted):
                    await self.kill_producer()

                await self._process_next_nodes(self.producer_flow_node, data)

            except Exception as e:
                logger.exception("Error in loop", error=str(e))
                await asyncio.sleep(1)
        else:
           self.shutdown()


    async def _process_next_nodes(
        self, current_flow_node: FlowNode, input_data: NodeOutput
    ):
        """
        Recursively process downstream nodes.
        Handles branching logic:
        - If LogicalNode: Executes selected branch (if any).
        - Otherwise: Executes default branch or first available branch.
        """
        next_nodes: Optional[Dict[str, List[FlowNode]]] = current_flow_node.next
        if not next_nodes:
            # No next nodes, break the loop
            return

        instance = current_flow_node.instance
        nodes_to_run: List[FlowNode] = []
        keys_to_process = set()

        # Determine which branches to follow
        if isinstance(input_data, ExecutionCompleted):
            # If Sentinel Pill, broadcast to ALL downstream nodes regardless of logic
            for key in next_nodes:
                keys_to_process.add(key)

        elif isinstance(instance, ConditionalNode):
            # For LogicalNodes, we follow the selected output branch
            if instance.output:
                keys_to_process.add(instance.output)
        else:
            # For non-LogicalNodes, we follow the default branch
            keys_to_process.add("default")

        # Collect all nodes from selected branches
        for key in keys_to_process:
            if key in next_nodes:
                nodes_to_run.extend(next_nodes[key])

        # Execute selected nodes
        for next_flow_node in nodes_to_run:
            next_instance = next_flow_node.instance

            logger.info(
                "Initiating node execution",
                node_id=next_flow_node.id,
                node_type=f"{node_type(next_instance)}({next_instance.identifier()})",
            )

            try:
                data = await self.executor.execute_in_pool(
                    next_instance.execution_pool, next_instance, input_data
                )

                logger.info(
                    "Node execution completed",
                    node_id=next_flow_node.id,
                    node_type=f"{node_type(next_instance)}({next_instance.identifier()})",
                    output=data.data,
                )

                if isinstance(next_instance, NonBlockingNode):
                    continue

                # Recurse for the next steps in this branch
                await self._process_next_nodes(next_flow_node, data)

            except Exception as e:
                logger.exception(
                    "Error executing node", node_id=next_flow_node.id, error=str(e)
                )

            except Exception as e:
                logger.exception("Error in loop", error=str(e))
                await asyncio.sleep(1)

    async def kill_producer(self):
        # Clean up producer resources
        await self.producer.cleanup()
        # Set running to False to stop next iteration
        self.running = False

    def shutdown(self):
        logger.info("Shutting down FlowRunner", loop_count=self.loop_count,  node_id=self.producer_flow_node.id, node_type=f"{node_type(self.producer)}({self.producer.identifier()})")
        self.executor.shutdown()

    async def _init_nodes(self):
        """Initialize all nodes in the flow by calling their init() method."""
        visited = set()
        await self._init_node_recursive(self.producer_flow_node, visited)

    async def _init_node_recursive(self, flow_node: FlowNode, visited: set):
        """Recursively initialize a node and its downstream nodes."""
        if flow_node.id in visited:
            return
        visited.add(flow_node.id)
        
        await flow_node.instance.init()
        
        for branch_nodes in flow_node.next.values():
            for next_node in branch_nodes:
                await self._init_node_recursive(next_node, visited)
