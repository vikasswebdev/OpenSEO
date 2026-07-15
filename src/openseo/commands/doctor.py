"""
`seo doctor` command — health check for OpenSEO configuration and dependencies.
"""

from __future__ import annotations

import asyncio
import importlib
import platform
import sys
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from openseo import __version__
from openseo.config.manager import get_config_manager
from openseo.constants import CONFIG_FILE, KNOWN_PROVIDERS

console = Console()


def _check_dependency(module: str, display_name: str) -> tuple[str, bool, str]:
    """Check if a Python module is importable."""
    try:
        mod = importlib.import_module(module)
        version = getattr(mod, "__version__", "installed")
        return display_name, True, str(version)
    except ImportError:
        return display_name, False, "not installed"


async def _check_provider_connectivity(provider: str, model: str | None) -> bool:
    """Quickly test if a provider is reachable."""
    from openseo.services.llm import LLMService
    from openseo.config.manager import get_config_manager
    llm = LLMService(get_config_manager(), provider_override=provider, model_override=model)
    return await llm.health_check()


def register(app: typer.Typer) -> None:
    """Register the doctor command."""

    @app.command("doctor")
    def doctor(
        check_provider: Annotated[bool, typer.Option("--check-provider", help="Test provider connectivity")] = False,
    ) -> None:
        """
        Run a health check on your OpenSEO installation.

        Checks Python version, dependencies, configuration, and provider connectivity.

        Example:

          seo doctor

          seo doctor --check-provider
        """
        console.print()
        console.print(Panel(
            f"[bold]OpenSEO Doctor[/] [dim]v{__version__}[/]\n"
            f"[dim]Python {sys.version.split()[0]} on {platform.system()} {platform.machine()}[/]",
            border_style="bright_blue",
            padding=(0, 2),
        ))

        # ── Dependency Checks ─────────────────────────────────────────────────
        table = Table(
            "Dependency", "Status", "Version",
            box=box.ROUNDED,
            border_style="bright_blue",
            title="[bold]Dependencies",
        )
        deps = [
            ("typer", "Typer"),
            ("rich", "Rich"),
            ("litellm", "LiteLLM"),
            ("pydantic", "Pydantic"),
            ("httpx", "httpx"),
            ("bs4", "BeautifulSoup4"),
            ("playwright", "Playwright (optional)"),
        ]
        all_ok = True
        for module, name in deps:
            label, ok, ver = _check_dependency(module, name)
            optional = "optional" in name.lower()
            if not ok and not optional:
                all_ok = False
            icon = "[green]✓[/]" if ok else ("[yellow]~[/]" if optional else "[red]✗[/]")
            table.add_row(label, icon, f"[dim]{ver}[/]")
        console.print(table)

        # ── Config Checks ─────────────────────────────────────────────────────
        config_manager = get_config_manager()
        config_table = Table(
            "Check", "Status", "Value",
            box=box.ROUNDED,
            border_style="bright_blue",
            title="[bold]Configuration",
        )

        config_exists = CONFIG_FILE.exists()
        config_table.add_row(
            "Config File",
            "[green]✓[/]" if config_exists else "[red]✗[/]",
            str(CONFIG_FILE) if config_exists else "[red]Run `seo init` first[/]",
        )

        if config_exists:
            config = config_manager.load_or_default()
            config_table.add_row("Provider", "[green]✓[/]", config.provider)
            config_table.add_row("Model", "[green]✓[/]", config.model)
            config_table.add_row("Cache", "[green]✓[/]" if config.cache.enabled else "[yellow]~[/]", "enabled" if config.cache.enabled else "disabled")

        console.print(config_table)

        # ── Provider Connectivity ─────────────────────────────────────────────
        if check_provider and config_exists:
            config = config_manager.load_or_default()
            console.print()
            console.print(f"[dim]Testing {config.provider} connectivity...[/]")
            reachable = asyncio.run(_check_provider_connectivity(config.provider, None))
            if reachable:
                console.print(f"[green]✓[/] Provider [bold]{config.provider}[/] is reachable")
            else:
                console.print(f"[red]✗[/] Provider [bold]{config.provider}[/] is not reachable — check your API key")

        if all_ok:
            console.print(f"\n[bold green]✓ All checks passed.[/] OpenSEO is ready to use!")
        else:
            console.print(f"\n[yellow]⚠ Some checks failed.[/] Run [bold]pip install openseo[all][/] to fix.")
        console.print()
