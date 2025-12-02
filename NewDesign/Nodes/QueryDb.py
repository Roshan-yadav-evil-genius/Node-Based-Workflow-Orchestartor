from .ProducerNode import ProducerNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio

class QueryDb(ProducerNode):
    @classmethod
    def identifier(cls) -> str:
        return "query-db"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        print(f"[{self.config.node_name}] Querying DB...")
        await asyncio.sleep(0.2)
        return node_data
