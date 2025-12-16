from .BidderForm import BidderForm
from ....Core.Form.Core.BaseForm import BaseForm
from ....Core.Node.Core import NonBlockingNode, NodeOutput, PoolType
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class Bidder(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "playwright-freelance-bidder"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        await asyncio.sleep(1.5)
        node_data.data["Bidder"] = "Bidder"  # TODO: Implement the bidder logic
        return node_data

    def get_form(self) -> BaseForm:
        return BidderForm()
        # TODO: Impliment the way to populate the self.form with the data
