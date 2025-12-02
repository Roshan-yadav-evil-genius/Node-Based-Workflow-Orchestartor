from .NonBlockingNode import NonBlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio

class PlaywrightFreelanceBidder(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "playwright-freelance-bidder"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        print(f"[{self.config.node_name}] Submitting bid via Playwright...")
        await asyncio.sleep(1.5)
        print(f"[{self.config.node_name}] Bid submitted!")
        return node_data
