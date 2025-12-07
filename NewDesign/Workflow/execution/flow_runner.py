import asyncio
import structlog
from typing import Optional
from Node.Core.Node.Core.BaseNode import ProducerNode, NonBlockingNode, LogicalNode
from Node.Core.Node.Core.Data import NodeOutput
from ..flow_utils import node_type
from ..flow_node import FlowNode
from .pool_executor import PoolExecutor

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
                logger.info("Node execution completed", node_id=self.producer_flow_node.id, node_type=f"{node_type(producer)}({producer.identifier()})", output=data.data)
                
                current = self.producer_flow_node
                while True:
                    next_nodes = current.next
                    if not next_nodes:
                        break
                    
                    branch_key = "default" if "default" in next_nodes else list(next_nodes.keys())[0]
                    next_list = next_nodes.get(branch_key, [])
                    if not next_list:
                        break
                    
                    next_flow_node = next_list[0]
                    next_instance = next_flow_node.instance
                    logger.info("Initiating node execution", node_id=next_flow_node.id, node_type=f"{node_type(next_instance)}({next_instance.identifier()})")
                    data = await self.executor.execute_in_pool(
                        next_instance.execution_pool, next_instance, data
                    )
                    logger.info("Node execution completed", node_id=next_flow_node.id, node_type=f"{node_type(next_instance)}({next_instance.identifier()})", output=data.data)
                    
                    if isinstance(next_instance, NonBlockingNode):
                        break
                    
                    current = next_flow_node

            except Exception as e:
                logger.exception("Error in loop", error=str(e))
                await asyncio.sleep(1)

    def stop(self):
        self.running = False

    def shutdown(self):
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
