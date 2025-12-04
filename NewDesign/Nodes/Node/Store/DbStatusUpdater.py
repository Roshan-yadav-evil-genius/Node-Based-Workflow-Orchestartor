from ...Core import NonBlockingNode, NodeOutput, PoolType
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class DbStatusUpdater(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "db-status-updater"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.THREAD

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        await asyncio.sleep(0.2)
        return node_data
