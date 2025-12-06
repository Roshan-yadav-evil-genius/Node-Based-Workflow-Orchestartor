from ...Core.Node.Core import LogicalNode, NodeOutput, PoolType
import asyncio
import structlog
import random

logger = structlog.get_logger(__name__)

class IfCondition(LogicalNode):
    @classmethod
    def identifier(cls) -> str:
        return "if-condition"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:

        await asyncio.sleep(2)

        # Set output property for branch selection
        # 50% chance of true, 50% chance of false
        self.set_output(random.random() < 0.5)
        
        return NodeOutput(
            id=self.config.id,
            data=node_data.data,
            metadata=node_data.metadata
        )
