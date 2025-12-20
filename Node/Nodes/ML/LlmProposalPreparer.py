from random import randint
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
        await asyncio.sleep(1.0)
        output_key = self.get_unique_output_key(node_data, "llm_proposal")
        node_data.data[output_key] = {
            "proposal": "Generated Proposal Content...",
            "bid_amount": randint(100, 1000),
            "estimated_delivery_days": randint(1, 10)
        }
        return node_data
