"""
Site-wide recursive crawler with robots.txt parsing and sitemap discovery.
"""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse, urlunparse
import urllib.robotparser
from bs4 import BeautifulSoup

from openseo.crawler.http import HttpCrawler
from openseo.crawler.playwright_crawler import PlaywrightCrawler
from openseo.models.page import Page
from openseo.constants import CRAWLER_TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize a URL to prevent duplicate crawls of the same resource."""
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    # lowercase hostname
    netloc = parsed.netloc.lower()
    # remove trailing slash from path unless it's empty
    path = parsed.path
    if path == "/":
        path = ""
    elif path.endswith("/"):
        path = path[:-1]
    # rebuild URL without fragments
    return urlunparse((parsed.scheme, netloc, path, parsed.params, parsed.query, ""))


def get_clean_domain(netloc: str) -> str:
    """Strip www. prefix from domain name for comparison."""
    netloc = netloc.lower()
    if netloc.startswith("www."):
        return netloc[4:]
    return netloc


class SiteCrawler:
    """
    Crawls an entire website recursively starting from a base URL.
    Respects robots.txt, processes sitemaps, and applies crawl boundaries.
    """

    def __init__(
        self,
        base_url: str,
        *,
        max_pages: int = 20,
        max_depth: int = 3,
        use_playwright: bool = False,
        ignore_robots: bool = False,
        sitemap_only: bool = False,
    ) -> None:
        self.base_url = normalize_url(base_url)
        self.parsed_base = urlparse(self.base_url)
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.use_playwright = use_playwright
        self.ignore_robots = ignore_robots
        self.sitemap_only = sitemap_only

        self.visited: dict[str, Page] = {}
        self.queue: list[tuple[str, int]] = [] if sitemap_only else [(self.base_url, 0)]
        self.sitemap_urls: list[str] = []
        self.sitemap_discovered_urls: set[str] = set()
        self.robots_txt_content: str | None = None
        self.rp = urllib.robotparser.RobotFileParser()

    async def initialize(self) -> None:
        """Fetch robots.txt and sitemaps to initialize crawler paths."""
        robots_url = urljoin(f"{self.parsed_base.scheme}://{self.parsed_base.netloc}", "/robots.txt")
        crawler = HttpCrawler()
        try:
            # Load robots.txt
            logger.info("Checking robots.txt at: %s", robots_url)
            page = await crawler.fetch(robots_url)
            if page.status_code == 200 and page.body_text:
                # Page extractor gets visible text. We need raw body, let's fetch it as text
                import httpx
                async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=CRAWLER_TIMEOUT) as client:
                    resp = await client.get(robots_url, follow_redirects=True)
                    if resp.status_code == 200:
                        self.robots_txt_content = resp.text
                        self.rp.parse(resp.text.splitlines())
            
            # Find sitemaps in robots.txt
            if self.robots_txt_content:
                for line in self.robots_txt_content.splitlines():
                    if line.lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        self.sitemap_urls.append(sitemap_url)
            
            # If no sitemaps found, try standard locations
            if not self.sitemap_urls:
                base = f"{self.parsed_base.scheme}://{self.parsed_base.netloc}"
                self.sitemap_urls.extend([
                    f"{base}/sitemap.xml",
                    f"{base}/sitemap_index.xml"
                ])

            # Seed queue with sitemap URLs (up to limit)
            for s_url in self.sitemap_urls:
                try:
                    import httpx
                    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=CRAWLER_TIMEOUT) as client:
                        resp = await client.get(s_url, follow_redirects=True)
                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.text, "xml")
                            locs = [loc.get_text() for loc in soup.find_all("loc")]
                            for loc in locs:
                                loc_norm = normalize_url(loc)
                                self.sitemap_discovered_urls.add(loc_norm)
                                if self._should_crawl(loc_norm):
                                    self.queue.append((loc_norm, 1))
                except Exception as e:
                    logger.debug("Failed checking sitemap URL %s: %s", s_url, e)

        except Exception as e:
            logger.debug("Failed initializing crawler config: %s", e)
        finally:
            await crawler.close()

    def _should_crawl(self, url: str) -> bool:
        """Verify if URL belongs to the same domain and is allowed by robots.txt."""
        parsed = urlparse(url)
        # Verify domain
        if get_clean_domain(parsed.netloc) != get_clean_domain(self.parsed_base.netloc):
            return False

        # Verify visited
        if url in self.visited or any(q[0] == url for q in self.queue):
            return False

        # Verify robots.txt
        if not self.ignore_robots and self.robots_txt_content:
            if not self.rp.can_fetch(USER_AGENT, url):
                logger.warning("URL blocked by robots.txt: %s", url)
                return False

        return True

    async def crawl(self) -> dict[str, Page]:
        """
        Execute recursive crawler queue BFS loop.
        Returns a mapping of URL to crawled Page.
        """
        await self.initialize()

        if self.sitemap_only and not self.queue:
            logger.warning("Sitemap-only mode requested but no sitemap URLs discovered. Falling back to base URL.")
            self.queue.append((self.base_url, 0))

        if self.use_playwright:
            try:
                from playwright.async_api import async_playwright
                crawler = PlaywrightCrawler()
            except ImportError:
                logger.warning("Playwright is not installed. Falling back to HTTP crawler (non-JS mode).")
                print("\n⚠️  Playwright is not installed. Falling back to HTTP crawler (non-JS mode).\n")
                crawler = HttpCrawler()
        else:
            crawler = HttpCrawler()
        
        try:
            while self.queue:
                if self.max_pages > 0 and len(self.visited) >= self.max_pages:
                    break

                current_url, depth = self.queue.pop(0)

                if current_url in self.visited:
                    continue

                if depth > self.max_depth:
                    continue

                try:
                    page = await crawler.fetch(current_url)
                    page.robots_txt = self.robots_txt_content
                    page.sitemap_urls = self.sitemap_urls
                    self.visited[current_url] = page

                    # Extract new links for queue
                    if not self.sitemap_only and depth < self.max_depth:
                        for link in page.internal_links:
                            norm_link = normalize_url(link.href)
                            if self._should_crawl(norm_link):
                                self.queue.append((norm_link, depth + 1))

                except Exception as e:
                    logger.error("Failed to crawl %s: %s", current_url, e)

        finally:
            await crawler.close()

        return self.visited
