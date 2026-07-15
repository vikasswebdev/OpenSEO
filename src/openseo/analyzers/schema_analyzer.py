"""
Schema.org structured data analyzer.
"""

from __future__ import annotations

from openseo.models.issue import Category, Issue, Severity
from openseo.models.page import Page


def analyze_schema(page: Page) -> tuple[list[Issue], float]:
    """
    Analyze schema.org / JSON-LD structured data.

    Returns:
        Tuple of (issues list, score 0-100)
    """
    issues: list[Issue] = []
    score = 100.0

    schemas = page.schema_org

    if not schemas:
        issues.append(
            Issue(
                id="schema_missing",
                title="No Schema.org Structured Data",
                description=(
                    "No JSON-LD structured data found. Schema markup helps search engines "
                    "understand your content and enables rich results."
                ),
                severity=Severity.WARNING,
                category=Category.SCHEMA,
                recommendation="Add appropriate schema.org markup (e.g., Article, Product, FAQ, LocalBusiness).",
            )
        )
        score -= 20
    else:
        schema_types = [s.type for s in schemas if s.type]
        issues.append(
            Issue(
                id="schema_present",
                title=f"Schema.org Markup Found ({len(schemas)} types)",
                description=f"Found schema types: {', '.join(schema_types) or 'Unknown'}",
                severity=Severity.PASS,
                category=Category.SCHEMA,
            )
        )

    return issues, max(0.0, score)


__all__ = ["analyze_schema"]
