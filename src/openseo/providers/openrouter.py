"""
OpenRouter provider — access hundreds of models via one API.
"""

from __future__ import annotations

from openseo.providers.litellm_provider import LiteLLMProvider


class OpenRouterProvider(LiteLLMProvider):
    """OpenRouter provider — unified access to 100+ models."""

    name = "openrouter"
    display_name = "OpenRouter"

    def __init__(
        self,
        model: str = "openrouter/google/gemma-3-12b-it:free",
        api_key: str | None = None,
        api_base: str | None = None,
    ) -> None:
        super().__init__(model=model, api_key=api_key, api_base=api_base)


__all__ = ["OpenRouterProvider"]
