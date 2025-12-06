from ...Core.Form.Core.BaseForm import BaseForm
from .PlaceNodeForm import ContactForm
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
        logger.info(f"[{self.config.type}] Submitting bid via Playwright...")
        await asyncio.sleep(1.5)
        logger.info(f"[{self.config.type}] Bid submitted!")
        return node_data

    def get_form(self) -> BaseForm:
        return ContactForm()
