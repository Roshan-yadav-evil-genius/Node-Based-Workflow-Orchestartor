from .NonBlockingNode import NonBlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class DbNode(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "db-node"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        logger.info(f"[{self.config.node_name}] Saving to DB...")
        await asyncio.sleep(0.3)
        return node_data
