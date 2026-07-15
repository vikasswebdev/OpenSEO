# OpenSEO 🔍

[![PyPI version](https://img.shields.io/pypi/v/openseo.svg)](https://pypi.org/project/openseo/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/openseo.svg)](https://pypi.org/project/openseo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

OpenSEO is a production-quality, provider-agnostic, plugin-ready command-line tool built to help developers, marketers, and SEO professionals audit, analyze, and optimize search engine visibility using Large Language Models (LLMs).

Unlike other SEO auditing tools, OpenSEO **never** locks you into a single provider. With integration via LiteLLM, you can use OpenAI, Anthropic Claude, Google Gemini, Groq, Ollama, DeepSeek, Together AI, Fireworks, or any OpenAI-compatible endpoint with one unified interface.

---

## Key Features

- 🛠 **Full SEO Audit**: Combines rules-based HTML parsing with LLM-powered recommendations.
- 💡 **AI Provider-Agnostic**: Change providers or models seamlessly via commands or configs.
- 📂 **No Hardcoded Prompts**: Prompts are stored as dynamic Markdown templates, easy to edit and extend.
- 🧩 **Plugin Architecture**: Write and load custom commands, providers, and logic easily.
- ⚡ **SQLite Caching**: Zero-configuration, local caching with customizable TTL to avoid repeating API calls.
- 💻 **Beautiful UI**: Highly polished terminal UI with tables, trees, scoring, and progress bars powered by Rich.
- 🔒 **Privacy-First / local**: Supports local LLM endpoints like Ollama out-of-the-box.

---

## Installation

Install using `pip` or `uv`:

```bash
# Core installation
pip install openseo

# Install with all extras (includes Playwright for JavaScript rendering and developer tools)
pip install "openseo[all]"
playwright install chromium
```

---

## Quick Start

1. **Initialize configuration**:
   ```bash
   seo init
   ```
   This interactive wizard will help you set up your default provider and configurations at `~/.openseo/config.json`.

2. **Configure your API keys**:
   ```bash
   # Set key in config
   seo provider set-key openai sk-...
   
   # Or set environment variables (recommended)
   export OPENAI_API_KEY="sk-..."
   ```

3. **Verify installation**:
   ```bash
   seo doctor
   ```

4. **Run your first audit**:
   ```bash
   seo audit https://example.com
   ```

---

## Architecture Overview

OpenSEO is designed with clean architecture and modular SOLID principles:

```
src/openseo/
├── cli.py             # Entry point
├── app.py             # App bootstrap
├── commands/          # Isolated Typer command modules
├── providers/         # Provider adapters (OpenAI, Claude, etc.)
├── crawler/           # Page crawlers (Http, Playwright) & Extractor
├── analyzers/         # Independent SEO checks (Title, Image, Links)
├── prompts/           # PromptManager & Markdown Prompt templates
├── outputs/           # Output renderers (Terminal, JSON, Markdown)
├── cache/             # SQLite key-value cache
└── services/          # Unified LLMService
```

---

## Contributing

We welcome contributions of all forms! Check out [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
