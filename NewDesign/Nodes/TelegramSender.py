from .BlockingNode import BlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio

class TelegramSender(BlockingNode):
    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        print(f"[{self.config.node_name}] Sending Telegram notification...")
        await asyncio.sleep(0.4)
        return node_data
