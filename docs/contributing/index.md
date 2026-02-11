# Contributing

## Development Setup

```bash
git clone https://github.com/sbroenne/pytest-codingagents.git
cd pytest-codingagents
uv sync --all-extras
```

## Running Tests

```bash
# Unit tests (fast, no Copilot needed)
uv run pytest tests/unit/ -v

# Integration tests (requires Copilot CLI + auth)
uv run pytest tests/ -v -m copilot
```

## Code Quality

```bash
# Lint
uv run ruff check src tests

# Format
uv run ruff format src tests

# Type check
uv run pyright src
```

Pre-commit hooks run automatically on `git commit`.

## Project Structure

```
src/pytest_codingagents/
├── __init__.py              # Public API exports
├── plugin.py                # pytest plugin entry point
└── copilot/
    ├── __init__.py          # Copilot subpackage exports
    ├── agent.py             # CopilotAgent dataclass
    ├── result.py            # CopilotResult, Turn, ToolCall
    ├── events.py            # EventMapper (SDK event → result)
    ├── runner.py            # run_copilot() execution engine
    └── fixtures.py          # copilot_run fixture + aitest bridge
```
