"""
Markdown renderer — outputs Markdown-formatted results.
"""

from __future__ import annotations

from typing import Any

from openseo.models.issue import Severity
from openseo.outputs.base import BaseRenderer


class MarkdownRenderer(BaseRenderer):
    """Renders SEO results as Markdown documents."""

    def render_audit(self, result: Any) -> None:
        """Render audit result as Markdown."""
        lines = [
            f"# SEO Audit: {result.url}",
            f"",
            f"**Score:** {result.score:.0f}/100 (Grade: {result.grade})",
            f"**Provider:** {result.provider_used or '—'} / {result.model_used or '—'}",
            f"",
            f"---",
            f"",
            f"## Issues",
            f"",
        ]

        for issue in result.issues:
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵", "pass": "🟢"}.get(
                issue.severity.value, "•"
            )
            lines.append(f"### {icon} {issue.title}")
            lines.append(f"")
            lines.append(f"{issue.description}")
            if issue.recommendation:
                lines.append(f"")
                lines.append(f"**Recommendation:** {issue.recommendation}")
            lines.append(f"")

        if result.recommendations:
            lines.append(f"## LLM Recommendations")
            lines.append(f"")
            for i, rec in enumerate(result.recommendations, 1):
                lines.append(f"### {i}. {rec.title}")
                lines.append(f"")
                lines.append(f"{rec.body}")
                lines.append(f"")
                lines.append(f"- **Priority:** {rec.priority}")
                lines.append(f"- **Impact:** {rec.impact}")
                lines.append(f"- **Effort:** {rec.effort}")
                lines.append(f"")

        print("\n".join(lines))

    def render_keywords(self, result: Any) -> None:
        """Render keyword results as Markdown."""
        lines = [
            f"# Keyword Research: {result.topic or result.url or ''}",
            f"",
            f"## Primary Keywords",
            f"",
        ]
        for kw in result.primary_keywords:
            lines.append(f"- {kw}")
        lines.append(f"")
        lines.append(f"## Long-Tail Keywords")
        lines.append(f"")
        for kw in result.long_tail_keywords:
            lines.append(f"- {kw}")

        print("\n".join(lines))

    def render_error(self, message: str, hint: str | None = None) -> None:
        print(f"> ❌ **Error:** {message}")
        if hint:
            print(f"> 💡 *{hint}*")

    def render_success(self, message: str) -> None:
        print(f"✅ {message}")

    def render_info(self, message: str) -> None:
        print(f"ℹ️ {message}")


__all__ = ["MarkdownRenderer"]
