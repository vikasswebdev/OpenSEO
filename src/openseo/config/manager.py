"""
Configuration manager — reads/writes ~/.openseo/config.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from openseo.config.schema import OpenSEOConfig
from openseo.constants import CONFIG_DIR, CONFIG_FILE
from openseo.exceptions import ConfigNotInitializedError, ConfigurationError

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages the OpenSEO configuration file.

    All reads and writes go through this class.
    The configuration is lazily loaded on first access.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or CONFIG_FILE
        self._config: OpenSEOConfig | None = None

    @property
    def config_path(self) -> Path:
        """Return the resolved config file path."""
        return self._config_path

    @property
    def is_initialized(self) -> bool:
        """Return True if the config file exists."""
        return self._config_path.exists()

    def load(self) -> OpenSEOConfig:
        """
        Load and return the configuration.

        Raises ConfigNotInitializedError if config does not exist.
        """
        if self._config is not None:
            return self._config

        if not self._config_path.exists():
            raise ConfigNotInitializedError()

        try:
            raw = json.loads(self._config_path.read_text(encoding="utf-8"))
            self._config = OpenSEOConfig.model_validate(raw)
            logger.debug("Config loaded from %s", self._config_path)
            return self._config
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Config file is not valid JSON: {self._config_path}",
                hint="Delete the file and run `seo init` to recreate it.",
            ) from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {e}") from e

    def load_or_default(self) -> OpenSEOConfig:
        """
        Load configuration, returning defaults if not initialized.

        Use this for commands that can run without initialization.
        """
        if self.is_initialized:
            return self.load()
        return OpenSEOConfig()

    def save(self, config: OpenSEOConfig) -> None:
        """Persist the configuration to disk."""
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            data = config.model_dump(mode="json", exclude_none=False)
            self._config_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self._config = config
            logger.debug("Config saved to %s", self._config_path)
        except OSError as e:
            raise ConfigurationError(f"Failed to save config: {e}") from e

    def initialize(self, *, overwrite: bool = False) -> OpenSEOConfig:
        """
        Create default configuration file.

        Returns the newly created config.
        """
        if self._config_path.exists() and not overwrite:
            raise ConfigurationError(
                "Config already exists.",
                hint="Use --overwrite to reinitialize.",
            )
        config = OpenSEOConfig()
        self.save(config)
        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a top-level config value by key."""
        config = self.load_or_default()
        return getattr(config, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a top-level config value and save."""
        config = self.load_or_default()
        if not hasattr(config, key):
            raise ConfigurationError(
                f"Unknown config key: '{key}'",
                hint=f"Valid keys: {', '.join(OpenSEOConfig.model_fields.keys())}",
            )
        updated = config.model_copy(update={key: value})
        self.save(updated)

    def reset(self) -> OpenSEOConfig:
        """Reset configuration to defaults."""
        config = OpenSEOConfig()
        self.save(config)
        return config


# Module-level singleton for convenience
_default_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """Return the default ConfigManager singleton."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ConfigManager()
    return _default_manager


def get_config() -> OpenSEOConfig:
    """Shortcut to load the current configuration."""
    return get_config_manager().load()


__all__ = ["ConfigManager", "get_config_manager", "get_config"]
