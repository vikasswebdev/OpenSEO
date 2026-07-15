"""Models package — all Pydantic data models for OpenSEO."""

from openseo.models.issue import Category, Issue, Recommendation, Severity
from openseo.models.page import (
    HeadingNode,
    ImageData,
    LinkData,
    OpenGraphData,
    Page,
    SchemaOrgItem,
    TwitterCardData,
)
from openseo.models.result import AuditResult, ContentResult, KeywordResult, SchemaResult
from openseo.models.site import DuplicateCluster, LinkNode, SiteAuditResult

__all__ = [
    "Category",
    "Issue",
    "Recommendation",
    "Severity",
    "HeadingNode",
    "ImageData",
    "LinkData",
    "OpenGraphData",
    "Page",
    "SchemaOrgItem",
    "TwitterCardData",
    "AuditResult",
    "ContentResult",
    "KeywordResult",
    "SchemaResult",
    "DuplicateCluster",
    "LinkNode",
    "SiteAuditResult",
]
