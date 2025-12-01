from .ProducerNode import ProducerNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio
import uuid

class QueueReader(ProducerNode):
    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        # Simulate reading from queue
        # In a real implementation, this would use QueueManager.pop
        print(f"[{self.config.node_name}] Reading data from queue...")
        await asyncio.sleep(0.1) # Simulate I/O
        
        # Return new data
        return NodeData(
            id=str(uuid.uuid4()), 
            payload={"data": "sample_data_from_queue"},
            metadata={"source": "queue_reader"}
        )
