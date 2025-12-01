from .BlockingNode import BlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio

class StoreNode(BlockingNode):
    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        store_name = self.config.dict().get("store_name", "default_store") # Access config safely
        print(f"[{self.config.node_name}] Storing job in {store_name}...")
        await asyncio.sleep(0.2)
        return node_data
