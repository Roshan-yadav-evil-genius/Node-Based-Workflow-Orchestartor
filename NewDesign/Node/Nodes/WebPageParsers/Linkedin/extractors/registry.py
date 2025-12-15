# Centralized Selector Registry
#
# Strategy:
# - Use generic container queries where possible
# - Prioritize ID and ARIA attributes over Tailwind classes
# - Group selectors by component

SELECTORS = {
    "header": {
        "name": [
            '//h1[contains(@class, "text-heading-xlarge")]/text()',
            "//h1//text()",
            '//*[@id="ember33"]/h1/text()',  # Highly specific fallback
        ],
        "headline": [
            '//div[contains(@class, "text-body-medium") and contains(@class, "break-words")]/text()',
            "//div[@data-generated-suggestion-target]/text()",
        ],
        "location": [
            '//span[contains(@class, "text-body-small") and contains(@class, "inline") and contains(@class, "break-words")]/text()',
            '//div[contains(@class, "mt2")]//span[contains(@class, "text-body-small")]/text()',
        ],
        "about": [
            './/div[contains(@class, "inline-show-more-text")]//span[@aria-hidden="true"]/text()',
            '//div[contains(@class, "pv-about__summary-text")]//text()',
            '//*[@id="about"]//following-sibling::div//span[@aria-hidden="true"]/text()',
        ],
    },
    "metrics": {
        "followers": [
            '//li//span[contains(text(), "followers")]/text()',
            '//*[contains(@class, "t-bold") and contains(text(), "followers")]/text()',
        ],
        "connections": [
            '//span[contains(@class, "t-bold") and contains(text(), "500+")]/text()',
            '//span[contains(text(), "connections")]/text()',
        ],
    },
    "section": {
        "root": "ancestor::section[1]",
        "list_item": './/li[contains(@class, "artdeco-list__item")]',
        "item_title": [
            './/div[contains(@class, "display-flex")]//span[@aria-hidden="true"]/text()',  # General title
            './/span[@class="t-bold"]/text()',  # Classic fallback
            './/div[contains(@class, "t-bold")]/span/text()',
        ],
        "item_subtitle": [
            './/span[contains(@class, "t-14")]//span[@aria-hidden="true"]/text()',
            './/span[contains(text(), "·")]/preceding-sibling::text()',
            './/span[contains(@class, "t-normal")]/span[@aria-hidden="true"]/text()',
        ],
        "item_meta": [
            './/span[contains(@class, "t-black--light")]/span[@aria-hidden="true"]/text()',
            './/span[contains(@class, "t-black--light")]/text()',
        ],
    },
}
