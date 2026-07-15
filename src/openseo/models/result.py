"""
Pydantic models for audit results, keyword results, and content results.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from openseo.models.issue import Issue, Recommendation, Severity
from openseo.models.page import Page


class ScoreBreakdown(BaseModel):
    """SEO score breakdown by category."""

    title: float = Field(0.0, ge=0, le=100)
    meta: float = Field(0.0, ge=0, le=100)
    headings: float = Field(0.0, ge=0, le=100)
    images: float = Field(0.0, ge=0, le=100)
    links: float = Field(0.0, ge=0, le=100)
    content: float = Field(0.0, ge=0, le=100)
    schema_org: float = Field(0.0, ge=0, le=100)
    technical: float = Field(0.0, ge=0, le=100)


class AuditResult(BaseModel):
    """Complete SEO audit result for a single URL."""

    # Identity
    url: str = Field(..., description="Audited URL")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the audit was run",
    )
    duration_ms: float = Field(0.0, description="Total audit duration in milliseconds")

    # Raw page data
    page: Page = Field(..., description="Crawled page data")

    # Analysis
    issues: list[Issue] = Field(default_factory=list, description="Detected SEO issues")
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="LLM-generated recommendations"
    )
    score: float = Field(0.0, ge=0, le=100, description="Overall SEO score")
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)

    # Provider metadata
    provider_used: str | None = Field(None, description="LLM provider used")
    model_used: str | None = Field(None, description="LLM model used")

    @property
    def critical_issues(self) -> list[Issue]:
        """Return only critical issues."""
        return [i for i in self.issues if i.severity == Severity.CRITICAL]

    @property
    def warnings(self) -> list[Issue]:
        """Return only warning-level issues."""
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def passed_checks(self) -> list[Issue]:
        """Return passing checks."""
        return [i for i in self.issues if i.severity == Severity.PASS]

    @property
    def grade(self) -> str:
        """Return a letter grade based on score."""
        if self.score >= 90:
            return "A"
        if self.score >= 80:
            return "B"
        if self.score >= 70:
            return "C"
        if self.score >= 60:
            return "D"
        return "F"


class KeywordResult(BaseModel):
    """Result of keyword analysis or generation."""

    url: str | None = Field(None, description="Source URL if applicable")
    topic: str | None = Field(None, description="Topic if provided")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    primary_keywords: list[str] = Field(default_factory=list)
    long_tail_keywords: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    related_topics: list[str] = Field(default_factory=list)

    provider_used: str | None = None
    model_used: str | None = None


class ContentResult(BaseModel):
    """Result of content analysis."""

    url: str = Field(..., description="Analyzed URL")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    word_count: int = Field(0)
    readability_score: float | None = Field(None, ge=0, le=100)
    sentiment: str | None = None
    tone: str | None = None
    suggestions: list[str] = Field(default_factory=list)
    optimized_content: str | None = None

    provider_used: str | None = None
    model_used: str | None = None


class SchemaResult(BaseModel):
    """Result of schema.org analysis."""

    url: str = Field(..., description="Analyzed URL")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    existing_schemas: list[str] = Field(default_factory=list, description="Found schema types")
    issues: list[Issue] = Field(default_factory=list)
    generated_schema: str | None = Field(None, description="LLM-generated schema JSON-LD")
    schema_type: str | None = Field(None, description="Recommended schema type")

    provider_used: str | None = None
    model_used: str | None = None


__all__ = [
    "ScoreBreakdown",
    "AuditResult",
    "KeywordResult",
    "ContentResult",
    "SchemaResult",
]
