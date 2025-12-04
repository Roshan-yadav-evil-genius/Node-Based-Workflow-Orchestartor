from ...Core import NonBlockingNode, NodeOutput, PoolType
from storage.data_store import DataStore
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

    def ready(self) -> dict:
        """
        Validate that queue_name is present in config.
        
        Returns:
            Dictionary mapping field names to error messages.
            Empty dict if node is ready, non-empty dict if validation fails.
        """
        errors = {}
        
        if not self.config.data or not self.config.data.get("queue_name"):
            errors["queue_name"] = "Missing required field 'queue_name' in config"
        
        return errors

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        """
        Execute the queue node by pushing data to the queue.
        
        Uses DataStore singleton instance for queue operations.
        """
        data_store = DataStore()
        
        # Extract queue name from node config (validated by NodeValidator)
        queue_name = self.config.data["queue_name"]
        
        # Push data to queue
        await data_store.push(queue_name, node_data.to_dict())
        
        return node_data
