"""
Ollama provider — local inference via Ollama.
"""

from __future__ import annotations

from openseo.providers.litellm_provider import LiteLLMProvider


class OllamaProvider(LiteLLMProvider):
    """Ollama provider — run models locally."""

    name = "ollama"
    display_name = "Ollama (Local)"

    def __init__(
        self,
        model: str = "ollama/llama3.2",
        api_key: str | None = None,
        api_base: str | None = "http://localhost:11434",
    ) -> None:
        super().__init__(model=model, api_key=api_key, api_base=api_base)


__all__ = ["OllamaProvider"]
