from .base import BaseExtractor
from .registry import SELECTORS
from .utils import clean_text


class SectionExtractor(BaseExtractor):
    def _get_section_root(self, header_texts: list):
        """
        Finds the section element (ancestor) based on a header text.
        Tries multiple header variations.
        """
        for header_text in header_texts:
            # Look for h2 containing the text, then get ancestor section
            # This is a bit dynamic so we construct xpath on the fly,
            # but we could also put this in registry if we wanted strict separation.
            # Keeping it here for flexibility with "header_texts" list.

            # This xpath matches any H2 that contains the text
            xpath = f'//h2//*[contains(text(), "{header_text}")]'
            header_node = self.selector.xpath(xpath)
            if header_node:
                root_xpath = SELECTORS["section"]["root"]
                return header_node[0].xpath(root_xpath)

            # Fallback: exact match on H2 or spans inside
            xpath_exact = (
                f'//span[normalize-space()="{header_text}"]/ancestor::section[1]'
            )
            node = self.selector.xpath(xpath_exact)
            if node:
                return node

        return None

    def extract_section(self, section_names: list):
        """
        Extracts a list of items from a section identified by one of the section_names.
        """
        root = self._get_section_root(section_names)
        if not root:
            return []

        items = []
        list_item_xpath = SELECTORS["section"]["list_item"]
        item_nodes = root.xpath(list_item_xpath)

        section_sels = SELECTORS["section"]

        for item in item_nodes:
            entry = {}

            # Title
            entry["title"] = self.extract_with_fallback(
                "title", section_sels["item_title"], context=item
            )

            # Subtitle
            entry["subtitle"] = self.extract_with_fallback(
                "subtitle", section_sels["item_subtitle"], context=item
            )

            # Meta (Date, Location, etc.) - This often has multiple parts
            # We can extract all matches and store them as meta_1, meta_2
            meta_vals = self.extract_list(section_sels["item_meta"], context=item)
            for i, val in enumerate(meta_vals):
                entry[f"meta_{i+1}"] = val

            items.append(entry)

        return items
