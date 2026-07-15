"""
Anthropic Claude provider — wraps LiteLLMProvider with Claude-specific defaults.
"""

from __future__ import annotations

from openseo.providers.litellm_provider import LiteLLMProvider


class ClaudeProvider(LiteLLMProvider):
    """Anthropic Claude provider (claude-3-5-sonnet, claude-3-5-haiku, etc.)."""

    name = "anthropic"
    display_name = "Anthropic Claude"

    def __init__(
        self,
        model: str = "claude-3-5-haiku-20241022",
        api_key: str | None = None,
        api_base: str | None = None,
    ) -> None:
        super().__init__(model=model, api_key=api_key, api_base=api_base)


__all__ = ["ClaudeProvider"]
