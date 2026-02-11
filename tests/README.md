# Integration Tests

These tests verify that pytest-codingagents correctly drives the GitHub Copilot SDK
against real coding tasks. Every test uses the actual Copilot API — no mocks.

## Test Matrix

| File | What It Tests | Models | Tests |
|------|---------------|--------|-------|
| `test_basic.py` | File creation, code quality, refactoring | `gpt-5.2`, `claude-opus-4.5` | 4 |
| `test_models.py` | Model comparison on identical tasks | `gpt-5.2`, `claude-opus-4.5` | 4 |
| `test_matrix.py` | Model × Instructions grid | `gpt-5.2`, `claude-opus-4.5` | 4 |
| `test_instructions.py` | System prompt style comparison, constraints | default | 4 |
| `test_cli_tools.py` | Terminal commands, git, tool exclusion | default | 4 |
| `test_custom_agents.py` | Custom agent routing, subagent tracking | default | 2 |
| `test_events.py` | Reasoning traces, permissions, usage, events | default | 6 |
| `test_skills.py` | Skill directories, disabled skills | default | 3 |

**Total: 31 test cases**

## Quick Start

```bash
# Run a single test (cheapest way to verify setup)
uv run pytest tests/test_basic.py::TestFileOperations::test_create_module_with_tests -k "gpt-5.2" -v

# Run all tests
uv run pytest tests/ -v

# Run only failed tests from last run
uv run pytest --lf tests/
```

## Prerequisites

- GitHub Copilot SDK credentials (agent sidecar running)
- `uv sync` to install dependencies

## Test Descriptions

### test_basic.py — Core File Operations

Parametrized across `MODELS` from `conftest.py`.

- **`test_create_module_with_tests`** — Create `calculator.py` with `add`, `subtract`,
  `multiply`, `divide`. Verifies all functions exist and `ValueError` handling is present.
- **`test_refactor_existing_code`** — Seed a messy file, ask agent to refactor. Verifies
  at least one improvement (renamed function, docstring, or type hints).

### test_models.py — Model Comparison

Same tasks, different models. Parametrized across `MODELS`.

- **`test_simple_function`** — Create `fibonacci.py` with `fibonacci(n)`.
- **`test_error_handling`** — Create `parser.py` with `FileNotFoundError` /
  `JSONDecodeError` handling.

### test_matrix.py — Model × Instructions Grid

Cross-product of 2 models × 2 instruction styles (minimal, detailed).

- **`test_create_utility`** — Create `string_utils.py` with `reverse`,
  `capitalize_words`, `count_vowels`. Every combination must produce working code.

### test_instructions.py — System Prompt Testing

Compares instruction variants and constraints.

- **`test_style_produces_code`** — Concise vs verbose instructions both create valid code.
- **`test_restricted_tools`** — Agent respects tool exclusion.
- **`test_domain_specific_instructions`** — FastAPI expert instructions produce correct
  framework choice.

### test_cli_tools.py — CLI Tool Testing

Verifies agents can operate terminal commands.

- **`test_run_python_script`** — Create and run a Python script; verify `run_in_terminal` called.
- **`test_use_git_cli`** — `git init`, `.gitignore`, initial commit.
- **`test_cli_tool_output_captured`** — Run command, process output, report findings.
- **`test_no_terminal_when_excluded`** — `excluded_tools=["run_in_terminal"]` prevents usage.

### test_custom_agents.py — Custom Agent / Subagent

- **`test_with_custom_agent`** — Agent with `custom_agents` config creates files.
- **`test_subagent_invocations_tracked`** — `result.subagent_invocations` is populated.

### test_events.py — SDK-Unique Features

Features that only exist in the Copilot SDK, not in generic AI testing.

- **`test_reasoning_captured`** — `reasoning_effort="high"` produces reasoning traces.
- **`test_auto_confirm_permissions`** — `auto_confirm=True` auto-approves tool use.
- **`test_usage_info_captured`** — Token usage tracked from SDK events.
- **`test_token_usage_dict`** — `result.token_usage` returns aitest-compatible dict.
- **`test_raw_events_populated`** — All SDK events captured in `result.raw_events`.
- **`test_excluded_tools`** — Tool exclusion verified at SDK level.

### test_skills.py — Skill Directories

- **`test_skill_loaded`** — Skill markdown loaded, influences code quality (type hints).
- **`test_without_skill`** — No skill baseline for comparison.
- **`test_disabled_skill_not_used`** — `disabled_skills` prevents loading.

## Constants (`conftest.py`)

```python
DEFAULT_MODEL: str | None = None    # Copilot picks its default
MODELS = ["gpt-5.2", "claude-opus-4.5"]
DEFAULT_TIMEOUT_S = 120.0
DEFAULT_MAX_TURNS = 25
```

## Adding New Tests

```python
from pytest_codingagents.copilot.agent import CopilotAgent
from .conftest import MODELS

@pytest.mark.copilot
class TestMyFeature:
    @pytest.mark.parametrize("model", MODELS)
    async def test_something(self, copilot_run, tmp_path, model):
        agent = CopilotAgent(
            name=f"my-agent-{model}",
            model=model,
            instructions="Your instructions here.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(agent, "Do something useful.")
        assert result.success
```
