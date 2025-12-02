from ...Core.BlockingNode import BlockingNode
from ...Core.NodeData import NodeData
from ...Core.ExecutionPool import ExecutionPool
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class IfPythonJob(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "if-python-job"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        logger.info("Checking if job is Python related...",node_id=self.config.node_id)

        await asyncio.sleep(5)
        
        title = node_data.payload.get("job_title", "").lower()
        is_python = "python" in title
        
        # In a real graph, we would handle conditional edges here.
        # For this simulation, we'll just add a flag to metadata.
        node_data.metadata["condition"] = is_python
        logger.info("Condition: {is_python}",node_id=self.config.node_id,condition=is_python)
        
        return node_data
