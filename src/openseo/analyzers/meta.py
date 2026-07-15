"""
Meta description analyzer.
"""

from __future__ import annotations

from openseo.constants import (
    META_DESC_MAX_LENGTH,
    META_DESC_MIN_LENGTH,
)
from openseo.models.issue import Category, Issue, Severity
from openseo.models.page import Page


def analyze_meta(page: Page) -> tuple[list[Issue], float]:
    """
    Analyze meta description and other meta tags.

    Returns:
        Tuple of (issues list, score 0-100)
    """
    issues: list[Issue] = []
    score = 100.0

    desc = page.meta_description

    # ── Meta Description ─────────────────────────────────────────────────────
    if not desc:
        issues.append(
            Issue(
                id="meta_desc_missing",
                title="Missing Meta Description",
                description=(
                    "The page has no meta description. While not a direct ranking factor, "
                    "it significantly affects click-through rates in search results."
                ),
                severity=Severity.WARNING,
                category=Category.META,
                recommendation=f"Add a compelling meta description between {META_DESC_MIN_LENGTH}-{META_DESC_MAX_LENGTH} characters.",
            )
        )
        score -= 25
    else:
        length = len(desc)
        if length < META_DESC_MIN_LENGTH:
            issues.append(
                Issue(
                    id="meta_desc_too_short",
                    title="Meta Description Too Short",
                    description=f"Meta description is {length} chars (minimum {META_DESC_MIN_LENGTH}).",
                    severity=Severity.WARNING,
                    category=Category.META,
                    element=desc,
                    recommendation=f"Expand to at least {META_DESC_MIN_LENGTH} characters.",
                )
            )
            score -= 15
        elif length > META_DESC_MAX_LENGTH:
            issues.append(
                Issue(
                    id="meta_desc_too_long",
                    title="Meta Description Too Long",
                    description=(
                        f"Meta description is {length} chars (max {META_DESC_MAX_LENGTH}). "
                        "It will be truncated in search results."
                    ),
                    severity=Severity.WARNING,
                    category=Category.META,
                    element=desc,
                    recommendation=f"Shorten to under {META_DESC_MAX_LENGTH} characters.",
                )
            )
            score -= 10
        else:
            issues.append(
                Issue(
                    id="meta_desc_ok",
                    title="Meta Description Length is Optimal",
                    description=f"Meta description is {length} characters (ideal: {META_DESC_MIN_LENGTH}-{META_DESC_MAX_LENGTH}).",
                    severity=Severity.PASS,
                    category=Category.META,
                )
            )

    # ── Viewport ─────────────────────────────────────────────────────────────
    if not page.viewport:
        issues.append(
            Issue(
                id="viewport_missing",
                title="Missing Viewport Meta Tag",
                description="No viewport meta tag found. This affects mobile rendering.",
                severity=Severity.WARNING,
                category=Category.MOBILE,
                recommendation='Add: <meta name="viewport" content="width=device-width, initial-scale=1">',
            )
        )
        score -= 10
    else:
        issues.append(
            Issue(
                id="viewport_ok",
                title="Viewport Meta Tag Present",
                description="Viewport meta tag is configured.",
                severity=Severity.PASS,
                category=Category.MOBILE,
            )
        )

    # ── Open Graph ───────────────────────────────────────────────────────────
    og = page.open_graph
    if not og.title and not og.description:
        issues.append(
            Issue(
                id="og_missing",
                title="Missing Open Graph Tags",
                description="No Open Graph tags found. Social sharing will use defaults.",
                severity=Severity.INFO,
                category=Category.META,
                recommendation="Add og:title, og:description, og:image, og:url tags.",
            )
        )
        score -= 5
    else:
        issues.append(
            Issue(
                id="og_present",
                title="Open Graph Tags Present",
                description="Open Graph metadata is configured for social sharing.",
                severity=Severity.PASS,
                category=Category.META,
            )
        )

    return issues, max(0.0, score)


__all__ = ["analyze_meta"]
