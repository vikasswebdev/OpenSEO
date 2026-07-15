"""
Terminal renderer using Rich.

Produces beautiful, colored, structured output in the terminal.
"""

from __future__ import annotations

from typing import Any

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from openseo.constants import SEVERITY_COLORS, SEVERITY_ICONS
from openseo.models.issue import Severity
from openseo.outputs.base import BaseRenderer

console = Console()
error_console = Console(stderr=True)


def _severity_style(severity: Severity) -> str:
    """Return Rich style string for a severity level."""
    return SEVERITY_COLORS.get(severity.value, "white")


def _severity_icon(severity: Severity) -> str:
    """Return icon for a severity level."""
    return SEVERITY_ICONS.get(severity.value, "•")


class TerminalRenderer(BaseRenderer):
    """
    Renders SEO results as beautiful Rich terminal output.

    Uses panels, tables, trees, and colored text for a professional look.
    """

    def __init__(self, verbose: bool = False, no_color: bool = False) -> None:
        self._verbose = verbose
        global console, error_console
        if no_color:
            console = Console(no_color=True)
            error_console = Console(stderr=True, no_color=True)

    def render_audit(self, result: Any) -> None:
        """Render a full AuditResult with panels, tables, and score."""
        from openseo.models.result import AuditResult

        if not isinstance(result, AuditResult):
            self.render_error("Invalid result type for audit renderer.")
            return

        console.print()
        self._render_header(result)
        self._render_score(result)
        self._render_issues(result)
        self._render_recommendations(result)
        self._render_page_details(result)
        console.print()

    def _render_header(self, result: Any) -> None:
        """Render the audit header panel."""
        page = result.page
        title_text = Text()
        title_text.append("🔍 SEO Audit Report\n", style="bold white")
        title_text.append(result.url, style="bright_cyan underline")

        meta = Text()
        meta.append(f"  Status: ", style="dim")
        status = page.status_code or "?"
        meta.append(str(status), style="green" if status == 200 else "red")
        if page.response_time_ms:
            meta.append(f"  •  {page.response_time_ms:.0f}ms", style="dim")
        if page.word_count:
            meta.append(f"  •  {page.word_count} words", style="dim")
        if result.provider_used:
            meta.append(f"  •  {result.provider_used}/{result.model_used}", style="dim")

        console.print(Panel(
            title_text + Text("\n") + meta,
            border_style="bright_blue",
            padding=(1, 2),
        ))

    def _render_score(self, result: Any) -> None:
        """Render the SEO score with grade."""
        score = result.score
        grade = result.grade

        if score >= 80:
            color = "bright_green"
        elif score >= 60:
            color = "yellow"
        else:
            color = "red"

        score_text = Text()
        score_text.append(f"Overall SEO Score: ", style="bold white")
        score_text.append(f"{score:.0f}/100", style=f"bold {color}")
        score_text.append(f"  Grade: ", style="bold white")
        score_text.append(f" {grade} ", style=f"bold white on {color}")

        breakdown = result.score_breakdown
        breakdown_text = Text()
        for field_name in ["title", "meta", "headings", "images", "links", "content", "schema_org"]:
            val = getattr(breakdown, field_name, 0)
            bar_color = "green" if val >= 80 else "yellow" if val >= 60 else "red"
            breakdown_text.append(f"\n  {field_name.title():12}", style="dim")
            breakdown_text.append(f" {val:3.0f}/100", style=bar_color)

        console.print(Panel(
            score_text + breakdown_text,
            title="[bold]Score",
            border_style=color,
            padding=(0, 2),
        ))

    def _render_issues(self, result: Any) -> None:
        """Render issues grouped by severity."""
        if not result.issues:
            return

        table = Table(
            title="[bold]Issues & Checks",
            box=box.ROUNDED,
            border_style="bright_blue",
            show_header=True,
            header_style="bold white",
            padding=(0, 1),
        )
        table.add_column("", width=2, no_wrap=True)
        table.add_column("Title", style="white", min_width=25)
        table.add_column("Category", style="dim", min_width=12)
        table.add_column("Description", style="dim")

        # Sort: critical first
        order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2, Severity.PASS: 3}
        sorted_issues = sorted(result.issues, key=lambda i: order.get(i.severity, 4))

        for issue in sorted_issues:
            style = _severity_style(issue.severity)
            icon = _severity_icon(issue.severity)
            desc = issue.description
            if len(desc) > 80:
                desc = desc[:77] + "..."
            table.add_row(
                Text(icon, style=f"bold {style}"),
                Text(issue.title, style=style if issue.is_critical else "white"),
                Text(issue.category.value, style="dim"),
                Text(desc, style="dim"),
            )

        console.print(table)

    def _render_recommendations(self, result: Any) -> None:
        """Render LLM-generated recommendations."""
        if not result.recommendations:
            return

        tree = Tree("[bold bright_blue]💡 Recommendations")
        for i, rec in enumerate(result.recommendations[:5], 1):
            impact_color = "green" if rec.impact == "high" else "yellow" if rec.impact == "medium" else "white"
            branch = tree.add(
                f"[bold]{i}. {rec.title}[/] "
                f"[dim](Priority {rec.priority} • Impact: [{impact_color}]{rec.impact}[/] • Effort: {rec.effort})[/]"
            )
            branch.add(Text(rec.body, style="dim"))

        console.print(Panel(tree, border_style="bright_blue", padding=(0, 1)))

    def _render_page_details(self, result: Any) -> None:
        """Render page metadata in a compact table."""
        if not self._verbose:
            return

        page = result.page
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Key", style="dim", min_width=20)
        table.add_column("Value", style="white")

        rows = [
            ("Title", page.title or "—"),
            ("Meta Description", (page.meta_description or "—")[:80]),
            ("Canonical", page.canonical or "—"),
            ("H1 Tags", ", ".join(page.h1_tags) or "—"),
            ("Images", str(len(page.images))),
            ("Internal Links", str(len(page.internal_links))),
            ("External Links", str(len(page.external_links))),
            ("Schema Types", ", ".join(s.type or "?" for s in page.schema_org) or "—"),
            ("Open Graph", "✓" if page.open_graph.title else "✗"),
        ]
        for key, val in rows:
            table.add_row(key, val)

        console.print(Panel(table, title="[bold]Page Details", border_style="dim", padding=(0, 1)))

    def render_site_audit(self, result: Any) -> None:
        """Render a comprehensive SiteAuditResult with scores, graphs, clusters, and roadmaps."""
        from openseo.models.site import SiteAuditResult
        from urllib.parse import urlparse

        if not isinstance(result, SiteAuditResult):
            self.render_error("Invalid result type for site audit renderer.")
            return

        console.print()
        # ── Site Header ───────────────────────────────────────────────────────
        title_text = Text()
        title_text.append("🌐 Site SEO Audit Report\n", style="bold white")
        title_text.append(result.url, style="bright_cyan underline")

        meta = Text()
        meta.append(f"  Pages Crawled: ", style="dim")
        meta.append(str(result.total_pages), style="green")
        meta.append(f"  •  Duration: {result.duration_ms/1000:.1f}s", style="dim")
        if result.provider_used:
            meta.append(f"  •  AI: {result.provider_used}/{result.model_used}", style="dim")
        console.print(Panel(title_text + Text("\n") + meta, border_style="bright_blue", padding=(1, 2)))

        # ── Score Panel ───────────────────────────────────────────────────────
        score = result.score
        if score >= 80:
            color = "bright_green"
            grade = "A" if score >= 90 else "B"
        elif score >= 60:
            color = "yellow"
            grade = "C" if score >= 70 else "D"
        else:
            color = "red"
            grade = "F"

        score_text = Text()
        score_text.append(f"Overall Website SEO Score: ", style="bold white")
        score_text.append(f"{score:.0f}/100", style=f"bold {color}")
        score_text.append(f"  Grade: ", style="bold white")
        score_text.append(f" {grade} ", style=f"bold white on {color}")

        breakdown = result.score_breakdown
        breakdown_text = Text()
        for field_name in ["title", "meta", "headings", "images", "links", "content", "schema_org", "technical"]:
            val = getattr(breakdown, field_name, 0)
            bar_color = "green" if val >= 80 else "yellow" if val >= 60 else "red"
            breakdown_text.append(f"\n  Average {field_name.title():12}", style="dim")
            breakdown_text.append(f" {val:3.0f}/100", style=bar_color)

        console.print(Panel(
            score_text + breakdown_text,
            title="[bold]Site Score Summary",
            border_style=color,
            padding=(0, 2),
        ))

        # ── Consolidated Issues Table ────────────────────────────────────────
        consolidated_issues = []
        # Add site issues
        for issue in result.site_issues:
            consolidated_issues.append((
                issue.title,
                issue.description,
                issue.severity,
                issue.category,
                "Site-Wide"
            ))

        # Group page issues
        page_issues_map = {}
        for url, p_res in result.pages.items():
            for issue in p_res.issues:
                if issue.severity != Severity.PASS:
                    key = (issue.id, issue.title)
                    page_issues_map.setdefault(key, (issue.title, issue.description, issue.severity, issue.category, []))
                    page_issues_map[key][4].append(url)

        for (iid, title), (title, desc, sev, cat, urls) in page_issues_map.items():
            if len(urls) == result.total_pages:
                affected = "All Pages"
            elif len(urls) > 3:
                affected = f"{len(urls)} Pages (e.g., {urls[0]})"
            else:
                # Truncate URLs for display
                short_urls = []
                for u in urls:
                    parsed_u = urlparse(u)
                    short_urls.append(parsed_u.path or "/")
                affected = ", ".join(short_urls)
            consolidated_issues.append((title, desc, sev, cat, affected))

        if consolidated_issues:
            table = Table(
                title="[bold red]Detected SEO Issues & Opportunities",
                box=box.ROUNDED,
                border_style="red",
                show_header=True,
                header_style="bold white",
            )
            table.add_column("", width=2, no_wrap=True)
            table.add_column("Issue / Category", style="bold white", min_width=25)
            table.add_column("Details", style="dim")
            table.add_column("Affected Pages", style="bright_cyan")

            # Sort: critical first
            order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
            sorted_issues = sorted(consolidated_issues, key=lambda i: order.get(i[2], 3))

            for title, desc, sev, cat, affected in sorted_issues:
                style = _severity_style(sev)
                icon = _severity_icon(sev)
                table.add_row(
                    Text(icon, style=f"bold {style}"),
                    Text(f"{title} ({cat.value})", style=style if sev == Severity.CRITICAL else "white"),
                    Text(desc, style="dim"),
                    Text(affected, style="bright_cyan" if affected != "Site-Wide" else "dim white"),
                )
            console.print(table)

        # ── Pages Breakdown Table ─────────────────────────────────────────────
        pages_table = Table(
            title="[bold]Crawled Pages Directory",
            box=box.ROUNDED,
            border_style="bright_blue",
            show_header=True,
            header_style="bold white",
        )
        pages_table.add_column("URL", style="bright_cyan")
        pages_table.add_column("Status", style="white", justify="center")
        pages_table.add_column("Score", style="white", justify="center")
        pages_table.add_column("Word Count", style="dim", justify="right")
        pages_table.add_column("Page Title", style="dim")

        for u, res in result.pages.items():
            p_score = res.score
            p_color = "green" if p_score >= 80 else "yellow" if p_score >= 60 else "red"
            status = res.page.status_code or "?"
            status_style = "green" if status == 200 else "red"
            pages_table.add_row(
                u,
                Text(str(status), style=status_style),
                Text(f"{p_score:.0f}", style=p_color),
                str(res.page.word_count),
                res.page.title or "—",
            )
        console.print(pages_table)

        # ── Internal Link Graph & Orphans ─────────────────────────────────────
        orphans = result.orphan_pages
        links_panel_text = Text()
        links_panel_text.append(f"Orphan Pages Found: ", style="bold")
        if orphans:
            links_panel_text.append(f"{len(orphans)}\n", style="bold red")
            for o in orphans:
                links_panel_text.append(f"  • {o}\n", style="dim red")
        else:
            links_panel_text.append("0 (Excellent! All pages have internal links)\n", style="green")

        console.print(Panel(
            links_panel_text,
            title="[bold]Site Architecture & Internal Links",
            border_style="yellow" if orphans else "green",
            padding=(0, 2),
        ))

        # ── Duplicate Content Clusters ────────────────────────────────────────
        if result.duplicate_clusters:
            clusters_tree = Tree("[bold red]Duplicate Content Clusters")
            for cluster in result.duplicate_clusters:
                branch = clusters_tree.add(f"[bold]Content Hash: {cluster.content_hash[:8]}[/] [dim]({len(cluster.urls)} identical pages)[/]")
                for u in cluster.urls:
                    branch.add(f"[dim]{u}[/]")
            console.print(Panel(clusters_tree, border_style="red", padding=(0, 1)))

        # ── Site Recommendations ──────────────────────────────────────────────
        if result.site_recommendations:
            rec_tree = Tree("[bold bright_blue]💡 Site-Wide Strategic Recommendations")
            for i, rec in enumerate(result.site_recommendations[:5], 1):
                impact_color = "green" if rec.impact == "high" else "yellow" if rec.impact == "medium" else "white"
                branch = rec_tree.add(
                    f"[bold]{i}. {rec.title}[/] "
                    f"[dim](Priority {rec.priority} • Impact: [{impact_color}]{rec.impact}[/] • Effort: {rec.effort})[/]"
                )
                branch.add(Text(rec.body, style="dim"))
            console.print(Panel(rec_tree, border_style="bright_blue", padding=(0, 1)))

        console.print()

    def render_keywords(self, result: Any) -> None:
        """Render keyword research results."""
        from openseo.models.result import KeywordResult

        if not isinstance(result, KeywordResult):
            self.render_error("Invalid result type for keyword renderer.")
            return

        console.print()
        console.print(Panel(
            f"[bold]🔑 Keyword Research[/]\n[dim]{result.topic or result.url or ''}[/]",
            border_style="bright_blue",
        ))

        if result.primary_keywords:
            t = Table(title="Primary Keywords", box=box.ROUNDED, border_style="green")
            t.add_column("Keyword", style="bold green")
            for kw in result.primary_keywords:
                t.add_row(kw)
            console.print(t)

        if result.long_tail_keywords:
            t = Table(title="Long-Tail Keywords", box=box.SIMPLE)
            t.add_column("Keyword", style="cyan")
            for kw in result.long_tail_keywords:
                t.add_row(kw)
            console.print(t)

        if result.questions:
            tree = Tree("[bold yellow]❓ Questions People Ask")
            for q in result.questions:
                tree.add(f"[dim]{q}[/]")
            console.print(tree)

    def render_error(self, message: str, hint: str | None = None) -> None:
        """Render an error panel."""
        content = Text(f"✗ {message}", style="bold red")
        if hint:
            content.append(f"\n  {hint}", style="dim yellow")
        error_console.print(Panel(content, border_style="red", padding=(0, 1)))

    def render_success(self, message: str) -> None:
        """Render a success message."""
        console.print(f"[bold green]✓[/] {message}")

    def render_info(self, message: str) -> None:
        """Render an info message."""
        console.print(f"[dim]ℹ[/] {message}")

    @staticmethod
    def create_spinner(description: str) -> Progress:
        """Create a spinner progress context for long-running tasks."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        )


__all__ = ["TerminalRenderer", "console"]
