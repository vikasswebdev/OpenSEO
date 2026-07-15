"""
Custom exception hierarchy for OpenSEO.

All exceptions inherit from OpenSEOError so callers can catch the base
class when they do not care about the specific error type.
"""

from __future__ import annotations


class OpenSEOError(Exception):
    """Base exception for all OpenSEO errors."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message}\n  Hint: {self.hint}"
        return self.message


# ─── Provider Exceptions ───────────────────────────────────────────────────────


class ProviderError(OpenSEOError):
    """Raised when an LLM provider encounters an error."""


class AuthenticationError(ProviderError):
    """Raised when API key validation fails."""


class RateLimitError(ProviderError):
    """Raised when an LLM provider rate limit is hit."""

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        hint = f"Retry after {retry_after:.0f}s" if retry_after else "Try again later"
        super().__init__(message, hint=hint)
        self.retry_after = retry_after


class ModelNotFoundError(ProviderError):
    """Raised when the requested model is not available on the provider."""


class ProviderNotFoundError(ProviderError):
    """Raised when the specified provider is not registered."""

    def __init__(self, name: str) -> None:
        super().__init__(
            f"Provider '{name}' is not registered.",
            hint="Run `seo provider list` to see available providers.",
        )
        self.name = name


# ─── Crawler Exceptions ────────────────────────────────────────────────────────


class CrawlerError(OpenSEOError):
    """Base class for crawler-related errors."""


class FetchError(CrawlerError):
    """Raised when a URL cannot be fetched."""

    def __init__(self, url: str, reason: str) -> None:
        super().__init__(f"Failed to fetch '{url}': {reason}")
        self.url = url
        self.reason = reason


class RobotsBlockedError(CrawlerError):
    """Raised when robots.txt disallows crawling."""

    def __init__(self, url: str) -> None:
        super().__init__(
            f"Crawling blocked by robots.txt: {url}",
            hint="Use --ignore-robots to bypass (respect the site owner's wishes).",
        )
        self.url = url


class PlaywrightNotInstalledError(CrawlerError):
    """Raised when Playwright is required but not installed."""

    def __init__(self) -> None:
        super().__init__(
            "Playwright is not installed.",
            hint="Install it with: pip install 'openseo[playwright]' && playwright install chromium",
        )


# ─── Config Exceptions ─────────────────────────────────────────────────────────


class ConfigurationError(OpenSEOError):
    """Raised for configuration-related errors."""


class ConfigNotInitializedError(ConfigurationError):
    """Raised when OpenSEO has not been initialized."""

    def __init__(self) -> None:
        super().__init__(
            "OpenSEO is not initialized.",
            hint="Run `seo init` to get started.",
        )


# ─── Plugin Exceptions ─────────────────────────────────────────────────────────


class PluginError(OpenSEOError):
    """Base class for plugin-related errors."""


class PluginNotFoundError(PluginError):
    """Raised when a plugin cannot be found."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Plugin '{name}' not found.")
        self.name = name


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""


# ─── Validation Exceptions ─────────────────────────────────────────────────────


class ValidationError(OpenSEOError):
    """Raised when input validation fails."""


# ─── Cache Exceptions ──────────────────────────────────────────────────────────


class CacheError(OpenSEOError):
    """Raised when a cache operation fails."""


# ─── Prompt Exceptions ─────────────────────────────────────────────────────────


class PromptError(OpenSEOError):
    """Raised when a prompt cannot be loaded or rendered."""


class PromptNotFoundError(PromptError):
    """Raised when the requested prompt file does not exist."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Prompt '{name}' not found.")
        self.name = name


__all__ = [
    "OpenSEOError",
    "ProviderError",
    "AuthenticationError",
    "RateLimitError",
    "ModelNotFoundError",
    "ProviderNotFoundError",
    "CrawlerError",
    "FetchError",
    "RobotsBlockedError",
    "PlaywrightNotInstalledError",
    "ConfigurationError",
    "ConfigNotInitializedError",
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "ValidationError",
    "CacheError",
    "PromptError",
    "PromptNotFoundError",
]
