from ...Core.Node.Core import BlockingNode, NodeOutput, PoolType
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
        await asyncio.sleep(0.5)

        score = random.random()
        node_data.data["score"] = score

        return node_data
