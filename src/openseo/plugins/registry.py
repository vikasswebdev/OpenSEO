"""
Plugin registry — tracks registered plugins.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata for a loaded plugin."""

    name: str
    version: str
    description: str
    author: str = ""
    homepage: str = ""
    commands: list[str] = field(default_factory=list)
    path: str = ""


class PluginRegistry:
    """
    Central registry for all loaded plugins.

    Plugins register themselves here after loading.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, PluginMetadata] = {}
        self._typer_apps: dict[str, Any] = {}

    def register(self, metadata: PluginMetadata, typer_app: Any | None = None) -> None:
        """Register a plugin."""
        self._plugins[metadata.name] = metadata
        if typer_app is not None:
            self._typer_apps[metadata.name] = typer_app
        logger.info("Plugin registered: %s v%s", metadata.name, metadata.version)

    def get(self, name: str) -> PluginMetadata | None:
        """Return plugin metadata by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> list[PluginMetadata]:
        """Return all registered plugins."""
        return list(self._plugins.values())

    def is_registered(self, name: str) -> bool:
        """Return True if the plugin is registered."""
        return name in self._plugins

    def get_typer_app(self, name: str) -> Any | None:
        """Return the Typer app for a plugin."""
        return self._typer_apps.get(name)


# Module-level singleton registry
_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    """Return the global plugin registry."""
    return _registry


__all__ = ["PluginMetadata", "PluginRegistry", "get_registry"]
