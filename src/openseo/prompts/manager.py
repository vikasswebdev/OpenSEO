"""
PromptManager — loads prompts and performs variable interpolation.
"""

from __future__ import annotations

import re
import logging
from pathlib import Path

from openseo.prompts.loader import PromptLoader

logger = logging.getLogger(__name__)

# Template variable pattern: {{variable_name}}
_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")


class PromptManager:
    """
    Manages prompt loading and rendering with variable substitution.

    Variables in prompts use {{variable_name}} syntax.

    Example:
        manager = PromptManager()
        prompt = manager.render("audit", url="https://example.com", title="Example")
    """

    def __init__(self, prompts_dir: Path | None = None) -> None:
        self._loader = PromptLoader(prompts_dir)

    def load(self, name: str) -> str:
        """Load a raw prompt without variable substitution."""
        return self._loader.load(name)

    def render(self, name: str, **variables: str | int | float | None) -> str:
        """
        Load a prompt and substitute template variables.

        Args:
            name: Prompt name (e.g., "audit")
            **variables: Variables to substitute into the prompt

        Returns:
            Rendered prompt string with all variables replaced

        Raises:
            PromptNotFoundError: If the prompt file does not exist
        """
        template = self._loader.load(name)
        rendered = self._substitute(template, variables)
        logger.debug(
            "Rendered prompt '%s' with variables: %s",
            name,
            list(variables.keys()),
        )
        return rendered

    def list_prompts(self) -> list[str]:
        """Return available prompt names."""
        return self._loader.list_prompts()

    def list_variables(self, name: str) -> list[str]:
        """Return all variable names used in a prompt."""
        template = self._loader.load(name)
        return list({m.group(1) for m in _VAR_PATTERN.finditer(template)})

    @staticmethod
    def _substitute(template: str, variables: dict[str, str | int | float | None]) -> str:
        """Replace {{key}} placeholders with values."""

        def replacer(match: re.Match) -> str:
            key = match.group(1)
            if key in variables:
                return str(variables[key] or "")
            logger.warning("Prompt variable '{{%s}}' not provided", key)
            return match.group(0)  # Leave unreplaced

        return _VAR_PATTERN.sub(replacer, template)


__all__ = ["PromptManager"]
