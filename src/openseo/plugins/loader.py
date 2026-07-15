"""
Plugin loader — discovers and loads plugins from the filesystem.

Plugin discovery order:
1. Built-in plugins (plugins/ directory in the package)
2. User plugins (~/.openseo/plugins/)
3. Project-local plugins (./plugins/)
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

from openseo.exceptions import PluginLoadError, PluginNotFoundError
from openseo.plugins.registry import PluginMetadata, PluginRegistry, get_registry

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Discovers and loads OpenSEO plugins.

    Each plugin must have a plugin.yaml in its root directory.
    Optionally, it can have a commands/ directory with command modules.
    """

    def __init__(self, registry: PluginRegistry | None = None) -> None:
        self._registry = registry or get_registry()

    def load_from_directory(self, directory: Path) -> list[PluginMetadata]:
        """
        Discover and load all plugins in a directory.

        Each subdirectory containing plugin.yaml is treated as a plugin.

        Returns:
            List of loaded plugin metadata
        """
        if not directory.exists():
            return []

        loaded = []
        for plugin_dir in directory.iterdir():
            if not plugin_dir.is_dir():
                continue
            yaml_file = plugin_dir / "plugin.yaml"
            if not yaml_file.exists():
                continue
            try:
                metadata = self._load_plugin(plugin_dir)
                loaded.append(metadata)
            except Exception as e:
                logger.warning("Failed to load plugin from %s: %s", plugin_dir, e)

        return loaded

    def _load_plugin(self, plugin_dir: Path) -> PluginMetadata:
        """Load a single plugin from its directory."""
        yaml_file = plugin_dir / "plugin.yaml"
        try:
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        except Exception as e:
            raise PluginLoadError(f"Invalid plugin.yaml in {plugin_dir}: {e}") from e

        metadata = PluginMetadata(
            name=raw.get("name", plugin_dir.name),
            version=raw.get("version", "0.1.0"),
            description=raw.get("description", ""),
            author=raw.get("author", ""),
            homepage=raw.get("homepage", ""),
            commands=raw.get("commands", []),
            path=str(plugin_dir),
        )

        # Load command modules if present
        commands_dir = plugin_dir / "commands"
        typer_app = None
        if commands_dir.exists():
            typer_app = self._load_plugin_commands(commands_dir, metadata.name)

        self._registry.register(metadata, typer_app)
        logger.info("Loaded plugin: %s v%s from %s", metadata.name, metadata.version, plugin_dir)
        return metadata

    def _load_plugin_commands(self, commands_dir: Path, plugin_name: str) -> Any | None:
        """Dynamically load command modules from a plugin."""
        import typer

        plugin_app = typer.Typer(help=f"Commands from plugin: {plugin_name}")

        for cmd_file in commands_dir.glob("*.py"):
            if cmd_file.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    f"openseo_plugin_{plugin_name}_{cmd_file.stem}",
                    cmd_file,
                )
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)  # type: ignore[union-attr]

                if hasattr(module, "register"):
                    module.register(plugin_app)
                    logger.debug("Loaded plugin command: %s.%s", plugin_name, cmd_file.stem)
            except Exception as e:
                logger.warning("Failed to load plugin command %s: %s", cmd_file, e)

        return plugin_app


def load_all_plugins(typer_app: Any | None = None) -> list[PluginMetadata]:
    """
    Load plugins from all standard locations.

    Args:
        typer_app: If provided, register plugin command groups with this app.

    Returns:
        List of all loaded plugin metadata
    """
    from openseo.constants import PLUGINS_DIR

    loader = PluginLoader()
    all_plugins = []

    # User plugins
    all_plugins.extend(loader.load_from_directory(PLUGINS_DIR))

    # Project-local plugins
    local_plugins = Path.cwd() / "plugins"
    if local_plugins.exists():
        all_plugins.extend(loader.load_from_directory(local_plugins))

    # Register plugin Typer apps if a parent app is provided
    if typer_app is not None:
        registry = get_registry()
        for meta in all_plugins:
            plugin_app = registry.get_typer_app(meta.name)
            if plugin_app is not None:
                typer_app.add_typer(plugin_app, name=f"plugin-{meta.name}")

    logger.info("Total plugins loaded: %d", len(all_plugins))
    return all_plugins


__all__ = ["PluginLoader", "load_all_plugins"]
