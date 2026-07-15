"""Outputs package — renderer factory and all renderer classes."""

from __future__ import annotations

from openseo.outputs.base import BaseRenderer
from openseo.outputs.json_renderer import JsonRenderer
from openseo.outputs.markdown import MarkdownRenderer
from openseo.outputs.terminal import TerminalRenderer
from openseo.outputs.pdf import PdfRenderer


def get_renderer(
    format: str = "terminal",
    verbose: bool = False,
    no_color: bool = False,
) -> BaseRenderer:
    """
    Return the appropriate renderer for the given format.

    Args:
        format: "terminal", "markdown", or "json"
        verbose: Enable verbose terminal output
        no_color: Disable color output

    Returns:
        Configured BaseRenderer instance
    """
    if format == "json":
        return JsonRenderer()
    if format == "markdown":
        return MarkdownRenderer()
    return TerminalRenderer(verbose=verbose, no_color=no_color)


__all__ = [
    "BaseRenderer",
    "TerminalRenderer",
    "MarkdownRenderer",
    "JsonRenderer",
    "PdfRenderer",
    "get_renderer",
]
