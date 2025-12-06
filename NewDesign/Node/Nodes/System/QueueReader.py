from Workflow.flow_utils import node_type
from ...Core.Node.Core import ProducerNode, NodeOutput, PoolType
from Workflow.storage.data_store import DataStore
import structlog

logger = structlog.get_logger(__name__)

class QueueReader(ProducerNode):
    @classmethod
    def identifier(cls) -> str:
        return "queue-reader-dummy"

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
        Execute the queue reader by popping data from the queue.
        
        Uses DataStore singleton instance for queue operations. Blocks indefinitely until data is available.
        """
        data_store = DataStore()
        
        # Extract queue name from node config (validated by NodeValidator)
        queue_name = self.config.data["queue_name"]
        
        # Pop data from queue (blocks indefinitely until data arrives)
        result = await data_store.pop(queue_name, timeout=0)

        logger.info(f"Popped from queue",queue_name=queue_name, node_id=self.config.id, node_type=f"{node_type(self)}({self.identifier()})")
        
        return NodeOutput(**result)
