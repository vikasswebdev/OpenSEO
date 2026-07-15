"""
Provider registry — factory and discovery for all LLM providers.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from openseo.constants import KNOWN_PROVIDERS, PROVIDER_DEFAULT_MODELS
from openseo.exceptions import ProviderNotFoundError

if TYPE_CHECKING:
    from openseo.providers.base import BaseProvider

logger = logging.getLogger(__name__)

# Map of provider name → (class import path, class name)
_PROVIDER_REGISTRY: dict[str, tuple[str, str]] = {
    "openai": ("openseo.providers.openai", "OpenAIProvider"),
    "anthropic": ("openseo.providers.claude", "ClaudeProvider"),
    "gemini": ("openseo.providers.gemini", "GeminiProvider"),
    "groq": ("openseo.providers.groq", "GroqProvider"),
    "openrouter": ("openseo.providers.openrouter", "OpenRouterProvider"),
    "ollama": ("openseo.providers.ollama", "OllamaProvider"),
    "deepseek": ("openseo.providers.deepseek", "DeepSeekProvider"),
    # Together AI and Fireworks use the generic LiteLLM provider
    "together": ("openseo.providers.litellm_provider", "LiteLLMProvider"),
    "fireworks": ("openseo.providers.litellm_provider", "LiteLLMProvider"),
}

# API key environment variable names per provider
_ENV_KEY_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "ollama": "",  # No key needed
    "deepseek": "DEEPSEEK_API_KEY",
    "together": "TOGETHER_API_KEY",
    "fireworks": "FIREWORKS_API_KEY",
}


def _resolve_api_key(provider: str, explicit_key: str | None) -> str | None:
    """Resolve API key from explicit value or environment variable."""
    if explicit_key:
        return explicit_key
    env_var = _ENV_KEY_MAP.get(provider, "")
    if env_var:
        return os.environ.get(env_var)
    return None


def create_provider(
    provider: str,
    model: str | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
) -> "BaseProvider":
    """
    Instantiate and return a provider by name.

    Args:
        provider: Provider identifier (e.g., "openai", "anthropic")
        model: Model name. Defaults to the provider's default model.
        api_key: API key. Falls back to environment variable.
        api_base: Custom API base URL.

    Returns:
        Configured BaseProvider instance

    Raises:
        ProviderNotFoundError: If the provider is unknown
    """
    provider = provider.lower()

    if provider not in _PROVIDER_REGISTRY:
        raise ProviderNotFoundError(provider)

    module_path, class_name = _PROVIDER_REGISTRY[provider]

    import importlib
    module = importlib.import_module(module_path)
    provider_class = getattr(module, class_name)

    resolved_model = model or PROVIDER_DEFAULT_MODELS.get(provider, "")
    resolved_key = _resolve_api_key(provider, api_key)

    logger.debug(
        "Creating provider: %s / model: %s", provider, resolved_model
    )

    return provider_class(
        model=resolved_model,
        api_key=resolved_key,
        api_base=api_base,
    )


def list_providers() -> dict[str, str]:
    """Return a mapping of provider_id → display_name."""
    return {k: KNOWN_PROVIDERS.get(k, k) for k in _PROVIDER_REGISTRY}


def is_known_provider(name: str) -> bool:
    """Return True if the provider is registered."""
    return name.lower() in _PROVIDER_REGISTRY


def get_env_key_name(provider: str) -> str | None:
    """Return the environment variable name for a provider's API key."""
    return _ENV_KEY_MAP.get(provider.lower) or None


__all__ = [
    "create_provider",
    "list_providers",
    "is_known_provider",
    "get_env_key_name",
]
