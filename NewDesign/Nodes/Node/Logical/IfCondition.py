from ...Core.LogicalNodes import LogicalNodes
from ...Core.NodeData import NodeData
from ...Core.ExecutionPool import ExecutionPool
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class IfCondition(LogicalNodes):
    @classmethod
    def identifier(cls) -> str:
        return "if-condition"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        logger.info("Performing condition check...",node_id=self.config.node_id)

        await asyncio.sleep(5)
        
        title = node_data.payload.get("job_title", "").lower()
        node_data.metadata["condition"] = "python" in title

        logger.info("If condition Executed",node_id=self.config.node_id,condition=node_data.metadata["condition"])
        
        return NodeData(
            id=self.config.node_id,
            payload=node_data.payload,
            metadata=node_data.metadata
        )
