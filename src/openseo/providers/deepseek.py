"""
DeepSeek provider.
"""

from __future__ import annotations

from openseo.providers.litellm_provider import LiteLLMProvider


class DeepSeekProvider(LiteLLMProvider):
    """DeepSeek provider."""

    name = "deepseek"
    display_name = "DeepSeek"

    def __init__(
        self,
        model: str = "deepseek/deepseek-chat",
        api_key: str | None = None,
        api_base: str | None = None,
    ) -> None:
        super().__init__(model=model, api_key=api_key, api_base=api_base)


__all__ = ["DeepSeekProvider"]
