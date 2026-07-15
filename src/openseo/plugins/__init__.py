"""Plugins package."""

from openseo.plugins.loader import PluginLoader, load_all_plugins
from openseo.plugins.registry import PluginMetadata, PluginRegistry, get_registry

__all__ = [
    "PluginLoader",
    "load_all_plugins",
    "PluginMetadata",
    "PluginRegistry",
    "get_registry",
]
