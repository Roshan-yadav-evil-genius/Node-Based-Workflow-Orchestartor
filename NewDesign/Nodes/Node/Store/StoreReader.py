from ...Core import ProducerNode, NodeOutput, PoolType
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class StoreReader(ProducerNode):
    @classmethod
    def identifier(cls) -> str:
        return "store-reader"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        logger.info(f"[{self.config.type}] Reading job from store...")
        await asyncio.sleep(0.1)
        return node_data
