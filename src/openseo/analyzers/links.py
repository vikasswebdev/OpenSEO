"""
Link structure analyzer.
"""

from __future__ import annotations

from openseo.models.issue import Category, Issue, Severity
from openseo.models.page import Page


def analyze_links(page: Page) -> tuple[list[Issue], float]:
    """
    Analyze internal and external link structure.

    Returns:
        Tuple of (issues list, score 0-100)
    """
    issues: list[Issue] = []
    score = 100.0

    internal = page.internal_links
    external = page.external_links

    # ── Internal Links ────────────────────────────────────────────────────────
    if len(internal) == 0:
        issues.append(
            Issue(
                id="no_internal_links",
                title="No Internal Links Found",
                description="Page has no internal links, which limits crawlability and PageRank flow.",
                severity=Severity.WARNING,
                category=Category.LINKS,
                recommendation="Add relevant internal links to other pages on your site.",
            )
        )
        score -= 15
    else:
        issues.append(
            Issue(
                id="internal_links_ok",
                title=f"{len(internal)} Internal Links",
                description=f"Page has {len(internal)} internal links.",
                severity=Severity.PASS,
                category=Category.LINKS,
            )
        )

    # ── Links Without Anchor Text ─────────────────────────────────────────────
    empty_anchor = [l for l in page.links if not l.text or l.text.strip() in ("", "click here", "read more", "here")]
    if empty_anchor:
        issues.append(
            Issue(
                id="links_empty_anchor",
                title=f"{len(empty_anchor)} Links With Poor Anchor Text",
                description="Links using generic anchor text like 'click here' miss keyword opportunities.",
                severity=Severity.INFO,
                category=Category.LINKS,
                recommendation="Use descriptive, keyword-rich anchor text for links.",
            )
        )
        score -= 5

    # ── Nofollow External Links ───────────────────────────────────────────────
    nofollow_external = [l for l in external if l.is_nofollow]
    dofollow_external = [l for l in external if not l.is_nofollow]
    if dofollow_external and len(dofollow_external) > 10:
        issues.append(
            Issue(
                id="many_external_dofollow",
                title=f"{len(dofollow_external)} External Dofollow Links",
                description="Many outbound dofollow links may dilute PageRank.",
                severity=Severity.INFO,
                category=Category.LINKS,
                recommendation="Consider nofollow for low-value external links.",
            )
        )

    return issues, max(0.0, score)


__all__ = ["analyze_links"]
