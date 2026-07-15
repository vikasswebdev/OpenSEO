"""
PromptLoader — loads prompt files from the filesystem.

Prompts are stored as Markdown files and loaded at runtime.
"""

from __future__ import annotations

import logging
from pathlib import Path

from openseo.exceptions import PromptNotFoundError

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Loads prompt Markdown files from a directory.

    Prompts are discovered by their filename (without extension).
    e.g., "audit" → "audit.md"
    """

    def __init__(self, prompts_dir: Path | None = None) -> None:
        from openseo.constants import PROMPTS_DIR

        self._dir = prompts_dir or PROMPTS_DIR
        self._cache: dict[str, str] = {}

    @property
    def prompts_dir(self) -> Path:
        """Return the prompts directory path."""
        return self._dir

    def load(self, name: str) -> str:
        """
        Load a prompt by name.

        Args:
            name: Prompt name without extension (e.g., "audit")

        Returns:
            Raw prompt content as a string

        Raises:
            PromptNotFoundError: If the prompt file does not exist
        """
        if name in self._cache:
            return self._cache[name]

        path = self._dir / f"{name}.md"
        if not path.exists():
            raise PromptNotFoundError(name)

        content = path.read_text(encoding="utf-8")
        self._cache[name] = content
        logger.debug("Loaded prompt '%s' from %s", name, path)
        return content

    def list_prompts(self) -> list[str]:
        """Return a list of available prompt names."""
        if not self._dir.exists():
            return []
        return [p.stem for p in self._dir.glob("*.md") if p.is_file()]

    def reload(self, name: str) -> str:
        """Force-reload a prompt, bypassing the cache."""
        self._cache.pop(name, None)
        return self.load(name)

    def invalidate_cache(self) -> None:
        """Clear the entire prompt cache."""
        self._cache.clear()


__all__ = ["PromptLoader"]
