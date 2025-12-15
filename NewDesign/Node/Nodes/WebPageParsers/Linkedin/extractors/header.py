from .base import BaseExtractor
from .registry import SELECTORS


class HeaderExtractor(BaseExtractor):
    def extract(self):
        data = {}
        header_sels = SELECTORS["header"]

        data["name"] = self.extract_with_fallback("name", header_sels["name"])
        data["headline"] = self.extract_with_fallback(
            "headline", header_sels["headline"]
        )
        data["location"] = self.extract_with_fallback(
            "location", header_sels["location"]
        )

        # About is slightly different, might need joining multiple p tags
        about_text = self.extract_with_fallback("about", header_sels["about"])
        data["about"] = about_text  # The base extractor cleans it already

        return data
