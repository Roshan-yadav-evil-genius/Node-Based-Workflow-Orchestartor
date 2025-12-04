from ...Core import BlockingNode, NodeOutput, PoolType
import asyncio
import structlog
import random

logger = structlog.get_logger(__name__)


class AiMlScoring(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "ai-ml-scoring"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.PROCESS

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        logger.info(f"[{self.config.type}] Scoring job with AI/ML...")
        await asyncio.sleep(0.5)

        score = random.random()
        node_data.data["score"] = score
        logger.info(f"[{self.config.type}] Score: {score:.2f}")

        return node_data
