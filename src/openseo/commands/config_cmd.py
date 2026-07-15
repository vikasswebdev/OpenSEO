"""
`seo config` command — view and update configuration.
"""

from __future__ import annotations

import json
from typing import Annotated, Optional

import typer
from rich import box
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from openseo.config.manager import get_config_manager
from openseo.exceptions import ConfigurationError

console = Console()
app = typer.Typer(help="Manage OpenSEO configuration.")


def register(parent: typer.Typer) -> None:
    """Register the config command group."""

    @parent.command("config")
    def config_cmd(
        key: Annotated[Optional[str], typer.Argument(help="Config key to get")] = None,
        value: Annotated[Optional[str], typer.Argument(help="Value to set")] = None,
        show: Annotated[bool, typer.Option("--show", help="Show full config")] = False,
        reset: Annotated[bool, typer.Option("--reset", help="Reset to defaults")] = False,
    ) -> None:
        """
        View and update OpenSEO configuration.

        Examples:

          seo config --show

          seo config provider anthropic

          seo config model claude-3-5-haiku-20241022

          seo config --reset
        """
        config_manager = get_config_manager()

        if reset:
            cfg = config_manager.reset()
            console.print(f"[green]✓[/] Config reset to defaults.")
            return

        if show or (key is None and value is None):
            cfg = config_manager.load_or_default()
            data = cfg.model_dump(mode="json")
            syntax = Syntax(json.dumps(data, indent=2), "json", theme="monokai")
            console.print(syntax)
            return

        if key and value is None:
            # Get a value
            cfg = config_manager.load_or_default()
            val = getattr(cfg, key, None)
            if val is None:
                console.print(f"[red]Unknown key:[/] {key}")
                raise typer.Exit(1)
            console.print(f"[dim]{key}:[/] [bold]{val}[/]")
            return

        if key and value:
            # Set a value
            try:
                # Type coercion
                cfg = config_manager.load_or_default()
                current = getattr(cfg, key, None)
                if isinstance(current, bool):
                    typed_value: object = value.lower() in ("true", "1", "yes")
                elif isinstance(current, int):
                    typed_value = int(value)
                elif isinstance(current, float):
                    typed_value = float(value)
                else:
                    typed_value = value

                config_manager.set(key, typed_value)
                console.print(f"[green]✓[/] Set [bold]{key}[/] = [cyan]{value}[/]")
            except ConfigurationError as e:
                console.print(f"[red]Error:[/] {e}")
                raise typer.Exit(1)
