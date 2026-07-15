"""
Application bootstrap — wires together all commands and plugins.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

import typer
from rich.console import Console

from openseo import __version__

console = Console()
logger = logging.getLogger(__name__)


def _configure_logging(verbose: bool = False) -> None:
    """Configure structured logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "litellm", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def create_app() -> typer.Typer:
    """
    Create and configure the main Typer application.

    This function:
    1. Creates the root Typer app
    2. Registers all built-in commands
    3. Loads plugins
    4. Returns the configured app

    Returns:
        Configured Typer application
    """
    app = typer.Typer(
        name="seo",
        help=(
            "[bold bright_blue]OpenSEO[/] — Production-quality SEO CLI powered by any LLM.\n\n"
            "Run [bold]seo init[/] to get started.\n"
            "Run [bold]seo doctor[/] to check your setup.\n"
        ),
        rich_markup_mode="rich",
        pretty_exceptions_enable=True,
        pretty_exceptions_show_locals=False,
        no_args_is_help=True,
        add_completion=True,
    )

    # ── Register Built-in Commands ────────────────────────────────────────────
    from openseo.commands import audit, config_cmd, content, doctor, init, keywords, provider, robots, schema, sitemap

    init.register(app)
    config_cmd.register(app)
    provider.register(app)
    audit.register(app)
    keywords.register(app)
    schema.register(app)
    content.register(app)
    doctor.register(app)
    sitemap.register(app)
    robots.register(app)

    # ── Version Command ───────────────────────────────────────────────────────
    @app.command("version")
    def version_cmd() -> None:
        """Show the current OpenSEO version."""
        from openseo.constants import APP_DISPLAY_NAME, HOMEPAGE
        console.print(f"[bold]{APP_DISPLAY_NAME}[/] v[cyan]{__version__}[/]")
        console.print(f"[dim]{HOMEPAGE}[/]")

    # ── Load Plugins ──────────────────────────────────────────────────────────
    try:
        from openseo.plugins.loader import load_all_plugins
        load_all_plugins(app)
    except Exception as e:
        logger.debug("Plugin loading skipped: %s", e)

    # ── Global Callback ───────────────────────────────────────────────────────
    @app.callback()
    def global_callback(
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging", is_eager=False),
        version: Optional[bool] = typer.Option(None, "--version", "-V", help="Show version", is_eager=True),
    ) -> None:
        """OpenSEO — Production-quality SEO CLI powered by any LLM."""
        if version:
            console.print(f"OpenSEO v{__version__}")
            raise typer.Exit()
        _configure_logging(verbose)

    return app


__all__ = ["create_app"]
