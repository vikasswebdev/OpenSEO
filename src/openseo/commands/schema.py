"""
`seo schema` command — generate schema.org JSON-LD for a URL.
"""

from __future__ import annotations

import asyncio
import json
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from openseo.config.manager import get_config_manager
from openseo.crawler.http import HttpCrawler
from openseo.models.result import SchemaResult
from openseo.outputs import get_renderer
from openseo.prompts.manager import PromptManager
from openseo.services.llm import LLMService

console = Console()


async def _run_schema(
    url: str,
    content_type: str,
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

    existing = [s.type or "?" for s in page.schema_org]
    llm = LLMService(config_manager, provider_override=provider, model_override=model)
    prompt_manager = PromptManager()
    prompt = prompt_manager.render(
        "schema",
        url=url,
        title=page.title or "",
        meta_description=page.meta_description or "",
        content_type=content_type,
        body_text_excerpt=page.body_text[:2000],
        existing_schemas=", ".join(existing) if existing else "None",
    )

    try:
        typer.echo("🤖 Generating schema markup...", err=True)
        response = await llm.generate(prompt)
        raw = response.content
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        data = json.loads(raw.strip())

        if output == "terminal":
            console.print(Panel(
                f"[bold]Schema Type:[/] [green]{data.get('recommended_type', '?')}[/]\n"
                f"[dim]{data.get('reasoning', '')}[/]",
                title="[bold]Schema.org Analysis",
                border_style="bright_blue",
            ))

            json_ld = data.get("json_ld", {})
            syntax = Syntax(
                json.dumps(json_ld, indent=2),
                "json",
                theme="monokai",
                line_numbers=True,
            )
            console.print(Panel(syntax, title="[bold]Generated JSON-LD", border_style="green"))
        else:
            result = SchemaResult(
                url=url,
                existing_schemas=existing,
                generated_schema=json.dumps(data.get("json_ld", {}), indent=2),
                schema_type=data.get("recommended_type"),
                provider_used=llm.provider_name,
                model_used=llm.model_name,
            )
            print(result.model_dump_json(indent=2))

    except Exception as e:
        renderer.render_error(str(e))
        raise typer.Exit(1)


def register(app: typer.Typer) -> None:
    """Register the schema command."""

    @app.command("schema")
    def schema(
        url: Annotated[str, typer.Argument(help="URL to generate schema for")],
        content_type: Annotated[str, typer.Option("--type", "-t", help="Content type hint")] = "auto",
        provider: Annotated[Optional[str], typer.Option("--provider", "-p")] = None,
        model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
        output: Annotated[str, typer.Option("--output", "-o")] = "terminal",
    ) -> None:
        """
        Generate schema.org JSON-LD structured data for a URL.

        Examples:

          seo schema https://example.com/blog/post

          seo schema https://shop.com/product --type product
        """
        asyncio.run(_run_schema(url, content_type, provider, model, output))
