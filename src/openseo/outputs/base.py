"""
Abstract renderer interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseRenderer(ABC):
    """
    Abstract base class for all output renderers.

    Renderers are responsible for displaying data to the user.
    Business logic NEVER prints directly — it always calls a renderer.
    """

    @abstractmethod
    def render_audit(self, result: Any) -> None:
        """Render a full AuditResult."""
        ...

    @abstractmethod
    def render_keywords(self, result: Any) -> None:
        """Render keyword research results."""
        ...

    @abstractmethod
    def render_error(self, message: str, hint: str | None = None) -> None:
        """Render an error message."""
        ...

    @abstractmethod
    def render_success(self, message: str) -> None:
        """Render a success message."""
        ...

    @abstractmethod
    def render_info(self, message: str) -> None:
        """Render an informational message."""
        ...


__all__ = ["BaseRenderer"]
