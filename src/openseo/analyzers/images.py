"""
Image SEO analyzer.
"""

from __future__ import annotations

from openseo.models.issue import Category, Issue, Severity
from openseo.models.page import Page


def analyze_images(page: Page) -> tuple[list[Issue], float]:
    """
    Analyze image SEO: alt text, lazy loading, dimensions.

    Returns:
        Tuple of (issues list, score 0-100)
    """
    issues: list[Issue] = []
    score = 100.0

    images = page.images
    if not images:
        return issues, score

    missing_alt = page.images_without_alt
    missing_alt_count = len(missing_alt)
    total = len(images)

    if missing_alt_count > 0:
        severity = Severity.CRITICAL if missing_alt_count > total * 0.5 else Severity.WARNING
        issues.append(
            Issue(
                id="images_missing_alt",
                title=f"Images Missing Alt Text ({missing_alt_count}/{total})",
                description=(
                    f"{missing_alt_count} of {total} images are missing alt attributes. "
                    "Alt text is critical for accessibility and image SEO."
                ),
                severity=severity,
                category=Category.IMAGES,
                recommendation="Add descriptive alt text to all meaningful images.",
            )
        )
        score -= min(40, missing_alt_count * 5)
    else:
        issues.append(
            Issue(
                id="images_alt_ok",
                title="All Images Have Alt Text",
                description=f"All {total} images have alt attributes.",
                severity=Severity.PASS,
                category=Category.IMAGES,
            )
        )

    # Check lazy loading
    no_lazy = [img for img in images if img.loading != "lazy"]
    if len(no_lazy) > 3:
        issues.append(
            Issue(
                id="images_no_lazy_loading",
                title="Images Not Using Lazy Loading",
                description=f"{len(no_lazy)} images don't use lazy loading.",
                severity=Severity.INFO,
                category=Category.IMAGES,
                recommendation='Add loading="lazy" to below-the-fold images.',
            )
        )
        score -= 5

    return issues, max(0.0, score)


__all__ = ["analyze_images"]
