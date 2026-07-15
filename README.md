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

### Standard Installation

Install using `pip` or `uv`:

```bash
# Core installation
pip install openseo

# Install with all extras (includes Playwright for JavaScript rendering and developer tools)
pip install "openseo[all]"
playwright install chromium
```

### Running Locally from Source

If you want to clone and run OpenSEO from the source code locally:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/openseo/openseo.git
   cd OpenSEO
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Create environment
   python -m venv .venv

   # Activate environment (Windows PowerShell)
   .venv\Scripts\Activate.ps1

   # Activate environment (macOS/Linux)
   source .venv/bin/activate
   ```

3. **Install OpenSEO in editable mode**:
   ```bash
   # Core installation
   pip install -e .

   # Or install with all development and rendering extras
   pip install -e ".[all]"
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

## Detailed Usage Guide

### 1. Interactive Audit Wizard
If you run the audit command without a target URL, OpenSEO enters an interactive wizard:
```bash
seo audit
```
It will guide you step-by-step to customize page crawl limits, depth, sitemaps, JS rendering, AI configurations, and PDF generation.

### 2. Sitemap-Only & Unlimited Crawling
To audit **every page** declared inside your website sitemap:
```bash
# Audits only sitemap pages, with no crawl limit
seo audit https://example.com --sitemap-only --max-pages 0
```
* `--sitemap-only`: Crawls only sitemap links, skipping standard link-expansion discovery.
* `--max-pages 0`: Disables crawl page-counts limits.

### 3. Generating PDF Reports
Generate a complete, page-by-page PDF audit report with scorecard breakdowns, consolidated issues, and strategic AI roadmaps:
```bash
seo audit https://example.com --report
```
The report is automatically generated and saved inside a `results/` folder at your project root.

### 4. Running Locally with Ollama
OpenSEO integrates natively with local Ollama models (e.g. `llama3.1`, `llama3.2`, etc.) for privacy-first, free auditing:

1. Verify your local Ollama instance is running:
   ```bash
   ollama list
   ```
2. Configure OpenSEO to use Ollama:
   ```bash
   # Select ollama provider and configure the model
   seo provider use ollama --model ollama/llama3.1
   ```
3. Run the audit (make sure the model is pulled locally via `ollama pull llama3.1` first):
   ```bash
   seo audit https://example.com
   ```

### 5. Managing AI Providers & Keys
Configure credentials for various hosted API providers (OpenAI, Gemini, Claude, Groq, DeepSeek, etc.):
```bash
# List available providers
seo provider list

# Set api key for a provider
seo provider set-key openai sk-your-key-here
seo provider set-key anthropic sk-ant-your-key-here

# Switch active provider and default model
seo provider use gemini --model gemini/gemini-1.5-pro
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
