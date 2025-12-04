from ...Core import ProducerNode, NodeOutput, PoolType
from storage.data_store import DataStore
import structlog

logger = structlog.get_logger(__name__)

class QueueReader(ProducerNode):
    @classmethod
    def identifier(cls) -> str:
        return "queue-reader-dummy"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        """
        Execute the queue reader by popping data from the queue.
        
        Uses DataStore.get_shared_instance() to access the shared DataStore
        instance for queue operations. Blocks indefinitely until data is available.
        """
        data_store = DataStore.get_shared_instance()
        
        # Extract queue name from node config
        queue_name = self.config.data.get("queue_name", "default")
        
        # Pop data from queue (blocks indefinitely until data arrives)
        logger.info(f"[{self.config.type}] Reading data from queue '{queue_name}' (blocking indefinitely)...")
        result = await data_store.pop(queue_name, timeout=None)
        
        # Return the data from queue
        logger.info(f"[{self.config.type}] Received data from queue '{queue_name}': {result}")
        return result
