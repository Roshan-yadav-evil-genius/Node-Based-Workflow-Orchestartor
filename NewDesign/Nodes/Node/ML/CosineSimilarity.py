from ...Core import BlockingNode, NodeOutput, PoolType
import asyncio
import structlog
import random

logger = structlog.get_logger(__name__)

class CosineSimilarity(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "cosine-similarity"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:

        logger.info("Calculating cosine similarity...",node_id=self.config.id)

        
        await asyncio.sleep(5)

        # similarity is a number between 0 and 1
        similarity = random.random()

        node_data.data["similarity_score"] = similarity

        logger.info("Similarity: {similarity}",node_id=self.config.id,similarity=similarity)

        
        return NodeOutput(
            id=self.config.id,
            data=node_data.data,
            metadata=node_data.metadata
        )
