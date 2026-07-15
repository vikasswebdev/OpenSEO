"""
Google Gemini provider — wraps LiteLLMProvider with Gemini-specific defaults.
"""

from __future__ import annotations

from openseo.providers.litellm_provider import LiteLLMProvider


class GeminiProvider(LiteLLMProvider):
    """Google Gemini provider (gemini-1.5-flash, gemini-1.5-pro, etc.)."""

    name = "gemini"
    display_name = "Google Gemini"

    def __init__(
        self,
        model: str = "gemini/gemini-1.5-flash",
        api_key: str | None = None,
        api_base: str | None = None,
    ) -> None:
        super().__init__(model=model, api_key=api_key, api_base=api_base)


__all__ = ["GeminiProvider"]
