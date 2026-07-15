"""
Pydantic models representing site-wide audit results, internal linking structures,
and duplicate content clusters.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Any

from openseo.models.result import AuditResult, ScoreBreakdown
from openseo.models.issue import Issue, Recommendation


class LinkNode(BaseModel):
    """A node in the internal link graph representing page connectivity."""

    url: str = Field(..., description="The page URL")
    in_links: list[str] = Field(default_factory=list, description="URLs linking to this page")
    out_links: list[str] = Field(default_factory=list, description="URLs this page links to")
    anchor_texts: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Map of source URL to lists of anchor texts used for this page"
    )

    @property
    def is_orphan(self) -> bool:
        """Orphan pages have 0 incoming internal links."""
        return len(self.in_links) == 0


class DuplicateCluster(BaseModel):
    """A cluster of pages identified as having duplicate content."""

    content_hash: str = Field(..., description="Hash of the page body content")
    urls: list[str] = Field(..., description="URLs sharing this content hash")
    strategy: str | None = Field(
        None,
        description="AI recommended strategy: merge, redirect, rewrite, canonicalize, keep_separate"
    )
    explanation: str | None = Field(None, description="Reasoning for the recommended action")


class SiteAuditResult(BaseModel):
    """
    Complete representation of a site-wide SEO audit.

    Aggregates page-level results, link graph calculations, duplicate clusters,
    and site-level AI recommendations.
    """

    url: str = Field(..., description="Target site base URL")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the site audit was run"
    )
    duration_ms: float = Field(0.0, description="Total crawl and analysis time in ms")

    # Raw / Page Audits
    pages: dict[str, AuditResult] = Field(
        default_factory=dict,
        description="Map of page URL to its individual page audit result"
    )

    # Site-level structures
    link_graph: dict[str, LinkNode] = Field(
        default_factory=dict,
        description="Internal linking graph represented as a map of URL to LinkNode"
    )
    duplicate_clusters: list[DuplicateCluster] = Field(
        default_factory=list,
        description="Identified clusters of duplicate pages"
    )

    # Site-level scoring
    score: float = Field(0.0, ge=0.0, le=100.0, description="Overall site SEO score")
    score_breakdown: ScoreBreakdown = Field(
        default_factory=ScoreBreakdown,
        description="Average breakdown scores across all pages"
    )

    # Global issues & strategic recommendations
    site_issues: list[Issue] = Field(
        default_factory=list,
        description="Deterministic site-wide issues (e.g., missing sitemap/robots.txt)"
    )
    site_recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="AI-generated site-wide recommendations and strategic roadmap"
    )
    sitemap_discovered_urls: list[str] = Field(
        default_factory=list,
        description="All discovered URLs inside the XML sitemaps"
    )

    # Provider metadata
    provider_used: str | None = None
    model_used: str | None = None

    @property
    def total_pages(self) -> int:
        """Total number of crawled pages."""
        return len(self.pages)

    @property
    def orphan_pages(self) -> list[str]:
        """List of orphan page URLs."""
        return [url for url, node in self.link_graph.items() if node.is_orphan]
