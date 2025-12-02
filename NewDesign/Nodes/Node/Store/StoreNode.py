from ...Core.NonBlockingNode import NonBlockingNode
from ...Core.NodeData import NodeData
from ...Core.ExecutionPool import ExecutionPool
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class StoreNode(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "store-node"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        store_name = self.config.dict().get("store_name", "default_store") # Access config safely
        logger.info(f"[{self.config.node_name}] Storing job in {store_name}...")
        await asyncio.sleep(0.2)
        return node_data
