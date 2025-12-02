from ...Core.BlockingNode import BlockingNode
from ...Core.NodeData import NodeData
from ...Core.ExecutionPool import ExecutionPool
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class IfScoreThreshold(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "if-score-threshold"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        threshold = self.config.dict().get("threshold", 0.5)
        score = node_data.payload.get("score", 0.0)
        
        logger.info(f"[{self.config.node_name}] Checking if score {score:.2f} > {threshold}...")
        await asyncio.sleep(0.1)
        
        passed = score > threshold
        node_data.metadata["score_passed"] = passed
        logger.info(f"[{self.config.node_name}] Passed? {passed}")
        
        return node_data
