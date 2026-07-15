"""
`seo keywords` command — keyword research using LLMs.
"""

from __future__ import annotations

import asyncio
import json
from typing import Annotated, Optional

import typer

from openseo.config.manager import get_config_manager
from openseo.models.result import KeywordResult
from openseo.outputs import get_renderer
from openseo.prompts.manager import PromptManager
from openseo.services.llm import LLMService


async def _run_keywords(
    topic: str,
    url: str | None,
    audience: str,
    content_type: str,
    business_context: str,
    provider: str | None,
    model: str | None,
    output: str,
) -> None:
    renderer = get_renderer(output)
    config_manager = get_config_manager()

    llm = LLMService(config_manager, provider_override=provider, model_override=model)
    prompt_manager = PromptManager()
    prompt = prompt_manager.render(
        "keywords",
        topic=topic or url or "",
        audience=audience,
        content_type=content_type,
        business_context=business_context,
    )

    try:
        typer.echo(f"🔍 Researching keywords for: {topic or url}", err=True)
        response = await llm.generate(prompt)

        raw = response.content
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        data = json.loads(raw.strip())
        result = KeywordResult(
            url=url,
            topic=topic or url,
            primary_keywords=data.get("primary_keywords", []),
            long_tail_keywords=data.get("long_tail_keywords", []),
            questions=data.get("questions", []),
            related_topics=data.get("related_topics", []),
            provider_used=llm.provider_name,
            model_used=llm.model_name,
        )
        renderer.render_keywords(result)
    except Exception as e:
        renderer.render_error(str(e))
        raise typer.Exit(1)


def register(app: typer.Typer) -> None:
    """Register the keywords command."""

    @app.command("keywords")
    def keywords(
        topic: Annotated[str, typer.Argument(help="Topic or keyword to research")],
        url: Annotated[Optional[str], typer.Option("--url", help="Source URL (optional)")] = None,
        audience: Annotated[str, typer.Option("--audience", help="Target audience")] = "general",
        content_type: Annotated[str, typer.Option("--content-type", help="Content type (blog, product, landing)")] = "blog",
        business_context: Annotated[str, typer.Option("--context", help="Business context")] = "",
        provider: Annotated[Optional[str], typer.Option("--provider", "-p")] = None,
        model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
        output: Annotated[str, typer.Option("--output", "-o")] = "terminal",
    ) -> None:
        """
        Research keywords for a topic using AI.

        Examples:

          seo keywords "python web scraping"

          seo keywords "coffee shop" --content-type product --audience "coffee enthusiasts"
        """
        asyncio.run(_run_keywords(topic, url, audience, content_type, business_context, provider, model, output))
