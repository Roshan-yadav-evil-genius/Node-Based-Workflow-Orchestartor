from ...Core.BlockingNode import BlockingNode
from ...Core.NodeData import NodeData
from ...Core.ExecutionPool import ExecutionPool
import asyncio
import structlog
import random

logger = structlog.get_logger(__name__)


class AiMlScoring(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "ai-ml-scoring"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.PROCESS

    async def execute(self, node_data: NodeData) -> NodeData:
        logger.info(f"[{self.config.node_name}] Scoring job with AI/ML...")
        await asyncio.sleep(0.5)

        score = random.random()
        node_data.payload["score"] = score
        logger.info(f"[{self.config.node_name}] Score: {score:.2f}")

        return node_data
