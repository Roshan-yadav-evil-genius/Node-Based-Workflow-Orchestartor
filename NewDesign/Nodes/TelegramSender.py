from .BlockingNode import BlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class TelegramSender(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "telegram-sender"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.THREAD

    async def execute(self, node_data: NodeData) -> NodeData:
        logger.info(f"[{self.config.node_name}] Sending Telegram notification...")
        await asyncio.sleep(0.4)
        return node_data
