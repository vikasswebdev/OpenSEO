"""
Content quality analyzer.
"""

from __future__ import annotations

from openseo.models.issue import Category, Issue, Severity
from openseo.models.page import Page

MINIMUM_WORD_COUNT = 300
GOOD_WORD_COUNT = 800


def analyze_content(page: Page) -> tuple[list[Issue], float]:
    """
    Analyze content quality and depth.

    Returns:
        Tuple of (issues list, score 0-100)
    """
    issues: list[Issue] = []
    score = 100.0

    word_count = page.word_count

    if word_count < MINIMUM_WORD_COUNT:
        issues.append(
            Issue(
                id="content_thin",
                title=f"Thin Content ({word_count} words)",
                description=(
                    f"Page has only {word_count} words. Google may consider this thin content "
                    f"and rank it lower. Aim for at least {MINIMUM_WORD_COUNT} words."
                ),
                severity=Severity.WARNING,
                category=Category.CONTENT,
                recommendation=f"Expand content to at least {MINIMUM_WORD_COUNT} words with valuable information.",
            )
        )
        score -= 25
    elif word_count < GOOD_WORD_COUNT:
        issues.append(
            Issue(
                id="content_adequate",
                title=f"Adequate Content ({word_count} words)",
                description=f"Content meets minimum threshold. Consider expanding to {GOOD_WORD_COUNT}+ words.",
                severity=Severity.INFO,
                category=Category.CONTENT,
            )
        )
    else:
        issues.append(
            Issue(
                id="content_good",
                title=f"Good Content Depth ({word_count} words)",
                description=f"Page has {word_count} words — good for comprehensive coverage.",
                severity=Severity.PASS,
                category=Category.CONTENT,
            )
        )

    # Canonical check
    if not page.canonical:
        issues.append(
            Issue(
                id="canonical_missing",
                title="Missing Canonical URL",
                description="No canonical URL specified. This can cause duplicate content issues.",
                severity=Severity.WARNING,
                category=Category.TECHNICAL,
                recommendation="Add <link rel='canonical' href='...'> to prevent duplicate content.",
            )
        )
        score -= 10

    return issues, max(0.0, score)


__all__ = ["analyze_content"]
