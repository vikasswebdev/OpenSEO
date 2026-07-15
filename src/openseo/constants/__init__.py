"""
App-wide constants for OpenSEO.

Keep all magic numbers and fixed strings here.
"""

from __future__ import annotations

from pathlib import Path

# ─── Application Identity ──────────────────────────────────────────────────────

APP_NAME = "openseo"
CLI_NAME = "seo"
APP_DISPLAY_NAME = "OpenSEO"
APP_DESCRIPTION = "Production-quality SEO CLI powered by any LLM"
HOMEPAGE = "https://github.com/openseo/openseo"

# ─── Filesystem ───────────────────────────────────────────────────────────────

CONFIG_DIR: Path = Path.home() / ".openseo"
CONFIG_FILE: Path = CONFIG_DIR / "config.json"
CACHE_DIR: Path = CONFIG_DIR / "cache"
CACHE_DB: Path = CACHE_DIR / "cache.db"
LOGS_DIR: Path = CONFIG_DIR / "logs"
PLUGINS_DIR: Path = CONFIG_DIR / "plugins"

# Built-in prompts directory (shipped with package)
PROMPTS_DIR: Path = Path(__file__).parent.parent / "prompts"
if not (PROMPTS_DIR / "audit.md").exists():
    _repo_prompts = Path(__file__).parent.parent.parent.parent / "prompts"
    if (_repo_prompts / "audit.md").exists():
        PROMPTS_DIR = _repo_prompts

# ─── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.2

# ─── HTTP / Crawler ───────────────────────────────────────────────────────────

USER_AGENT = (
    "Mozilla/5.0 (compatible; OpenSEO/0.1; +https://github.com/openseo/openseo)"
)
CRAWLER_TIMEOUT = 20  # seconds
MAX_REDIRECTS = 10
MAX_PAGE_SIZE = 10 * 1024 * 1024  # 10 MB

# ─── SEO Thresholds ───────────────────────────────────────────────────────────

TITLE_MIN_LENGTH = 30
TITLE_MAX_LENGTH = 60
META_DESC_MIN_LENGTH = 70
META_DESC_MAX_LENGTH = 160
H1_IDEAL_COUNT = 1

# ─── Output ───────────────────────────────────────────────────────────────────

SUPPORTED_OUTPUT_FORMATS = ("terminal", "markdown", "json")
DEFAULT_OUTPUT_FORMAT = "terminal"

# ─── Providers ────────────────────────────────────────────────────────────────

KNOWN_PROVIDERS: dict[str, str] = {
    "openai": "OpenAI",
    "anthropic": "Anthropic Claude",
    "gemini": "Google Gemini",
    "groq": "Groq",
    "openrouter": "OpenRouter",
    "ollama": "Ollama (local)",
    "deepseek": "DeepSeek",
    "together": "Together AI",
    "fireworks": "Fireworks AI",
}

PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-20241022",
    "gemini": "gemini/gemini-1.5-flash",
    "groq": "groq/llama-3.1-8b-instant",
    "openrouter": "openrouter/google/gemma-3-12b-it:free",
    "ollama": "ollama/llama3.2",
    "deepseek": "deepseek/deepseek-chat",
    "together": "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "fireworks": "fireworks_ai/accounts/fireworks/models/llama-v3p1-8b-instruct",
}

# ─── Issue Severity ───────────────────────────────────────────────────────────

SEVERITY_CRITICAL = "critical"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"
SEVERITY_PASS = "pass"

SEVERITY_COLORS: dict[str, str] = {
    SEVERITY_CRITICAL: "red",
    SEVERITY_WARNING: "yellow",
    SEVERITY_INFO: "blue",
    SEVERITY_PASS: "green",
}

SEVERITY_ICONS: dict[str, str] = {
    SEVERITY_CRITICAL: "✗",
    SEVERITY_WARNING: "⚠",
    SEVERITY_INFO: "ℹ",
    SEVERITY_PASS: "✓",
}

__all__ = [
    "APP_NAME",
    "CLI_NAME",
    "APP_DISPLAY_NAME",
    "APP_DESCRIPTION",
    "HOMEPAGE",
    "CONFIG_DIR",
    "CONFIG_FILE",
    "CACHE_DIR",
    "CACHE_DB",
    "LOGS_DIR",
    "PLUGINS_DIR",
    "PROMPTS_DIR",
    "DEFAULT_PROVIDER",
    "DEFAULT_MODEL",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_CACHE_TTL",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_TEMPERATURE",
    "USER_AGENT",
    "CRAWLER_TIMEOUT",
    "MAX_REDIRECTS",
    "MAX_PAGE_SIZE",
    "TITLE_MIN_LENGTH",
    "TITLE_MAX_LENGTH",
    "META_DESC_MIN_LENGTH",
    "META_DESC_MAX_LENGTH",
    "H1_IDEAL_COUNT",
    "SUPPORTED_OUTPUT_FORMATS",
    "DEFAULT_OUTPUT_FORMAT",
    "KNOWN_PROVIDERS",
    "PROVIDER_DEFAULT_MODELS",
    "SEVERITY_CRITICAL",
    "SEVERITY_WARNING",
    "SEVERITY_INFO",
    "SEVERITY_PASS",
    "SEVERITY_COLORS",
    "SEVERITY_ICONS",
]
