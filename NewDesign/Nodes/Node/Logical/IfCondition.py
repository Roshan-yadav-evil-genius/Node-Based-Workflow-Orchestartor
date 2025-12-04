from ...Core import LogicalNodes, NodeOutput, PoolType
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class IfCondition(LogicalNodes):
    @classmethod
    def identifier(cls) -> str:
        return "if-condition"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        logger.info("Performing condition check...",node_id=self.config.id)

        await asyncio.sleep(5)
        
        title = node_data.data.get("job_title", "").lower()
        node_data.metadata["condition"] = "python" in title

        logger.info("If condition Executed",node_id=self.config.id,condition=node_data.metadata["condition"])
        
        return NodeOutput(
            id=self.config.id,
            data=node_data.data,
            metadata=node_data.metadata
        )
