from typing import Any, Dict, List
import structlog
from scrapy import Selector
from ...Core.Node.Core import BaseNode, NodeOutput, PoolType
from .extractors.header import HeaderExtractor
from .extractors.metrics import MetricsExtractor
from .extractors.experience import ExperienceExtractor
from .extractors.education import EducationExtractor
from .extractors.section import SectionExtractor

logger = structlog.get_logger(__name__)

class LinkedinProfileParser(BaseNode):
    @classmethod
    def identifier(cls) -> str:
        return "linkedin-profile-parser"

    @property
    def execution_pool(self) -> PoolType:
        # Parsing is CPU bound, so run in thread pool (SYNC)
        return PoolType.SYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        """
        Parse Linkedin Profile HTML.
        Expects 'content' or 'html' in input data (string).
        """
        # Check form for HTML content first
        form_data = self.node_config.data.form or {}
        html_content = form_data.get("html_content")

        try:
            logger.info("Starting Linkedin Profile Parsing")
            extracted_data = self.extract_data_from_html(html_content)
            logger.info("Parsing completed successfully")
            
            # Wrap data to match expected structure
            final_data = {
                "status": "success",
                "data": extracted_data
            }
            
            return NodeOutput(
                id=self.node_config.id,
                data=final_data,
                metadata={
                    "sourceNodeID": self.node_config.id,
                    "sourceNodeName": self.identifier()
                }
            )
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
