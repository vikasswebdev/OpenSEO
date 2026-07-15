# Contributing to OpenSEO

First off, thank you for taking the time to contribute! OpenSEO is built to be a community-driven tool, and your help is highly appreciated.

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/openseo/openseo.git
   cd openseo
   ```

2. **Set up virtual environment & dependencies**:
   We recommend using `uv` for lightning-fast environment setup:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[all]"
   ```

3. **Install Playwright**:
   ```bash
   playwright install chromium
   ```

## Development Workflow

### Coding Standards
- **Typing**: 100% typed. All functions must have type hints. Run `mypy` to verify.
- **Style**: We use `ruff` for linting and formatting.
- **Composition**: Prefer composition over inheritance. Keep modules small and highly focused.
- **No Monoliths**: Commands, analyzers, and outputs must be kept in their respective folders and follow the abstraction contracts.

### Verification and Quality Checks
Before submitting a PR, make sure your code passes formatting, type checks, and tests:

```bash
# Run Ruff linting and formatting
ruff check src/ tests/
ruff format src/ tests/

# Run type checker
mypy src/

# Run tests
pytest tests/
```

## Adding a New CLI Command
1. Create a new module in `src/openseo/commands/<command_name>.py`.
2. Implement the command function using `typer`.
3. Expose a `register(app: typer.Typer)` function to add it to the main Typer application.
4. Import and call the registration in `src/openseo/app.py`.

## Adding a New Analyzer
1. Add your analyzer function in `src/openseo/analyzers/`. It must accept a `Page` model and return a tuple of `(list[Issue], float)`.
2. Expose it in `src/openseo/analyzers/__init__.py`.
3. Call it in `src/openseo/commands/audit.py` to incorporate it into the main audit scoring.
