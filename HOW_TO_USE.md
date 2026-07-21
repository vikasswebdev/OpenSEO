# OpenSEO CLI Documentation & Usage Guide 🔍

OpenSEO is a production-quality, provider-agnostic command-line tool built to help developers, marketers, and SEO professionals audit, analyze, and monitor search engine visibility using Large Language Models (LLMs) and local diagnostic checks.

---

## 🚀 Installation & Local Setup

### 1. Standard Virtual Environment setup
If you are developing locally from the source, create and activate a virtual environment:

```powershell
# Create environment
python -m venv .venv

# Activate environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate environment (macOS/Linux)
source .venv/bin/activate
```

### 2. Install OpenSEO in Editable Mode (Required for development)
To ensure the `seo` CLI command references your local workspace changes (`src/` directory), install the package in **editable mode**:

```bash
pip install -e ".[all]"
```
*(Optionally run `playwright install chromium` if you wish to use javascript rendering features)*

---

## 🛠 Command Reference & Usage

Run `seo --help` to see all available commands. Below is a detailed breakdown of each command and how to use it:

---

### 1. Setup & Diagnostics

#### `seo init`
Initializes OpenSEO with an interactive setup wizard that guides you through selecting default providers, models, caches, and output directory paths. Configurations are stored globally in `~/.openseo/config.json`.

```bash
seo init
```

#### `seo doctor`
Runs a health check on your environment to verify API keys, cache database status, playwritght dependencies, and internet connectivity.

```bash
seo doctor
```

#### `seo provider`
Lists available LLM providers, sets API credentials, and overrides default models.

```bash
# List all providers
seo provider list

# Set API key for a provider
seo provider set-key openai sk-proj-...
seo provider set-key gemini AIzaSy...

# Set active provider and model
seo provider use gemini --model gemini/gemini-1.5-flash
```

---

### 2. Analysis & Auditing

#### `seo audit`
Crawls a website and runs rule-based technical checks combined with LLM analysis.

```bash
# Run a quick audit on a single URL
seo audit https://example.com

# Audit pages found in the sitemap index with custom depth
seo audit https://example.com --sitemap-only --max-pages 20

# Generate a complete PDF scorecard report inside the results/ folder
seo audit https://example.com --report
```

#### `seo content`
Analyzes content relevance against target keywords, checks search experience guidelines, and performs NLP/QRG diagnostics.

```bash
# Run LLM-based content keyword gap audit
seo content https://example.com/blog/python-tutorial --keyword "python tutorial"

# Run local Quality Rater Guidelines (QRG) checks (AI pattern, filler, repetition)
seo content https://example.com/blog/python-tutorial --quality
```

#### `seo schema`
Generates structured Schema.org JSON-LD blocks for search eligibility.

```bash
# Generate schema recommendations using page crawling + LLM analysis
seo schema https://example.com/blog/post --type article

# Interactively generate predefined high-leverage schema templates
seo schema --template profile
seo schema --template discussion
seo schema --template order
seo schema --template reservation
```

---

### 3. SEO Drift & Regression Monitoring (`seo drift`)

Allows capturing a technical baseline state of page structures and comparing current states to check for unintended deployments/code regressions (e.g., losing noindex directives, removing canonical tags, or deleting Schema).

#### Capture a Baseline Snapshot
```bash
seo drift baseline https://example.com/pricing
```

#### Compare Current State to Baseline
```bash
# Compare against the latest captured baseline
seo drift compare https://example.com/pricing

# Compare against a specific baseline ID
seo drift compare https://example.com/pricing --baseline-id 4

# Output diff results as raw JSON
seo drift compare https://example.com/pricing -o json
```

#### View Drift History
```bash
seo drift history https://example.com/pricing
```

#### Generate HTML Drift Reports
```bash
# Creates a self-contained color-coded HTML report (seo-drift-report.html)
seo drift report https://example.com/pricing
```

---

### 4. Utilities

- `seo sitemap <url>`: Fetches and parses standard XML sitemaps to check schema compliance.
- `seo robots <url>`: Audits site `robots.txt` configuration and maps user-agent blocks.
- `seo keywords <topic>`: Generates keyword clustering and search-intent outlines.
