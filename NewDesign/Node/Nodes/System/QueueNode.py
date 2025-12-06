from ...Core.Node.Core import NonBlockingNode, NodeOutput, PoolType
from Workflow.storage.data_store import DataStore
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class QueueNode(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "queue-node-dummy"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        """
        Execute the queue node by pushing data to the queue.
        
        Uses DataStore's queue service for queue operations.
        """
        data_store = DataStore()
        
        # Extract queue name from node config (validated by NodeValidator)
        queue_name = self.config.data["queue_name"]
        
        # Push data to queue using the new SRP-compliant API
        await data_store.queue.push(queue_name, node_data.to_dict())
        
        return node_data
