"""
Groq provider — wraps LiteLLMProvider with Groq-specific defaults.
"""

from __future__ import annotations

from openseo.providers.litellm_provider import LiteLLMProvider


class GroqProvider(LiteLLMProvider):
    """Groq provider — ultra-fast inference (Llama, Mixtral, Gemma, etc.)."""

    name = "groq"
    display_name = "Groq"

    def __init__(
        self,
        model: str = "groq/llama-3.1-8b-instant",
        api_key: str | None = None,
        api_base: str | None = None,
    ) -> None:
        super().__init__(model=model, api_key=api_key, api_base=api_base)


__all__ = ["GroqProvider"]
