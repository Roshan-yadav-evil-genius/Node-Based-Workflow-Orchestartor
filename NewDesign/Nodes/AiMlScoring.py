from .BlockingNode import BlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio
import random

class AiMlScoring(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "ai-ml-scoring"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        print(f"[{self.config.node_name}] Scoring job with AI/ML...")
        await asyncio.sleep(0.5)
        
        score = random.random()
        node_data.payload["score"] = score
        print(f"[{self.config.node_name}] Score: {score:.2f}")
        
        return node_data
