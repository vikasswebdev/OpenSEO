"""
Pydantic models representing a crawled web page and its extracted data.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class HeadingNode(BaseModel):
    """A single heading element."""

    model_config = {"frozen": True}

    level: int = Field(..., ge=1, le=6, description="Heading level (1-6)")
    text: str = Field(..., description="Heading text content")


class ImageData(BaseModel):
    """Metadata for a single image."""

    model_config = {"frozen": True}

    src: str = Field(..., description="Image source URL or path")
    alt: str | None = Field(None, description="Alt attribute value")
    title: str | None = Field(None, description="Title attribute value")
    width: int | None = Field(None, description="Image width in pixels")
    height: int | None = Field(None, description="Image height in pixels")
    loading: str | None = Field(None, description="Loading attribute (lazy/eager)")


class LinkData(BaseModel):
    """Metadata for a single link."""

    model_config = {"frozen": True}

    href: str = Field(..., description="Link href value")
    text: str | None = Field(None, description="Anchor text")
    rel: str | None = Field(None, description="Rel attribute value")
    is_external: bool = Field(False, description="Whether this is an external link")
    is_nofollow: bool = Field(False, description="Whether nofollow is set")


class OpenGraphData(BaseModel):
    """Open Graph protocol metadata."""

    title: str | None = None
    description: str | None = None
    image: str | None = None
    url: str | None = None
    type: str | None = None
    site_name: str | None = None


class TwitterCardData(BaseModel):
    """Twitter Card metadata."""

    card: str | None = None
    site: str | None = None
    title: str | None = None
    description: str | None = None
    image: str | None = None


class SchemaOrgItem(BaseModel):
    """A single JSON-LD schema.org item."""

    type: str | None = Field(None, alias="@type")
    raw: dict = Field(default_factory=dict, description="Full raw schema object")


class Page(BaseModel):
    """
    Complete representation of a crawled web page.

    This is the central data object that flows through the analysis pipeline.
    """

    # Identity
    url: str = Field(..., description="Canonical URL that was crawled")
    final_url: str | None = Field(None, description="Final URL after redirects")
    status_code: int | None = Field(None, description="HTTP response status code")

    # Content basics
    title: str | None = Field(None, description="<title> tag content")
    meta_description: str | None = Field(None, description="meta[name=description] content")
    meta_keywords: str | None = Field(None, description="meta[name=keywords] content")
    canonical: str | None = Field(None, description="<link rel=canonical> href")
    lang: str | None = Field(None, description="<html lang> attribute")

    # Headings
    headings: list[HeadingNode] = Field(default_factory=list)

    # Media & Links
    images: list[ImageData] = Field(default_factory=list)
    links: list[LinkData] = Field(default_factory=list)

    # Structured data
    open_graph: OpenGraphData = Field(default_factory=OpenGraphData)
    twitter_card: TwitterCardData = Field(default_factory=TwitterCardData)
    schema_org: list[SchemaOrgItem] = Field(default_factory=list)

    # Technical
    robots_meta: str | None = Field(None, description="meta[name=robots] content")
    viewport: str | None = Field(None, description="meta[name=viewport] content")
    charset: str | None = Field(None, description="Document charset")
    word_count: int = Field(0, description="Approximate word count of visible text")
    body_text: str = Field("", description="Extracted visible body text")

    # Sitemap / Robots
    sitemap_urls: list[str] = Field(default_factory=list)
    robots_txt: str | None = Field(None, description="robots.txt content")

    # Response metadata
    content_type: str | None = None
    response_time_ms: float | None = None
    page_size_bytes: int | None = None
    is_js_rendered: bool = Field(False, description="Whether Playwright was used")

    @property
    def h1_tags(self) -> list[str]:
        """Return all H1 heading texts."""
        return [h.text for h in self.headings if h.level == 1]

    @property
    def internal_links(self) -> list[LinkData]:
        """Return only internal links."""
        return [l for l in self.links if not l.is_external]

    @property
    def external_links(self) -> list[LinkData]:
        """Return only external links."""
        return [l for l in self.links if l.is_external]

    @property
    def images_without_alt(self) -> list[ImageData]:
        """Return images missing alt text."""
        return [img for img in self.images if not img.alt]


__all__ = [
    "HeadingNode",
    "ImageData",
    "LinkData",
    "OpenGraphData",
    "TwitterCardData",
    "SchemaOrgItem",
    "Page",
]
