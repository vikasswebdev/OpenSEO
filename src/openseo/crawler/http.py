"""
HTTP crawler using httpx.

Handles standard HTTP/HTTPS pages without JavaScript rendering.
"""

from __future__ import annotations

import logging
import time

import httpx

from openseo.constants import CRAWLER_TIMEOUT, MAX_REDIRECTS, USER_AGENT
from openseo.crawler.base import BaseCrawler
from openseo.crawler.extractor import PageExtractor
from openseo.exceptions import FetchError
from openseo.models.page import Page

logger = logging.getLogger(__name__)


class HttpCrawler(BaseCrawler):
    """
    Crawls pages using httpx (async, follows redirects, no JS).

    This is the default crawler. Use PlaywrightCrawler for JS-heavy pages.
    """

    def __init__(
        self,
        timeout: float = CRAWLER_TIMEOUT,
        follow_redirects: bool = True,
        max_redirects: int = MAX_REDIRECTS,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._timeout = timeout
        self._headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            **(headers or {}),
        }
        self._client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
            headers=self._headers,
        )

    async def fetch(self, url: str) -> Page:
        """
        Fetch a URL and extract all SEO data.

        Args:
            url: URL to crawl

        Returns:
            Populated Page model

        Raises:
            FetchError: If the request fails
        """
        logger.info("Fetching: %s", url)
        start = time.monotonic()

        try:
            response = await self._client.get(url)
        except httpx.TimeoutException as e:
            raise FetchError(url, f"Request timed out after {self._timeout}s") from e
        except httpx.RequestError as e:
            raise FetchError(url, str(e)) from e

        elapsed_ms = (time.monotonic() - start) * 1000
        logger.debug("Fetched %s in %.0fms (status=%d)", url, elapsed_ms, response.status_code)

        if response.status_code >= 400:
            logger.warning("HTTP %d for %s", response.status_code, url)

        html = response.text
        final_url = str(response.url)

        # Extract all SEO data
        extractor = PageExtractor(base_url=final_url, html=html)
        extracted = extractor.extract()

        return Page(
            url=url,
            final_url=final_url if final_url != url else None,
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
            response_time_ms=round(elapsed_ms, 2),
            page_size_bytes=len(response.content),
            is_js_rendered=False,
            **extracted,
        )

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()
        logger.debug("HttpCrawler closed")


__all__ = ["HttpCrawler"]
