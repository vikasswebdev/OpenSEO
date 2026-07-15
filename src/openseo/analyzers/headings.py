"""
Heading structure analyzer.
"""

from __future__ import annotations

from openseo.constants import H1_IDEAL_COUNT
from openseo.models.issue import Category, Issue, Severity
from openseo.models.page import Page


def analyze_headings(page: Page) -> tuple[list[Issue], float]:
    """
    Analyze heading structure (H1-H6).

    Returns:
        Tuple of (issues list, score 0-100)
    """
    issues: list[Issue] = []
    score = 100.0

    h1_count = len(page.h1_tags)

    # ── H1 Checks ────────────────────────────────────────────────────────────
    if h1_count == 0:
        issues.append(
            Issue(
                id="h1_missing",
                title="Missing H1 Tag",
                description="The page has no H1 heading. This is a significant SEO issue.",
                severity=Severity.CRITICAL,
                category=Category.HEADINGS,
                recommendation="Add exactly one H1 tag that includes your primary keyword.",
            )
        )
        score -= 30
    elif h1_count > H1_IDEAL_COUNT:
        issues.append(
            Issue(
                id="h1_multiple",
                title=f"Multiple H1 Tags ({h1_count})",
                description=(
                    f"Found {h1_count} H1 tags. Best practice is exactly one H1 per page."
                ),
                severity=Severity.WARNING,
                category=Category.HEADINGS,
                element=", ".join(page.h1_tags[:3]),
                recommendation="Use only one H1 tag. Use H2-H6 for subheadings.",
            )
        )
        score -= 15
    else:
        issues.append(
            Issue(
                id="h1_ok",
                title="Single H1 Tag",
                description=f"Page has exactly one H1 tag: '{page.h1_tags[0][:60]}'",
                severity=Severity.PASS,
                category=Category.HEADINGS,
                element=page.h1_tags[0],
            )
        )

    # ── Heading Hierarchy ─────────────────────────────────────────────────────
    levels = [h.level for h in page.headings]
    if levels:
        # Check for skipped heading levels
        prev_level = 1
        skips_detected = False
        for level in levels:
            if level > prev_level + 1:
                skips_detected = True
                break
            prev_level = level

        if skips_detected:
            issues.append(
                Issue(
                    id="heading_hierarchy_skip",
                    title="Skipped Heading Levels",
                    description="Heading levels are skipped (e.g., H1 → H3), which harms accessibility.",
                    severity=Severity.INFO,
                    category=Category.HEADINGS,
                    recommendation="Maintain sequential heading hierarchy: H1 → H2 → H3.",
                )
            )
            score -= 5

    total_headings = len(page.headings)
    if total_headings == 0:
        issues.append(
            Issue(
                id="headings_none",
                title="No Headings Found",
                description="Page has no heading tags at all.",
                severity=Severity.CRITICAL,
                category=Category.HEADINGS,
                recommendation="Structure your content with proper heading tags.",
            )
        )
        score = 0.0

    return issues, max(0.0, score)


__all__ = ["analyze_headings"]
