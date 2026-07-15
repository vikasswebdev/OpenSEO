"""
`seo sitemap` command — analyze or fetch a sitemap.
"""

from __future__ import annotations

import asyncio
from typing import Annotated

import httpx
import typer
from rich import box
from rich.console import Console
from rich.table import Table

from openseo.constants import USER_AGENT

console = Console()


async def _fetch_sitemap(url: str) -> str | None:
    """Fetch the sitemap content from a URL."""
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=20) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
        except Exception:
            return None


async def _run_sitemap(url: str) -> None:
    from bs4 import BeautifulSoup

    # Attempt common sitemap URLs if root given
    candidates = []
    if not url.endswith(".xml"):
        from urllib.parse import urlparse
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        candidates = [
            f"{base}/sitemap.xml",
            f"{base}/sitemap_index.xml",
            f"{base}/sitemap-index.xml",
        ]
    else:
        candidates = [url]

    sitemap_content = None
    sitemap_url = None
    for candidate in candidates:
        typer.echo(f"Trying: {candidate}", err=True)
        sitemap_content = await _fetch_sitemap(candidate)
        if sitemap_content:
            sitemap_url = candidate
            break

    if not sitemap_content:
        console.print("[red]✗[/] No sitemap found. Tried:")
        for c in candidates:
            console.print(f"  [dim]{c}[/]")
        raise typer.Exit(1)

    soup = BeautifulSoup(sitemap_content, "xml")
    urls = [loc.get_text() for loc in soup.find_all("loc")]

    console.print(f"\n[green]✓[/] Sitemap found: [cyan]{sitemap_url}[/]")
    console.print(f"[dim]{len(urls)} URLs indexed[/]\n")

    table = Table(
        "#", "URL", "Last Modified",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold",
    )
    for i, loc in enumerate(urls[:50], 1):
        lastmod = ""
        table.add_row(str(i), loc, lastmod)

    console.print(table)
    if len(urls) > 50:
        console.print(f"[dim]... and {len(urls) - 50} more URLs[/]")


def register(app: typer.Typer) -> None:
    """Register the sitemap command."""

    @app.command("sitemap")
    def sitemap(
        url: Annotated[str, typer.Argument(help="Website URL or direct sitemap XML URL")],
    ) -> None:
        """
        Fetch and analyze a website's sitemap.

        Examples:

          seo sitemap https://example.com

          seo sitemap https://example.com/sitemap.xml
        """
        asyncio.run(_run_sitemap(url))
