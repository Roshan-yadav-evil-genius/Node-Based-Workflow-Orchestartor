from .NonBlockingNode import NonBlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio

class QueueNode(NonBlockingNode):
    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        # Simulate pushing to queue
        # In a real implementation, this would use QueueManager.push
        print(f"[{self.config.node_name}] Pushing data to queue: {node_data.payload}")
        await asyncio.sleep(0.1) # Simulate I/O
        return node_data
