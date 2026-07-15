"""
Title tag analyzer.
"""

from __future__ import annotations

from openseo.constants import (
    SEVERITY_CRITICAL,
    SEVERITY_INFO,
    SEVERITY_PASS,
    SEVERITY_WARNING,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
)
from openseo.models.issue import Category, Issue, Severity
from openseo.models.page import Page


def analyze_title(page: Page) -> tuple[list[Issue], float]:
    """
    Analyze the page title tag.

    Returns:
        Tuple of (issues list, score 0-100)
    """
    issues: list[Issue] = []
    score = 100.0

    title = page.title

    if not title:
        issues.append(
            Issue(
                id="title_missing",
                title="Missing Title Tag",
                description="The page has no <title> tag. This is a critical SEO issue.",
                severity=Severity.CRITICAL,
                category=Category.TITLE,
                recommendation="Add a descriptive <title> tag between 50-60 characters.",
            )
        )
        return issues, 0.0

    length = len(title)

    if length < TITLE_MIN_LENGTH:
        issues.append(
            Issue(
                id="title_too_short",
                title="Title Too Short",
                description=f"Title is {length} characters (minimum {TITLE_MIN_LENGTH}).",
                severity=Severity.WARNING,
                category=Category.TITLE,
                element=title,
                recommendation=f"Expand the title to at least {TITLE_MIN_LENGTH} characters.",
            )
        )
        score -= 20

    elif length > TITLE_MAX_LENGTH:
        issues.append(
            Issue(
                id="title_too_long",
                title="Title Too Long",
                description=(
                    f"Title is {length} characters (maximum {TITLE_MAX_LENGTH}). "
                    "Search engines will truncate it."
                ),
                severity=Severity.WARNING,
                category=Category.TITLE,
                element=title,
                recommendation=f"Shorten the title to under {TITLE_MAX_LENGTH} characters.",
            )
        )
        score -= 15
    else:
        issues.append(
            Issue(
                id="title_length_ok",
                title="Title Length is Optimal",
                description=f"Title is {length} characters (ideal: {TITLE_MIN_LENGTH}-{TITLE_MAX_LENGTH}).",
                severity=Severity.PASS,
                category=Category.TITLE,
                element=title,
            )
        )

    # Check for keyword stuffing (very simplistic heuristic)
    if title.count("|") + title.count("-") + title.count(":") > 3:
        issues.append(
            Issue(
                id="title_separator_overuse",
                title="Excessive Title Separators",
                description="Title contains many separators, which may indicate keyword stuffing.",
                severity=Severity.INFO,
                category=Category.TITLE,
                element=title,
                recommendation="Use separators sparingly. One or two is fine.",
            )
        )
        score -= 5

    return issues, max(0.0, score)


__all__ = ["analyze_title"]
