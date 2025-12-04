from ...Core import NonBlockingNode, NodeOutput, PoolType
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class StoreNode(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "store-node"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        store_name = self.config.dict().get("store_name", "default_store") # Access config safely
        logger.info(f"[{self.config.node_name}] Storing job in {store_name}...")
        await asyncio.sleep(0.2)
        return node_data
