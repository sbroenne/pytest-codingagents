# Copilot Instructions for pytest-codingagents

## Build, Test & Lint Commands

```bash
# Install all dependencies (including dev and docs extras)
uv sync --all-extras

# Unit tests (fast, no credentials needed)
uv run pytest tests/unit/ -v

# Run a single unit test file
uv run pytest tests/unit/test_event_mapper.py -v

# Run a single test by name
uv run pytest tests/unit/test_result.py::test_name -v

# Integration tests (require GitHub Copilot credentials via GITHUB_TOKEN or `gh` CLI auth)
uv run pytest tests/ -v -m copilot

# Run one integration test file for a specific model
uv run pytest tests/test_basic.py -k "gpt-5.2" -v

# Lint
uv run ruff check src tests

# Format
uv run ruff format src tests

# Type check
uv run pyright src

# Multi-file integration run with per-file HTML reports
uv run python scripts/run_all.py
```

## Architecture

This is a **pytest plugin** (`pytest11` entry point) that provides a test harness for empirically validating GitHub Copilot agent configurations.

### Data Flow

```
CopilotAgent (frozen config dataclass)
  → runner.run_copilot(agent, prompt)
    → GitHub Copilot SDK client + session
      → SDK SessionEvent stream
        → EventMapper.process_event()  (38+ event types → structured data)
          → Turn / ToolCall accumulation
            → CopilotResult (turns, success, usage, reasoning, subagents)
              → copilot_run fixture stashes result for pytest-aitest
                → HTML report with AI-powered insights
```

### Key Modules (`src/pytest_codingagents/`)

| Module | Role |
|--------|------|
| `plugin.py` | Pytest plugin entry point; registers fixtures and `pytest_aitest_analysis_prompt` hook |
| `copilot/agent.py` | `CopilotAgent` frozen dataclass; `build_session_config()` maps user fields → SDK TypedDict |
| `copilot/runner.py` | `run_copilot()` — manages SDK client lifecycle, streams events, returns `CopilotResult` |
| `copilot/events.py` | `EventMapper` — translates raw SDK events into `Turn`/`ToolCall` objects |
| `copilot/result.py` | `CopilotResult`, `UsageInfo`, `SubagentInvocation`; re-exports `Turn`/`ToolCall` from `pytest_aitest` |
| `copilot/fixtures.py` | `copilot_run` and `ab_run` pytest fixtures |
| `copilot/agents.py` | `load_custom_agent()` — parses `.agent.md` YAML frontmatter files |
| `copilot/optimizer.py` | `optimize_instruction()` — uses pydantic-ai to suggest instruction improvements |
| `copilot/personas.py` | `VSCodePersona`, `ClaudeCodePersona`, `CopilotCLIPersona`, `HeadlessPersona` — inject IDE context |

### Two Core Fixtures

**`copilot_run(agent, prompt)`** — Executes a single agent run, auto-stashes result for aitest reporting.

**`ab_run(baseline_agent, treatment_agent, task)`** — Runs two agents in isolated `tmp_path` directories and returns `(baseline_result, treatment_result)` for direct comparison.

## Key Conventions

### Every module uses `from __future__ import annotations`
Required for forward references and PEP 563 deferred evaluation. Add it to every new module.

### `CopilotAgent` is a frozen dataclass
It is immutable and safe to share across parametrized tests. User-friendly field names (e.g., `instructions`) are mapped to SDK internals in `build_session_config()`. Unknown SDK fields go in `extra_config: dict`.

### Async-first
All SDK interactions are async. Test functions using `copilot_run` or `ab_run` must be `async def`. `asyncio_mode = "auto"` is set in `pyproject.toml`, so no `@pytest.mark.asyncio` decorator is needed.

### Integration tests are parametrized over models
```python
from tests.conftest import MODELS

@pytest.mark.parametrize("model", MODELS)
async def test_something(copilot_run, model):
    agent = CopilotAgent(model=model, ...)
```
`MODELS = ["gpt-5.2", "claude-opus-4.5"]` is defined in `tests/conftest.py`.

### Result introspection methods
Prefer the typed helper methods over raw field access:
- `result.success` / `result.error`
- `result.tool_was_called("create_file")` 
- `result.all_tool_calls` / `result.final_response`
- `result.file(path)` — reads a file from the agent's working directory
- `result.usage` — `UsageInfo` with token counts and estimated cost

### Personas inject IDE context post-config
Apply a persona to a `CopilotAgent` before running to simulate a specific IDE environment (e.g., `VSCodePersona` polyfills `runSubagent`). This is separate from the agent config.

### Custom agents use `.agent.md` files
YAML frontmatter + Markdown body. Parsed by `load_custom_agent(path)`. The `mode` frontmatter field controls agent type.

### Ruff rules: E, F, B, I — 100 char line length, double quotes
Enforced by pre-commit hooks and CI. Run `uv run ruff check --fix src tests` before committing.

### Pyright type checking is `basic` mode, scoped to `src/` only
Tests directory is not type-checked by pyright. Type annotations in `src/` should be complete and valid.
