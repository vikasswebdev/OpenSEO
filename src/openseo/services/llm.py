"""
LLMService — the single entry point for all LLM interactions.

Responsibilities:
- Load and configure the active provider
- Send prompts and receive responses
- Handle streaming
- Retry with exponential backoff
- Provider switching
- Rate limit handling
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from openseo.config.manager import ConfigManager, get_config_manager
from openseo.exceptions import ProviderError, RateLimitError
from openseo.providers.base import BaseProvider, CompletionResponse, Message
from openseo.providers.registry import create_provider

logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM service — the only class that commands and analyzers use.

    The CLI never instantiates providers directly; it always goes through
    this service. This allows provider switching, retries, and fallbacks
    to happen transparently.
    """

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        *,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> None:
        self._config_manager = config_manager or get_config_manager()
        self._provider_override = provider_override
        self._model_override = model_override
        self._provider: BaseProvider | None = None

    def _get_provider(self) -> BaseProvider:
        """Lazily initialize and return the active provider."""
        if self._provider is not None:
            return self._provider

        config = self._config_manager.load_or_default()

        provider_name = self._provider_override or config.provider
        model = self._model_override or config.model

        # Check for stored API key
        provider_conf = config.get_provider_config(provider_name)
        api_key = provider_conf.api_key if provider_conf else None
        api_base = provider_conf.api_base if provider_conf else None

        self._provider = create_provider(
            provider=provider_name,
            model=model,
            api_key=api_key,
            api_base=api_base,
        )
        logger.debug(
            "LLMService: using provider=%s model=%s", provider_name, model
        )
        return self._provider

    def switch_provider(self, provider: str, model: str | None = None) -> None:
        """Switch to a different provider (resets the cached instance)."""
        self._provider_override = provider
        self._model_override = model
        self._provider = None
        logger.info("Switched to provider: %s / model: %s", provider, model)

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        system: str | None = None,
        retries: int | None = None,
    ) -> CompletionResponse:
        """
        Generate a completion with automatic retry on rate limit.

        Args:
            prompt: User prompt string
            max_tokens: Override max tokens (uses config default if None)
            temperature: Override temperature (uses config default if None)
            system: Optional system prompt
            retries: Override retry count (uses config default if None)

        Returns:
            CompletionResponse
        """
        config = self._config_manager.load_or_default()
        effective_max_tokens = max_tokens or config.max_tokens
        effective_temperature = temperature if temperature is not None else config.temperature
        effective_retries = retries if retries is not None else config.max_retries

        provider = self._get_provider()
        last_exc: Exception | None = None

        for attempt in range(effective_retries + 1):
            try:
                return await provider.generate(
                    prompt,
                    max_tokens=effective_max_tokens,
                    temperature=effective_temperature,
                    system=system,
                )
            except RateLimitError as e:
                last_exc = e
                wait = min(2 ** attempt * 1.0, 30.0)
                logger.warning(
                    "Rate limit hit (attempt %d/%d). Waiting %.1fs...",
                    attempt + 1, effective_retries + 1, wait,
                )
                if attempt < effective_retries:
                    await asyncio.sleep(wait)
            except ProviderError:
                raise

        assert last_exc is not None
        raise last_exc

    async def stream(
        self,
        prompt: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream a completion token-by-token."""
        config = self._config_manager.load_or_default()
        provider = self._get_provider()

        async for chunk in provider.stream(
            prompt,
            max_tokens=max_tokens or config.max_tokens,
            temperature=temperature if temperature is not None else config.temperature,
            system=system,
        ):
            yield chunk

    async def chat(
        self,
        messages: list[Message],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> CompletionResponse:
        """Send a multi-turn conversation."""
        config = self._config_manager.load_or_default()
        provider = self._get_provider()

        return await provider.chat(
            messages,
            max_tokens=max_tokens or config.max_tokens,
            temperature=temperature if temperature is not None else config.temperature,
        )

    async def health_check(self) -> bool:
        """Check if the current provider is reachable."""
        try:
            provider = self._get_provider()
            return await provider.health_check()
        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        """Return the active provider name."""
        return self._get_provider().name

    @property
    def model_name(self) -> str:
        """Return the active model name."""
        return self._get_provider().model


__all__ = ["LLMService"]
