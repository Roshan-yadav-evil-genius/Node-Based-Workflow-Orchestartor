from ...Core import NonBlockingNode, NodeOutput, PoolType
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class DbNode(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "db-node"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        logger.info(f"[{self.config.type}] Saving to DB...")
        await asyncio.sleep(0.3)
        return node_data
