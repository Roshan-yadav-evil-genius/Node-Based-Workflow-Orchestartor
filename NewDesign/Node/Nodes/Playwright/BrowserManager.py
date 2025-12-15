import asyncio
from typing import Dict, Optional
from playwright.async_api import (
    async_playwright,
    Browser,
    Playwright,
    BrowserContext,
    Page,
)
import structlog

logger = structlog.get_logger(__name__)


class BrowserManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
            cls._instance._playwright: Optional[Playwright] = None
            cls._instance._contexts: Dict[str, BrowserContext] = {}
            cls._instance._initialized = False
            cls._instance._headless: bool = True
        return cls._instance

    async def initialize(self, headless: bool = True):
        """Initialize Playwright."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            logger.info("Initializing BrowserManager...")
            self._playwright = await async_playwright().start()
            self._headless = headless
            self._initialized = True
            logger.info("BrowserManager initialized successfully")

    async def get_context(self, context_name: str, **kwargs) -> BrowserContext:
        """
        Get an existing persistent context by name or create a new one.
        The context name is used as the directory name for the persistent session.
        """
        if not self._initialized:
            await self.initialize()

        if context_name in self._contexts:
            logger.info(f"Reusing existing persistent context: {context_name}")
            return self._contexts[context_name]

        logger.info(f"Creating new persistent context: {context_name}")
        user_data_dir = f"sessions/{context_name}"

        # Merge default args with kwargs
        launch_args = {
            "headless": self._headless,
            "args": [
                "--disable-blink-features=AutomationControlled"
            ],  # Standard anti-bot mitigation
        }
        launch_args.update(kwargs)

        context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir, **launch_args
        )
        self._contexts[context_name] = context
        return context

    async def get_or_create_page(self, context: BrowserContext, url: str) -> Page:
        """
        Check if any page in the given context is already at the specified URL.
        If yes, return that page.
        Else, create a new page, navigate to the URL, and return it.
        """
        # Normalize URL for comparison (remove trailing slash)
        target_url = url.rstrip("/")

        for page in context.pages:
            current_url = page.url.rstrip("/")
            if current_url == target_url:
                logger.info(f"Page already exists for URL: {url}")
                return page

        logger.info(f"Creating new page for URL: {url}")
        page = await context.new_page()
        await page.goto(url,wait_until="commit")
        return page

    async def close(self):
        """Close all contexts and playwright."""
        logger.info("Closing BrowserManager...")
        for name, context in self._contexts.items():
            await context.close()
        self._contexts.clear()

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        self._initialized = False
        logger.info("BrowserManager closed")
