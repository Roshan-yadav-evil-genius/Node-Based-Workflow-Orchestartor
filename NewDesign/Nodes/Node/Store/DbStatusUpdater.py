from ...Core.NonBlockingNode import NonBlockingNode
from ...Core.NodeData import NodeData
from ...Core.ExecutionPool import ExecutionPool
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class DbStatusUpdater(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "db-status-updater"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.THREAD

    async def execute(self, node_data: NodeData) -> NodeData:
        logger.info(f"[{self.config.node_name}] Updating DB status...")
        await asyncio.sleep(0.2)
        return node_data
