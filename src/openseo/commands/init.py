"""
`seo init` command — initialize OpenSEO configuration.
"""

from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from openseo.config.manager import get_config_manager
from openseo.config.schema import OpenSEOConfig
from openseo.constants import CONFIG_DIR, CONFIG_FILE, KNOWN_PROVIDERS, PROVIDER_DEFAULT_MODELS

console = Console()


def register(app: typer.Typer) -> None:
    """Register the init command."""

    @app.command("init")
    def init(
        provider: Annotated[Optional[str], typer.Option("--provider", "-p", help="Default LLM provider")] = None,
        non_interactive: Annotated[bool, typer.Option("--yes", "-y", help="Skip prompts, use defaults")] = False,
        overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing config")] = False,
    ) -> None:
        """
        Initialize OpenSEO with an interactive setup wizard.

        Creates ~/.openseo/config.json with your preferred settings.

        Example:

          seo init

          seo init --provider openai --yes
        """
        console.print()
        console.print(Panel(
            "[bold bright_blue]🚀 Welcome to OpenSEO![/]\n"
            "[dim]Let's set up your configuration.[/]",
            border_style="bright_blue",
            padding=(1, 2),
        ))

        # Check if already initialized
        config_manager = get_config_manager()
        if CONFIG_FILE.exists() and not overwrite:
            if not non_interactive:
                overwrite = Confirm.ask(
                    f"Config already exists at [cyan]{CONFIG_FILE}[/]. Overwrite?",
                    default=False,
                )
            if not overwrite:
                console.print("[yellow]Init cancelled.[/] Run [bold]seo config[/] to update settings.")
                return

        # Provider selection
        if not provider and not non_interactive:
            console.print("\n[bold]Available LLM Providers:[/]")
            provider_list = list(KNOWN_PROVIDERS.items())
            for i, (pid, pname) in enumerate(provider_list, 1):
                console.print(f"  [cyan]{i:2}.[/] {pname} [dim]({pid})[/]")

            choice = Prompt.ask(
                "\n[bold]Choose a provider[/]",
                default="openai",
                choices=list(KNOWN_PROVIDERS.keys()),
            )
            provider = choice

        selected_provider = provider or "openai"
        default_model = PROVIDER_DEFAULT_MODELS.get(selected_provider, "")

        config = OpenSEOConfig(provider=selected_provider, model=default_model)
        config_manager.save(config)

        # Create directories
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        console.print()
        console.print(Panel(
            f"[green]✓ OpenSEO initialized![/]\n\n"
            f"  [dim]Config:[/]   [cyan]{CONFIG_FILE}[/]\n"
            f"  [dim]Provider:[/] [bold]{selected_provider}[/]\n"
            f"  [dim]Model:[/]    [bold]{default_model}[/]\n\n"
            f"[dim]Next steps:[/]\n"
            f"  Set your API key: [bold]seo provider set-key {selected_provider} <your-key>[/]\n"
            f"  Run a health check: [bold]seo doctor[/]\n"
            f"  Audit a site: [bold]seo audit https://example.com[/]",
            border_style="green",
            padding=(1, 2),
        ))
