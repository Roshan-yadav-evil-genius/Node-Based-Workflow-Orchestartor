from scrapy import Selector
from .registry import SELECTORS
from .utils import clean_text
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BaseExtractor:
    def __init__(self, selector: Selector):
        self.selector = selector

    def extract_with_fallback(
        self, field_name: str, xpath_list: list, context=None
    ) -> str:
        """
        Tries a list of XPaths until one works.
        Optionally uses a context (snippet of Selector) instead of the global selector.
        """
        sel = context if context else self.selector

        for xpath in xpath_list:
            val = sel.xpath(xpath).get()
            if val:
                cleaned = clean_text(val)
                if cleaned:
                    return cleaned

        # Log failure only if it's a critical field or if we want high verbosity
        # logger.warning(f"Failed to extract '{field_name}' using any provided xpath.")
        return ""

    def extract_list(self, xpath_list: list, context=None) -> list:
        sel = context if context else self.selector
        for xpath in xpath_list:
            vals = sel.xpath(xpath).getall()
            if vals:
                cleaned = [clean_text(v) for v in vals if clean_text(v)]
                if cleaned:
                    return cleaned
        return []
