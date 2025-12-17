from typing import Optional
import structlog
from ....Core.Node.Core import BlockingNode, NodeOutput, PoolType
from ....Core.Form.Core.BaseForm import BaseForm
from .LinkedinProfileParserForm import LinkedinProfileParserForm
from ..extractors.linkedin import LinkedInProfileExtractor

logger = structlog.get_logger(__name__)

class LinkedinProfileParser(BlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "linkedin-profile-parser"

    @property
    def execution_pool(self) -> PoolType:
        # Parsing is CPU bound, so run in thread pool (SYNC)
        return PoolType.ASYNC

    def get_form(self) -> Optional[BaseForm]:
        return LinkedinProfileParserForm()

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        """
        Parse Linkedin Profile HTML.
        Expects 'content' or 'html' in input data (string).
        """
        # Check form for HTML content first
        
        html_content = self.form.cleaned_data.get("html_content")

        try:
            extractor = LinkedInProfileExtractor(html_content)
            extracted_data =  extractor.extract()
            
            node_data.data["parsed_linkedin_profile"] = extracted_data
            
            return node_data

        except Exception as e:
            logger.exception("Error parsing Linkedin Profile", error=str(e))
            raise e