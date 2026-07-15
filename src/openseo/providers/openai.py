"""
OpenAI provider — wraps LiteLLMProvider with OpenAI-specific defaults.
"""

from __future__ import annotations

from openseo.providers.litellm_provider import LiteLLMProvider


class OpenAIProvider(LiteLLMProvider):
    """OpenAI provider (GPT-4o, GPT-4o-mini, GPT-4, etc.)."""

    name = "openai"
    display_name = "OpenAI"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        api_base: str | None = None,
    ) -> None:
        # LiteLLM uses bare model names for OpenAI
        super().__init__(model=model, api_key=api_key, api_base=api_base)


__all__ = ["OpenAIProvider"]
