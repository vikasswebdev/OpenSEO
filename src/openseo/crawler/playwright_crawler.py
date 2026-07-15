"""
Playwright-based crawler for JavaScript-rendered pages.

Falls back gracefully if Playwright is not installed.
"""

from __future__ import annotations

import logging
import time

from openseo.crawler.base import BaseCrawler
from openseo.crawler.extractor import PageExtractor
from openseo.exceptions import FetchError, PlaywrightNotInstalledError
from openseo.models.page import Page

logger = logging.getLogger(__name__)


class PlaywrightCrawler(BaseCrawler):
    """
    Crawls JavaScript-heavy pages using Playwright (Chromium).

    Install Playwright extra: pip install 'openseo[playwright]'
    Then: playwright install chromium
    """

    def __init__(self, timeout: int = 30000) -> None:
        self._timeout = timeout  # ms
        self._browser = None
        self._playwright = None

    async def _ensure_browser(self) -> None:
        """Lazily launch the browser."""
        if self._browser is not None:
            return

        try:
            from playwright.async_api import async_playwright  # type: ignore[import]
        except ImportError as e:
            raise PlaywrightNotInstalledError() from e

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        logger.debug("Playwright browser launched")

    async def fetch(self, url: str) -> Page:
        """
        Fetch a URL using a headless Chromium browser.

        Args:
            url: URL to crawl

        Returns:
            Populated Page model with JS-rendered content

        Raises:
            FetchError: If navigation fails
            PlaywrightNotInstalledError: If Playwright is not installed
        """
        await self._ensure_browser()
        assert self._browser is not None

        page = await self._browser.new_page()
        start = time.monotonic()

        try:
            response = await page.goto(
                url,
                wait_until="networkidle",
                timeout=self._timeout,
            )
            await page.wait_for_load_state("domcontentloaded")

            elapsed_ms = (time.monotonic() - start) * 1000
            html = await page.content()
            final_url = page.url

            status = response.status if response else None
            logger.debug(
                "Playwright fetched %s in %.0fms (status=%s)",
                url, elapsed_ms, status,
            )

        except Exception as e:
            raise FetchError(url, f"Playwright navigation failed: {e}") from e
        finally:
            await page.close()

        extractor = PageExtractor(base_url=final_url, html=html)
        extracted = extractor.extract()

        return Page(
            url=url,
            final_url=final_url if final_url != url else None,
            status_code=status,
            response_time_ms=round(elapsed_ms, 2),
            is_js_rendered=True,
            **extracted,
        )

    async def close(self) -> None:
        """Close the browser and Playwright instance."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.debug("PlaywrightCrawler closed")


__all__ = ["PlaywrightCrawler"]
