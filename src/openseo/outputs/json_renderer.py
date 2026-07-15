"""
JSON renderer — outputs structured JSON to stdout.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from openseo.outputs.base import BaseRenderer


class JsonRenderer(BaseRenderer):
    """Renders results as pretty-printed JSON to stdout."""

    def render_audit(self, result: Any) -> None:
        """Render audit result as JSON."""
        data = result.model_dump(mode="json") if hasattr(result, "model_dump") else vars(result)
        print(json.dumps(data, indent=2, default=str))

    def render_keywords(self, result: Any) -> None:
        """Render keyword result as JSON."""
        data = result.model_dump(mode="json") if hasattr(result, "model_dump") else vars(result)
        print(json.dumps(data, indent=2, default=str))

    def render_error(self, message: str, hint: str | None = None) -> None:
        payload: dict[str, Any] = {"status": "error", "message": message}
        if hint:
            payload["hint"] = hint
        print(json.dumps(payload, indent=2), file=sys.stderr)

    def render_success(self, message: str) -> None:
        print(json.dumps({"status": "ok", "message": message}, indent=2))

    def render_info(self, message: str) -> None:
        print(json.dumps({"status": "info", "message": message}, indent=2))


__all__ = ["JsonRenderer"]
