"""
`seo robots` command — analyze robots.txt.
"""

from __future__ import annotations

import asyncio
from typing import Annotated
from urllib.parse import urlparse

import httpx
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from openseo.constants import USER_AGENT

console = Console()


async def _run_robots(url: str) -> None:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    base = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{base}/robots.txt"

    typer.echo(f"Fetching {robots_url}...", err=True)

    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=15) as client:
        try:
            r = await client.get(robots_url)
        except Exception as e:
            console.print(f"[red]✗ Failed to fetch robots.txt:[/] {e}")
            raise typer.Exit(1)

    if r.status_code == 404:
        console.print(f"[yellow]⚠[/] No robots.txt found at [cyan]{robots_url}[/]")
        console.print("[dim]This is valid — no crawling restrictions by default.[/]")
        return

    if r.status_code != 200:
        console.print(f"[red]✗[/] HTTP {r.status_code} for {robots_url}")
        raise typer.Exit(1)

    content = r.text
    console.print(f"\n[green]✓[/] robots.txt found ([dim]{len(content)} bytes[/])\n")

    syntax = Syntax(content, "text", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"[bold]{robots_url}", border_style="bright_blue"))

    # Basic analysis
    lines = content.splitlines()
    disallow_count = sum(1 for l in lines if l.strip().lower().startswith("disallow:"))
    allow_count = sum(1 for l in lines if l.strip().lower().startswith("allow:"))
    sitemap_count = sum(1 for l in lines if l.strip().lower().startswith("sitemap:"))

    sitemaps = [l.split(":", 1)[1].strip() for l in lines if l.strip().lower().startswith("sitemap:")]

    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("", style="dim", min_width=20)
    table.add_column("", style="white")
    table.add_row("Disallow rules", str(disallow_count))
    table.add_row("Allow rules", str(allow_count))
    table.add_row("Sitemaps declared", str(sitemap_count))
    for s in sitemaps:
        table.add_row("", f"[cyan]{s}[/]")

    console.print(Panel(table, title="[bold]Summary", border_style="dim"))


def register(app: typer.Typer) -> None:
    """Register the robots command."""

    @app.command("robots")
    def robots(
        url: Annotated[str, typer.Argument(help="Website URL")],
    ) -> None:
        """
        Fetch and analyze a website's robots.txt file.

        Examples:

          seo robots https://example.com

          seo robots example.com
        """
        asyncio.run(_run_robots(url))
