"""
Abstract crawler interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from openseo.models.page import Page


class BaseCrawler(ABC):
    """
    Abstract base class for page crawlers.

    Implementations: HttpCrawler (httpx), PlaywrightCrawler (JS rendering).
    """

    @abstractmethod
    async def fetch(self, url: str) -> Page:
        """
        Fetch a URL and return a populated Page model.

        Args:
            url: The URL to crawl

        Returns:
            Page with all extracted data

        Raises:
            FetchError: If the URL cannot be fetched
            CrawlerError: For other crawling failures
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources (close connections, browser, etc.)."""
        ...

    async def __aenter__(self) -> "BaseCrawler":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()


__all__ = ["BaseCrawler"]
