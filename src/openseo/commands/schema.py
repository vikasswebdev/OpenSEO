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


def _generate_profile_template() -> dict:
    name = typer.prompt("Person Name")
    url = typer.prompt("Person Profile/About URL")
    description = typer.prompt("Description", default="")
    same_as_raw = typer.prompt("SameAs URLs (comma-separated, e.g., GitHub, Twitter)", default="")
    knows_about_raw = typer.prompt("KnowsAbout topics (comma-separated)", default="")
    works_for = typer.prompt("Company/Organization works for", default="")
    job_title = typer.prompt("Job Title", default="")
    
    same_as = [s.strip() for s in same_as_raw.split(",") if s.strip()] if same_as_raw else None
    knows_about = [k.strip() for k in knows_about_raw.split(",") if k.strip()] if knows_about_raw else None
    
    person = {"@type": "Person", "name": name, "url": url}
    if description:
        person["description"] = description
    if same_as:
        person["sameAs"] = same_as
    if knows_about:
        person["knowsAbout"] = knows_about
    if works_for:
        person["worksFor"] = {"@type": "Organization", "name": works_for}
    if job_title:
        person["jobTitle"] = job_title
        
    return {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "mainEntity": person,
        "url": url,
    }


def _generate_discussion_template() -> dict:
    headline = typer.prompt("Forum Topic/Discussion Headline")
    author = typer.prompt("Author Name")
    url = typer.prompt("Discussion URL")
    date_published = typer.prompt("Date Published (ISO 8601, e.g., 2026-07-21)", default="")
    text = typer.prompt("Discussion Text Excerpt", default="")
    comment_count = typer.prompt("Comment Count", default="0")
    
    payload = {
        "@context": "https://schema.org",
        "@type": "DiscussionForumPosting",
        "headline": headline,
        "author": {"@type": "Person", "name": author},
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
    }
    if date_published:
        payload["datePublished"] = date_published
    if text:
        payload["text"] = text
    try:
        payload["commentCount"] = int(comment_count)
    except ValueError:
        pass
    return payload


def _generate_order_template() -> dict:
    merchant = typer.prompt("Merchant Name")
    order_url = typer.prompt("Order URL")
    name = typer.prompt("Action Name", default="Order online")
    
    return {
        "@context": "https://schema.org",
        "@type": "OrderAction",
        "name": name,
        "target": {
            "@type": "EntryPoint",
            "urlTemplate": order_url,
            "inLanguage": "en-US",
            "actionPlatform": [
                "https://schema.org/DesktopWebPlatform",
                "https://schema.org/MobileWebPlatform",
            ],
        },
        "deliveryMethod": [
            "https://schema.org/OnSitePickup",
            "https://schema.org/ParcelService",
        ],
        "priceSpecification": {
            "@type": "PriceSpecification",
            "eligibleTransactionVolume": {
                "@type": "PriceSpecification",
                "minPrice": 0,
                "priceCurrency": "USD",
            },
        },
        "merchant": {"@type": "Organization", "name": merchant},
    }


def _generate_reservation_template() -> dict:
    provider = typer.prompt("Reservation Provider Name")
    start = typer.prompt("Start Time (ISO 8601, e.g. 2026-07-21T19:30:00)")
    party_size = typer.prompt("Party Size", default="")
    reservation_id = typer.prompt("Reservation ID", default="")
    kind = typer.prompt("Reservation Kind", default="FoodEstablishmentReservation")
    
    payload = {
        "@context": "https://schema.org",
        "@type": kind,
        "reservationStatus": "https://schema.org/ReservationConfirmed",
        "provider": {"@type": "Organization", "name": provider},
        "reservationFor": {
            "@type": "FoodEstablishment" if kind == "FoodEstablishmentReservation" else "Place",
            "name": provider,
        },
        "startTime": start,
    }
    if party_size:
        try:
            payload["partySize"] = int(party_size)
        except ValueError:
            pass
    if reservation_id:
        payload["reservationId"] = reservation_id
    return payload


def register(app: typer.Typer) -> None:
    """Register the schema command."""

    @app.command("schema")
    def schema(
        url: Annotated[Optional[str], typer.Argument(help="URL to generate schema for")] = None,
        content_type: Annotated[str, typer.Option("--type", "-t", help="Content type hint")] = "auto",
        provider: Annotated[Optional[str], typer.Option("--provider", "-p")] = None,
        model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
        output: Annotated[str, typer.Option("--output", "-o")] = "terminal",
        template: Annotated[Optional[str], typer.Option("--template", help="Interactive schema template (profile, discussion, order, reservation)")] = None,
    ) -> None:
        """
        Generate schema.org JSON-LD structured data.

        Examples:

          seo schema https://example.com/blog/post

          seo schema --template profile
        """
        if template:
            template = template.lower()
            if template == "profile":
                data = _generate_profile_template()
            elif template == "discussion":
                data = _generate_discussion_template()
            elif template == "order":
                data = _generate_order_template()
            elif template == "reservation":
                data = _generate_reservation_template()
            else:
                typer.echo(f"Error: Unknown template '{template}'. Use profile, discussion, order, or reservation.", err=True)
                raise typer.Exit(1)

            if output == "terminal":
                syntax = Syntax(
                    json.dumps(data, indent=2),
                    "json",
                    theme="monokai",
                    line_numbers=True,
                )
                console.print(Panel(syntax, title=f"[bold]Generated Template: {template.capitalize()}[/]", border_style="green"))
            else:
                print(json.dumps(data, indent=2))
        else:
            if not url:
                typer.echo("Error: URL is required unless using --template.", err=True)
                raise typer.Exit(1)
            asyncio.run(_run_schema(url, content_type, provider, model, output))
