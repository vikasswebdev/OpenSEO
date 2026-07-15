"""
Pydantic models for SEO issues and recommendations.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity level of an SEO issue."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    PASS = "pass"


class Category(str, Enum):
    """Category of an SEO issue."""

    TITLE = "title"
    META = "meta"
    HEADINGS = "headings"
    IMAGES = "images"
    LINKS = "links"
    SCHEMA = "schema"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    CONTENT = "content"
    TECHNICAL = "technical"
    SECURITY = "security"
    MOBILE = "mobile"


class Issue(BaseModel):
    """A single SEO issue detected during analysis."""

    model_config = {"frozen": True}

    id: str = Field(..., description="Unique identifier for this issue type")
    title: str = Field(..., description="Short human-readable title")
    description: str = Field(..., description="Detailed description of the issue")
    severity: Severity = Field(..., description="How critical this issue is")
    category: Category = Field(..., description="SEO category this issue belongs to")
    element: str | None = Field(None, description="The specific HTML element or value")
    recommendation: str | None = Field(None, description="Suggested fix")
    documentation_url: str | None = Field(None, description="Link to documentation")

    @property
    def is_critical(self) -> bool:
        """Return True if this issue is critical."""
        return self.severity == Severity.CRITICAL

    @property
    def is_passing(self) -> bool:
        """Return True if this is a passing check."""
        return self.severity == Severity.PASS


class Recommendation(BaseModel):
    """A high-level SEO recommendation from an LLM analysis."""

    model_config = {"frozen": True}

    title: str = Field(..., description="Short recommendation title")
    body: str = Field(..., description="Detailed recommendation text")
    priority: int = Field(..., ge=1, le=5, description="Priority from 1 (highest) to 5")
    category: Category = Field(..., description="SEO category")
    effort: str = Field("medium", description="Effort level: low, medium, high")
    impact: str = Field("medium", description="Expected impact: low, medium, high")


__all__ = ["Severity", "Category", "Issue", "Recommendation"]
