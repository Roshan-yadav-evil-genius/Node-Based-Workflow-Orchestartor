from ...Core import ProducerNode, NodeOutput, PoolType
from storage.data_store import DataStore
import asyncio
import structlog
import uuid

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
        instance for queue operations. Blocks until data is available or timeout occurs.
        """
        data_store = DataStore.get_shared_instance()
        
        # Extract queue name and timeout from node config
        config_dict = self.config.dict()
        queue_name = config_dict.get("queue_name", "default")
        timeout = config_dict.get("timeout", 5.0)  # Default 5 seconds
        
        # Pop data from queue
        logger.info(f"[{self.config.type}] Reading data from queue '{queue_name}' (timeout: {timeout}s)...")
        result = await data_store.pop(queue_name, timeout)
        
        if result is None:
            # Timeout occurred - return empty data to allow loop to continue
            logger.warning(f"[{self.config.type}] Timeout waiting for data from queue '{queue_name}'")
            return NodeOutput(
                id=str(uuid.uuid4()),
                data={},
                metadata={"source": "queue_reader", "timeout": True}
            )
        
        # Return the data from queue
        logger.info(f"[{self.config.type}] Received data from queue '{queue_name}': {result}")
        return result
