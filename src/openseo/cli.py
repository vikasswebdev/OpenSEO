"""
OpenSEO CLI entry point.

This module is the `seo` command. It is kept minimal by design —
all app creation is delegated to app.py.
"""

from __future__ import annotations

import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from openseo.app import create_app

# Create the app once at module level so it can be used by tests and
# by the pyproject.toml entry point.
_app = create_app()


def main() -> None:
    """Entry point for the `seo` CLI command."""
    _app()


if __name__ == "__main__":
    main()
