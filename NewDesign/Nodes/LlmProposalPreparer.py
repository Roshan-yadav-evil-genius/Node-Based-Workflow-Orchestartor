from .BlockingNode import BlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class LlmProposalPreparer(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "llm-proposal-preparer"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.PROCESS

    async def execute(self, node_data: NodeData) -> NodeData:
        logger.info(f"[{self.config.node_name}] Preparing proposal with LLM...")
        await asyncio.sleep(1.0)
        node_data.payload["proposal"] = "Generated Proposal Content..."
        return node_data
