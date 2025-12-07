from ...Core.Node.Core import BlockingNode, NodeOutput, PoolType
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class TelegramSender(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "telegram-sender"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.THREAD

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        logger.info(f"[{self.node_config.type}] Sending Telegram notification...")
        await asyncio.sleep(0.4)
        return node_data
