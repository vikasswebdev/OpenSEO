"""
HTML data extractor using BeautifulSoup4.

Extracts all SEO-relevant data from an HTML document into a Page model.
"""

from __future__ import annotations

import json
import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from openseo.models.page import (
    HeadingNode,
    ImageData,
    LinkData,
    OpenGraphData,
    Page,
    SchemaOrgItem,
    TwitterCardData,
)

logger = logging.getLogger(__name__)


class PageExtractor:
    """
    Extracts SEO data from raw HTML using BeautifulSoup4.

    Responsible for parsing and structuring all page metadata,
    content, and structured data from a raw HTML string.
    """

    def __init__(self, base_url: str, html: str) -> None:
        self._base_url = base_url
        self._base_domain = urlparse(base_url).netloc
        self._soup = BeautifulSoup(html, "lxml")

    def extract(self) -> dict:
        """
        Run all extractors and return a dict of Page kwargs.

        Returns a dictionary suitable for constructing a Page model.
        """
        return {
            "title": self._extract_title(),
            "meta_description": self._extract_meta("description"),
            "meta_keywords": self._extract_meta("keywords"),
            "canonical": self._extract_canonical(),
            "lang": self._extract_lang(),
            "headings": self._extract_headings(),
            "images": self._extract_images(),
            "links": self._extract_links(),
            "open_graph": self._extract_open_graph(),
            "twitter_card": self._extract_twitter_card(),
            "schema_org": self._extract_schema_org(),
            "robots_meta": self._extract_meta("robots"),
            "viewport": self._extract_meta("viewport"),
            "charset": self._extract_charset(),
            "body_text": self._extract_body_text(),
            "word_count": self._count_words(),
        }

    def _extract_title(self) -> str | None:
        tag = self._soup.find("title")
        if tag and isinstance(tag, Tag):
            return tag.get_text(strip=True) or None
        return None

    def _extract_meta(self, name: str) -> str | None:
        tag = self._soup.find("meta", attrs={"name": re.compile(name, re.I)})
        if tag and isinstance(tag, Tag):
            return tag.get("content") or None  # type: ignore[return-value]
        return None

    def _extract_canonical(self) -> str | None:
        tag = self._soup.find("link", rel=lambda v: v and "canonical" in v)
        if tag and isinstance(tag, Tag):
            href = tag.get("href")
            return str(href) if href else None
        return None

    def _extract_lang(self) -> str | None:
        html_tag = self._soup.find("html")
        if html_tag and isinstance(html_tag, Tag):
            lang = html_tag.get("lang")
            return str(lang) if lang else None
        return None

    def _extract_headings(self) -> list[HeadingNode]:
        headings = []
        for level in range(1, 7):
            for tag in self._soup.find_all(f"h{level}"):
                text = tag.get_text(strip=True)
                if text:
                    headings.append(HeadingNode(level=level, text=text))
        return headings

    def _extract_images(self) -> list[ImageData]:
        images = []
        for img in self._soup.find_all("img"):
            if not isinstance(img, Tag):
                continue
            src = img.get("src", "")
            if not src:
                continue
            images.append(
                ImageData(
                    src=urljoin(self._base_url, str(src)),
                    alt=img.get("alt") or None,  # type: ignore[arg-type]
                    title=img.get("title") or None,  # type: ignore[arg-type]
                    width=int(img["width"]) if img.get("width", "").isdigit() else None,  # type: ignore[union-attr]
                    height=int(img["height"]) if img.get("height", "").isdigit() else None,  # type: ignore[union-attr]
                    loading=img.get("loading") or None,  # type: ignore[arg-type]
                )
            )
        return images

    def _extract_links(self) -> list[LinkData]:
        links = []
        for a in self._soup.find_all("a", href=True):
            if not isinstance(a, Tag):
                continue
            href = str(a.get("href", ""))
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            full_url = urljoin(self._base_url, href)
            parsed = urlparse(full_url)
            is_external = parsed.netloc != self._base_domain and bool(parsed.netloc)
            rel = a.get("rel")
            rel_str = " ".join(rel) if isinstance(rel, list) else str(rel) if rel else None
            links.append(
                LinkData(
                    href=full_url,
                    text=a.get_text(strip=True) or None,
                    rel=rel_str,
                    is_external=is_external,
                    is_nofollow="nofollow" in (rel_str or ""),
                )
            )
        return links

    def _extract_open_graph(self) -> OpenGraphData:
        def og(prop: str) -> str | None:
            tag = self._soup.find("meta", property=f"og:{prop}")
            if tag and isinstance(tag, Tag):
                return tag.get("content") or None  # type: ignore[return-value]
            return None

        return OpenGraphData(
            title=og("title"),
            description=og("description"),
            image=og("image"),
            url=og("url"),
            type=og("type"),
            site_name=og("site_name"),
        )

    def _extract_twitter_card(self) -> TwitterCardData:
        def tw(name: str) -> str | None:
            tag = self._soup.find("meta", attrs={"name": f"twitter:{name}"})
            if tag and isinstance(tag, Tag):
                return tag.get("content") or None  # type: ignore[return-value]
            return None

        return TwitterCardData(
            card=tw("card"),
            site=tw("site"),
            title=tw("title"),
            description=tw("description"),
            image=tw("image"),
        )

    def _extract_schema_org(self) -> list[SchemaOrgItem]:
        schemas = []
        for script in self._soup.find_all("script", type="application/ld+json"):
            if not isinstance(script, Tag):
                continue
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    schemas.append(
                        SchemaOrgItem(
                            **{"@type": data.get("@type")},
                            raw=data,
                        )
                    )
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            schemas.append(
                                SchemaOrgItem(
                                    **{"@type": item.get("@type")},
                                    raw=item,
                                )
                            )
            except json.JSONDecodeError:
                logger.debug("Failed to parse JSON-LD script block")
        return schemas

    def _extract_charset(self) -> str | None:
        tag = self._soup.find("meta", charset=True)
        if tag and isinstance(tag, Tag):
            return str(tag.get("charset")) or None
        return None

    def _extract_body_text(self) -> str:
        """Extract visible text from the page body."""
        # Remove script and style elements
        for element in self._soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        body = self._soup.find("body") or self._soup
        text = body.get_text(separator=" ", strip=True)  # type: ignore[union-attr]
        # Collapse whitespace
        return re.sub(r"\s+", " ", text).strip()

    def _count_words(self) -> int:
        text = self._extract_body_text()
        return len(text.split()) if text else 0


__all__ = ["PageExtractor"]
