"""
LiteLLM-backed provider implementation.

This single class powers ALL supported LLM providers through LiteLLM's
unified interface. Concrete provider classes are thin wrappers that set
the correct model prefix and any provider-specific defaults.
"""

from __future__ import annotations

import logging
from typing import AsyncIterator

from openseo.exceptions import AuthenticationError, ProviderError, RateLimitError
from openseo.providers.base import (
    BaseProvider,
    CompletionResponse,
    EmbeddingResponse,
    Message,
)

logger = logging.getLogger(__name__)


def _build_litellm_messages(
    prompt: str, system: str | None
) -> list[dict[str, str]]:
    """Build LiteLLM-compatible messages list."""
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _convert_messages(messages: list[Message]) -> list[dict[str, str]]:
    """Convert Message dataclasses to LiteLLM dict format."""
    return [{"role": m.role, "content": m.content} for m in messages]


def _handle_litellm_error(e: Exception, provider_name: str) -> None:
    """Translate LiteLLM exceptions into OpenSEO exceptions."""
    error_str = str(e).lower()

    if "authentication" in error_str or "api key" in error_str or "unauthorized" in error_str:
        raise AuthenticationError(
            f"Authentication failed for provider '{provider_name}'.",
            hint="Check your API key with `seo provider set-key <provider> <key>`.",
        ) from e

    if "rate limit" in error_str or "ratelimit" in error_str or "429" in error_str:
        raise RateLimitError(
            f"Rate limit hit for provider '{provider_name}'.",
        ) from e

    raise ProviderError(f"Provider error from '{provider_name}': {e}") from e


class LiteLLMProvider(BaseProvider):
    """
    Universal LLM provider powered by LiteLLM.

    LiteLLM handles the translation between the universal API and each
    provider's native SDK/REST format.
    """

    name = "litellm"
    display_name = "LiteLLM (Universal)"

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        system: str | None = None,
    ) -> CompletionResponse:
        """Generate a completion using LiteLLM."""
        try:
            import litellm  # type: ignore[import]

            messages = _build_litellm_messages(prompt, system)
            kwargs: dict = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.api_base:
                kwargs["api_base"] = self.api_base

            logger.debug("LiteLLM call: model=%s", self.model)
            response = await litellm.acompletion(**kwargs)

            return CompletionResponse(
                content=response.choices[0].message.content or "",
                model=response.model or self.model,
                provider=self.name,
                input_tokens=getattr(response.usage, "prompt_tokens", 0),
                output_tokens=getattr(response.usage, "completion_tokens", 0),
                finish_reason=response.choices[0].finish_reason or "stop",
                raw=dict(response),
            )
        except Exception as e:
            _handle_litellm_error(e, self.name)
            raise  # unreachable, but satisfies type checker

    async def stream(
        self,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream completion tokens via LiteLLM."""
        try:
            import litellm  # type: ignore[import]

            messages = _build_litellm_messages(prompt, system)
            kwargs: dict = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            }
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.api_base:
                kwargs["api_base"] = self.api_base

            async for chunk in await litellm.acompletion(**kwargs):
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            _handle_litellm_error(e, self.name)

    async def chat(
        self,
        messages: list[Message],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> CompletionResponse:
        """Send a multi-turn conversation via LiteLLM."""
        try:
            import litellm  # type: ignore[import]

            litellm_messages = _convert_messages(messages)
            kwargs: dict = {
                "model": self.model,
                "messages": litellm_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.api_base:
                kwargs["api_base"] = self.api_base

            response = await litellm.acompletion(**kwargs)

            return CompletionResponse(
                content=response.choices[0].message.content or "",
                model=response.model or self.model,
                provider=self.name,
                input_tokens=getattr(response.usage, "prompt_tokens", 0),
                output_tokens=getattr(response.usage, "completion_tokens", 0),
                finish_reason=response.choices[0].finish_reason or "stop",
                raw=dict(response),
            )
        except Exception as e:
            _handle_litellm_error(e, self.name)
            raise

    async def embedding(self, text: str) -> EmbeddingResponse:
        """Generate embeddings via LiteLLM."""
        try:
            import litellm  # type: ignore[import]

            kwargs: dict = {"model": self.model, "input": text}
            if self.api_key:
                kwargs["api_key"] = self.api_key

            response = await litellm.aembedding(**kwargs)
            return EmbeddingResponse(
                embedding=response.data[0]["embedding"],
                model=response.model or self.model,
                provider=self.name,
                input_tokens=getattr(response.usage, "prompt_tokens", 0),
            )
        except Exception as e:
            _handle_litellm_error(e, self.name)
            raise


__all__ = ["LiteLLMProvider"]
