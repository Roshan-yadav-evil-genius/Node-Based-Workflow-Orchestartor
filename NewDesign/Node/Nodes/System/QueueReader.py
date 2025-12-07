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

    async def setup(self):
        """Initialize the DataStore connection once during node setup."""
        self.data_store = DataStore()

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        """
        Execute the queue reader by popping data from the queue.
        
        Uses DataStore's queue service for queue operations.
        Blocks indefinitely until data is available.
        """
        # Extract queue name from node config (validated by NodeValidator)
        queue_name = self.node_config.data.config["queue_name"]
        
        # Pop data from queue using the new SRP-compliant API
        # (blocks indefinitely until data arrives)
        result = await self.data_store.queue.pop(queue_name, timeout=0)

        logger.info(
            "Popped from queue",
            queue_name=queue_name,
            node_id=self.node_config.id,
            node_type=f"{node_type(self)}({self.identifier()})"
        )
        
        return NodeOutput(**result)
