from Node.Nodes.Playwright.PlaywrightFreelanceBidderForm import PlaywrightFreelanceBidderForm
from ...Core.Form.Core.BaseForm import BaseForm
from ...Core.Node.Core import NonBlockingNode, NodeOutput, PoolType
import asyncio
import structlog

logger = structlog.get_logger(__name__)

class PlaywrightFreelanceBidder(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "playwright-freelance-bidder"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        logger.info("[PlaywrightFreelanceBidder] Executing node")
        await asyncio.sleep(1.5)
        return node_data

    def get_form(self) -> BaseForm:
        return PlaywrightFreelanceBidderForm()
        # TODO: Impliment the way to populate the self.form with the data
