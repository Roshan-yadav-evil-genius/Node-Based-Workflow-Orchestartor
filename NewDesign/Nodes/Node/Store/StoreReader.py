from ...Core.ProducerNode import ProducerNode
from ...Core.NodeData import NodeData
from ...Core.ExecutionPool import ExecutionPool
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class StoreReader(ProducerNode):
    @classmethod
    def identifier(cls) -> str:
        return "store-reader"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        logger.info(f"[{self.config.node_name}] Reading job from store...")
        await asyncio.sleep(0.1)
        return node_data
