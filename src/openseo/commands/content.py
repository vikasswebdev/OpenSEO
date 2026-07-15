"""
`seo content` command — AI-powered content optimization.
"""

from __future__ import annotations

import asyncio
import json
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from openseo.config.manager import get_config_manager
from openseo.crawler.http import HttpCrawler
from openseo.outputs import get_renderer
from openseo.prompts.manager import PromptManager
from openseo.services.llm import LLMService

console = Console()


async def _run_content(
    url: str,
    keyword: str,
    provider: str | None,
    model: str | None,
    output: str,
) -> None:
    renderer = get_renderer(output)
    config_manager = get_config_manager()

    typer.echo(f"🕸  Crawling {url}...", err=True)
    try:
        async with HttpCrawler() as crawler:
            page = await crawler.fetch(url)
    except Exception as e:
        renderer.render_error(str(e))
        raise typer.Exit(1)

    llm = LLMService(config_manager, provider_override=provider, model_override=model)
    prompt_manager = PromptManager()
    prompt = prompt_manager.render(
        "content",
        url=url,
        target_keyword=keyword,
        title=page.title or "",
        meta_description=page.meta_description or "",
        word_count=str(page.word_count),
        body_text=page.body_text[:3000],
    )

    typer.echo("🤖 Analyzing content...", err=True)
    try:
        response = await llm.generate(prompt)
        raw = response.content
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        data = json.loads(raw.strip())

        if output == "terminal":
            score = data.get("content_score", 0)
            color = "green" if score >= 70 else "yellow" if score >= 50 else "red"
            console.print(Panel(
                f"[bold]Content Score:[/] [{color}]{score}/100[/]\n\n"
                f"[bold]Optimized Title:[/]\n[italic]{data.get('optimized_title', '')}[/]\n\n"
                f"[bold]Optimized Meta Description:[/]\n[italic]{data.get('optimized_meta_description', '')}[/]",
                title="[bold]Content Analysis",
                border_style="bright_blue",
            ))

            gaps = data.get("content_gaps", [])
            if gaps:
                console.print("\n[bold yellow]Content Gaps:[/]")
                for g in gaps:
                    console.print(f"  • {g}")

            suggestions = data.get("suggestions", [])
            if suggestions:
                console.print("\n[bold cyan]Suggestions:[/]")
                for s in suggestions:
                    console.print(f"  → {s}")
        else:
            print(json.dumps(data, indent=2))

    except Exception as e:
        renderer.render_error(str(e))
        raise typer.Exit(1)


def register(app: typer.Typer) -> None:
    """Register the content command."""

    @app.command("content")
    def content(
        url: Annotated[str, typer.Argument(help="URL to analyze")],
        keyword: Annotated[str, typer.Option("--keyword", "-k", help="Target keyword")] = "",
        provider: Annotated[Optional[str], typer.Option("--provider", "-p")] = None,
        model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
        output: Annotated[str, typer.Option("--output", "-o")] = "terminal",
    ) -> None:
        """
        Analyze and optimize page content with AI.

        Examples:

          seo content https://example.com/blog/post --keyword "python tutorial"
        """
        asyncio.run(_run_content(url, keyword, provider, model, output))
