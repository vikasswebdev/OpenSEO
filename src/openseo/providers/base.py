"""
Abstract base provider interface.

All LLM providers must implement this protocol.
The CLI and services ONLY interact through this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class Message:
    """A single chat message."""

    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class CompletionResponse:
    """Response from a completion or chat call."""

    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = "stop"
    raw: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Return total token count."""
        return self.input_tokens + self.output_tokens


@dataclass
class EmbeddingResponse:
    """Response from an embedding call."""

    embedding: list[float]
    model: str
    provider: str
    input_tokens: int = 0


class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Implementors must provide generate(), stream(), and chat().
    embedding() is optional (raises NotImplementedError by default).
    """

    name: str = "base"
    display_name: str = "Base Provider"

    def __init__(self, model: str, api_key: str | None = None, api_base: str | None = None) -> None:
        self.model = model
        self.api_key = api_key
        self.api_base = api_base

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        system: str | None = None,
    ) -> CompletionResponse:
        """
        Generate a completion for a single prompt string.

        Args:
            prompt: The user prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: Optional system prompt

        Returns:
            CompletionResponse with the generated text
        """
        ...

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream a completion token by token.

        Yields string chunks as they are received from the provider.
        """
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> CompletionResponse:
        """
        Send a multi-turn conversation to the provider.

        Args:
            messages: Ordered list of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            CompletionResponse with the assistant reply
        """
        ...

    async def embedding(self, text: str) -> EmbeddingResponse:
        """
        Generate an embedding vector for the given text.

        Not all providers support embeddings.
        Override in subclasses that do.
        """
        raise NotImplementedError(
            f"Provider '{self.name}' does not support embeddings."
        )

    async def health_check(self) -> bool:
        """
        Perform a lightweight health check.

        Returns True if the provider is reachable and authenticated.
        """
        try:
            resp = await self.generate("ping", max_tokens=5)
            return bool(resp.content)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model!r})"


__all__ = ["Message", "CompletionResponse", "EmbeddingResponse", "BaseProvider"]
