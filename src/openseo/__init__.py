"""
OpenSEO — Production-quality SEO CLI powered by any LLM.

This is the main package entry point.
"""

from importlib.metadata import PackageNotFoundError, version

__app_name__ = "openseo"
__cli_name__ = "seo"

try:
    __version__ = version(__app_name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0-dev"

__all__ = ["__app_name__", "__cli_name__", "__version__"]
