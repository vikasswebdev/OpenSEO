"""
`seo provider` command — manage LLM providers.
"""

from __future__ import annotations

import os
from typing import Annotated, Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from openseo.config.manager import get_config_manager
from openseo.constants import KNOWN_PROVIDERS, PROVIDER_DEFAULT_MODELS
from openseo.providers.registry import list_providers

console = Console()


def register(app: typer.Typer) -> None:
    """Register the provider command."""

    provider_app = typer.Typer(help="Manage LLM providers.")
    app.add_typer(provider_app, name="provider")

    @provider_app.command("list")
    def provider_list() -> None:
        """List all supported LLM providers."""
        config_manager = get_config_manager()
        config = config_manager.load_or_default()
        active = config.provider

        table = Table(
            "Provider ID", "Display Name", "Default Model", "Status",
            box=box.ROUNDED,
            border_style="bright_blue",
            title="[bold]Available LLM Providers",
        )
        for pid, pname in list_providers().items():
            model = PROVIDER_DEFAULT_MODELS.get(pid, "—")
            is_active = pid == active
            status_text = Text("● active", style="bold green") if is_active else Text("○", style="dim")
            table.add_row(
                Text(pid, style="bold cyan" if is_active else "white"),
                pname,
                model,
                status_text,
            )
        console.print(table)

    @provider_app.command("use")
    def provider_use(
        name: Annotated[str, typer.Argument(help="Provider name to activate")],
        model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
    ) -> None:
        """Switch the active LLM provider."""
        from openseo.providers.registry import is_known_provider
        if not is_known_provider(name):
            console.print(f"[yellow]Warning:[/] '{name}' is not a built-in provider.")

        config_manager = get_config_manager()
        config = config_manager.load_or_default()
        resolved_model = model or PROVIDER_DEFAULT_MODELS.get(name, config.model)
        config_manager.set("provider", name)
        config_manager.set("model", resolved_model)
        console.print(f"[green]✓[/] Active provider set to [bold]{name}[/] / [bold]{resolved_model}[/]")

    @provider_app.command("set-key")
    def provider_set_key(
        name: Annotated[str, typer.Argument(help="Provider name")],
        key: Annotated[Optional[str], typer.Argument(help="API key (leave blank to use env var)")] = None,
    ) -> None:
        """
        Store an API key for a provider.

        Example:

          seo provider set-key openai sk-...

          seo provider set-key anthropic
        """
        if key is None:
            env_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "gemini": "GEMINI_API_KEY",
                "groq": "GROQ_API_KEY",
                "openrouter": "OPENROUTER_API_KEY",
            }
            env_var = env_map.get(name)
            if env_var:
                key = os.environ.get(env_var)
                if key:
                    console.print(f"[dim]Using {env_var} from environment[/]")
                else:
                    console.print(f"[red]Error:[/] No key provided and {env_var} not set.")
                    raise typer.Exit(1)
            else:
                console.print(f"[red]Error:[/] No API key provided.")
                raise typer.Exit(1)

        config_manager = get_config_manager()
        config = config_manager.load_or_default()
        config.set_provider_api_key(name, key)
        config_manager.save(config)
        console.print(f"[green]✓[/] API key stored for [bold]{name}[/]")
        console.print(f"[dim](Key stored in config; prefer environment variables for security)[/]")

    @provider_app.command("info")
    def provider_info(
        name: Annotated[str, typer.Argument(help="Provider name")],
    ) -> None:
        """Show information about a provider."""
        display = KNOWN_PROVIDERS.get(name, name)
        model = PROVIDER_DEFAULT_MODELS.get(name, "—")
        console.print(f"\n[bold]{display}[/] [dim]({name})[/]")
        console.print(f"  Default model: [cyan]{model}[/]")
        console.print()
