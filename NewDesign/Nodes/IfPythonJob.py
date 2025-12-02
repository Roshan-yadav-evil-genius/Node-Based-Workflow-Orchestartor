from .BlockingNode import BlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
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
        logger.info(f"[{self.config.node_name}] Checking if job is Python related...")
        await asyncio.sleep(0.1)
        
        title = node_data.payload.get("job_title", "").lower()
        is_python = "python" in title
        
        # In a real graph, we would handle conditional edges here.
        # For this simulation, we'll just add a flag to metadata.
        node_data.metadata["is_python"] = is_python
        logger.info(f"[{self.config.node_name}] Is Python? {is_python}")
        
        return node_data
