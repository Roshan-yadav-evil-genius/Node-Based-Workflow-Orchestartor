from ...Core.BlockingNode import BlockingNode
from ...Core.NodeData import NodeData
from ...Core.ExecutionPool import ExecutionPool
import asyncio
import structlog
import random

logger = structlog.get_logger(__name__)

class CosineSimilarity(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "cosine-similarity"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:

        logger.info("Calculating cosine similarity...",node_id=self.config.node_id)

        
        await asyncio.sleep(5)

        # similarity is a number between 0 and 1
        similarity = random.random()

        node_data.payload["similarity_score"] = similarity

        logger.info("Similarity: {similarity}",node_id=self.config.node_id,similarity=similarity)

        
        return NodeData(
            id=self.config.node_id,
            payload=node_data.payload,
            metadata=node_data.metadata
        )
