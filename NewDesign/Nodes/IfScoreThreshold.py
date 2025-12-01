from .BlockingNode import BlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio

class IfScoreThreshold(BlockingNode):
    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        threshold = self.config.dict().get("threshold", 0.5)
        score = node_data.payload.get("score", 0.0)
        
        print(f"[{self.config.node_name}] Checking if score {score:.2f} > {threshold}...")
        await asyncio.sleep(0.1)
        
        passed = score > threshold
        node_data.metadata["score_passed"] = passed
        print(f"[{self.config.node_name}] Passed? {passed}")
        
        return node_data
