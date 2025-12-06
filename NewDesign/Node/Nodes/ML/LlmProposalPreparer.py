from ...Core.Node.Core import BlockingNode, NodeOutput, PoolType
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class LlmProposalPreparer(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "llm-proposal-preparer"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.PROCESS

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        logger.info(f"[{self.config.type}] Preparing proposal with LLM...")
        await asyncio.sleep(1.0)
        node_data.data["proposal"] = "Generated Proposal Content..."
        return node_data
