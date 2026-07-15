"""
Configuration schema using Pydantic v2 with settings management.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from openseo.constants import (
    DEFAULT_CACHE_TTL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT,
    KNOWN_PROVIDERS,
)


class ProviderConfig(BaseModel):
    """Configuration for a specific LLM provider."""

    name: str = Field(..., description="Provider identifier")
    model: str = Field(..., description="Default model for this provider")
    api_key: str | None = Field(None, description="API key (or use env var)")
    api_base: str | None = Field(None, description="Custom base URL")
    extra: dict[str, str] = Field(default_factory=dict, description="Extra provider options")


class CacheConfig(BaseModel):
    """Cache configuration."""

    enabled: bool = Field(True, description="Whether caching is enabled")
    ttl: int = Field(DEFAULT_CACHE_TTL, description="Cache TTL in seconds")
    max_size_mb: int = Field(100, description="Maximum cache size in MB")


class TelemetryConfig(BaseModel):
    """Telemetry / analytics configuration."""

    enabled: bool = Field(False, description="Whether anonymous telemetry is enabled")
    anonymous_id: str | None = Field(None, description="Anonymous user ID for telemetry")


class OutputConfig(BaseModel):
    """Output rendering configuration."""

    format: Literal["terminal", "markdown", "json"] = Field(
        "terminal", description="Default output format"
    )
    theme: Literal["dark", "light", "auto"] = Field("auto", description="Terminal color theme")
    verbose: bool = Field(False, description="Enable verbose output")
    no_color: bool = Field(False, description="Disable color output")


class OpenSEOConfig(BaseModel):
    """
    Root configuration model for OpenSEO.

    Stored at ~/.openseo/config.json
    """

    # Active provider
    provider: str = Field(DEFAULT_PROVIDER, description="Active LLM provider")
    model: str = Field(DEFAULT_MODEL, description="Active model")

    # Timeouts & retries
    timeout: int = Field(DEFAULT_TIMEOUT, description="HTTP timeout in seconds")
    max_retries: int = Field(DEFAULT_MAX_RETRIES, description="Max LLM call retries")
    max_tokens: int = Field(DEFAULT_MAX_TOKENS, description="Max tokens per LLM response")
    temperature: float = Field(DEFAULT_TEMPERATURE, ge=0.0, le=2.0, description="LLM temperature")

    # Sub-configs
    cache: CacheConfig = Field(default_factory=CacheConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    # Stored provider credentials (optional — prefer env vars)
    providers: dict[str, ProviderConfig] = Field(
        default_factory=dict,
        description="Per-provider configuration overrides",
    )

    # Workspace
    workspace: str | None = Field(None, description="Default workspace directory")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate that the provider is known or allow custom ones."""
        # Allow custom / unknown providers (future extensibility)
        return v.lower()

    def get_provider_config(self, name: str | None = None) -> ProviderConfig | None:
        """Return stored config for a provider, or None."""
        target = name or self.provider
        return self.providers.get(target)

    def set_provider_api_key(self, provider: str, api_key: str) -> None:
        """Store an API key for a provider."""
        from openseo.constants import PROVIDER_DEFAULT_MODELS

        if provider not in self.providers:
            self.providers[provider] = ProviderConfig(
                name=provider,
                model=PROVIDER_DEFAULT_MODELS.get(provider, DEFAULT_MODEL),
                api_key=api_key,
            )
        else:
            self.providers[provider] = self.providers[provider].model_copy(
                update={"api_key": api_key}
            )


__all__ = [
    "ProviderConfig",
    "CacheConfig",
    "TelemetryConfig",
    "OutputConfig",
    "OpenSEOConfig",
]
