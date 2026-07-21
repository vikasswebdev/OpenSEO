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
    quality: bool = False,
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

    qrg_data = None
    if quality:
        from openseo.analyzers.qrg import analyze_qrg
        qrg_data = analyze_qrg(page.body_text or "")

        if output == "terminal":
            color = "green" if qrg_data["overall_quality"] >= 70 else "yellow" if qrg_data["overall_quality"] >= 50 else "red"
            filler_color = "red" if qrg_data["filler_score"] >= 50 else "yellow" if qrg_data["filler_score"] >= 30 else "green"
            ai_color = "red" if qrg_data["ai_pattern_score"] >= 40 else "yellow" if qrg_data["ai_pattern_score"] >= 20 else "green"
            density_color = "green" if qrg_data["information_density"] >= 0.40 else "yellow" if qrg_data["information_density"] >= 0.20 else "red"
            rep_color = "red" if qrg_data["repetition_score"] >= 30 else "yellow" if qrg_data["repetition_score"] >= 15 else "green"
            
            panel_content = (
                f"[bold]Overall Quality Score:[/] [{color}]{qrg_data['overall_quality']}/100[/]\n"
                f"  • [bold]Filler Score:[/] [{filler_color}]{qrg_data['filler_score']}/100[/] (lower is better)\n"
                f"  • [bold]AI-Pattern Score:[/] [{ai_color}]{qrg_data['ai_pattern_score']}/100[/] (lower is better)\n"
                f"  • [bold]Information Density:[/] [{density_color}]{qrg_data['information_density']:.2f}[/] (range: 0.0 - 1.0)\n"
                f"  • [bold]Repetition Score:[/] [{rep_color}]{qrg_data['repetition_score']}/100[/] (lower is better)\n"
                f"  • [bold]Word/Token Count:[/] {qrg_data['tokens']} ({qrg_data['unique_tokens']} unique)\n"
            )
            if qrg_data["flags"]:
                panel_content += f"  • [bold]Flags:[/] [orange1]{', '.join(qrg_data['flags'])}[/]\n"

            console.print(Panel(
                panel_content.strip(),
                title="[bold]QRG Quality Metrics",
                border_style="bright_magenta",
            ))

            if qrg_data["matches"]["filler"]:
                console.print(f"[bold yellow]Filler Hits:[/] {', '.join(qrg_data['matches']['filler'][:8])}")
            if qrg_data["matches"]["ai_patterns"]:
                console.print(f"[bold cyan]AI Pattern Hits:[/] {', '.join(qrg_data['matches']['ai_patterns'][:8])}")
            console.print()

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
            if qrg_data:
                data["qrg_quality"] = qrg_data
            print(json.dumps(data, indent=2))

    except Exception as e:
        # If LLM fails but we got QRG data, and output was not terminal, print QRG data at least
        if qrg_data and output != "terminal":
            print(json.dumps({"qrg_quality": qrg_data, "llm_error": str(e)}, indent=2))
        else:
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
        quality: Annotated[bool, typer.Option("--quality", "-q", help="Run local QRG quality checks (AI patterns, filler, density)")] = False,
    ) -> None:
        """
        Analyze and optimize page content with AI.

        Examples:

          seo content https://example.com/blog/post --keyword "python tutorial"
          
          seo content https://example.com/blog/post --quality
        """
        asyncio.run(_run_content(url, keyword, provider, model, output, quality))
