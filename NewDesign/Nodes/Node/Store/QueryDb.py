from ...Core import ProducerNode, NodeOutput, PoolType
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class QueryDb(ProducerNode):
    @classmethod
    def identifier(cls) -> str:
        return "query-db"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        logger.info(f"[{self.config.type}] Querying DB...")
        await asyncio.sleep(0.2)
        return node_data
