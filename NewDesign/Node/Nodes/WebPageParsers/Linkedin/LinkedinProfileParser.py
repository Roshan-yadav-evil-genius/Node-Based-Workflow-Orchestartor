from typing import Any, Dict, List, Optional
import structlog
from scrapy import Selector
from ....Core.Node.Core import BlockingNode, NodeOutput, PoolType
from ....Core.Form.Core.BaseForm import BaseForm
from .LinkedinProfileParserForm import LinkedinProfileParserForm
from .extractors.header import HeaderExtractor
from .extractors.metrics import MetricsExtractor
from .extractors.experience import ExperienceExtractor
from .extractors.education import EducationExtractor
from .extractors.section import SectionExtractor

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
            extracted_data = self.extract_data_from_html(html_content)
            
            node_data.data["parsed_linkedin_profile"] = extracted_data
            
            return node_data

        except Exception as e:
            logger.exception("Error parsing Linkedin Profile", error=str(e))
            raise e

    def extract_data_from_html(self, html_content: str) -> Dict[str, Any]:
        sel = Selector(text=html_content)
        data = {}

        # 1. Header (Name, Headline, Location, About)
        header_ext = HeaderExtractor(sel)
        data.update(header_ext.extract())

        # 2. Metrics (Followers, Connections)
        metrics_ext = MetricsExtractor(sel)
        data.update(metrics_ext.extract())

        # 3. Experience
        exp_ext = ExperienceExtractor(sel)
        data["experience"] = exp_ext.extract()

        # 4. Education
        edu_ext = EducationExtractor(sel)
        data["education"] = edu_ext.extract()

        # 5. Generic Sections (Skills, Projects, etc.)
        section_ext = SectionExtractor(sel)

        # Skills
        skills_data = section_ext.extract_section(["Skills"])
        data["skills"] = [s.get("title") for s in skills_data if s.get("title")]

        data["licenses_and_certifications"] = section_ext.extract_section(
            ["Licenses & certifications"]
        )
        data["volunteering"] = section_ext.extract_section(["Volunteering"])
        data["projects"] = section_ext.extract_section(["Projects"])
        data["honors_and_awards"] = section_ext.extract_section(["Honors & awards"])
        data["languages"] = section_ext.extract_section(["Languages"])
        data["publications"] = section_ext.extract_section(["Publications"])
        data["recommendations"] = section_ext.extract_section(["Recommendations"])

        return data
