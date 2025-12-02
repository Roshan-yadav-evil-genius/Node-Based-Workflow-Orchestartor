from .NonBlockingNode import NonBlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio


class DbStatusUpdater(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "db-status-updater"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.THREAD

    async def execute(self, node_data: NodeData) -> NodeData:
        print(f"[{self.config.node_name}] Updating DB status...")
        await asyncio.sleep(0.2)
        return node_data
