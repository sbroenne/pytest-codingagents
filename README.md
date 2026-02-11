# pytest-codingagents

A pytest plugin for testing coding agents via their native SDKs.

**The agent is the test harness, not the thing being tested.** You write prompts, the agent executes them against your codebase, and the report tells you what to fix.

## Why?

Your MCP server passes all unit tests. Then a coding agent tries to use it and:

- Picks the wrong tool
- Passes garbage parameters
- Can't recover from errors
- Ignores your system prompt instructions

**Why?** Because you tested the code, not the AI interface.

## Supported Agents

| Agent | SDK | Status |
|-------|-----|--------|
| GitHub Copilot | `github-copilot-sdk` | ✅ Implemented |

## Quick Start

```bash
uv add pytest-codingagents
```

```python
from pytest_codingagents import CopilotAgent

agent = CopilotAgent(
    name="file-creator",
    instructions="Create files as requested.",
    working_directory=str(tmp_path),
)


async def test_create_file(copilot_run, tmp_path):
    result = await copilot_run(agent, "Create hello.py with print('hello')")
    assert result.success
    assert (tmp_path / "hello.py").exists()
```

## Features

### Native SDK Integration

Tests run against the real Copilot CLI — no mocks, no wrappers:

```python
agent = CopilotAgent(
    name="my-test",
    model="claude-sonnet-4",
    instructions="You are a Python expert.",
    working_directory=str(tmp_path),
    max_turns=10,
)
```

### Rich Results

```python
result = await copilot_run(agent, "Create a fibonacci function")

# Tool tracking
assert result.tool_was_called("create_file")
assert len(result.all_tool_calls) > 0

# Token usage & cost
print(result.total_tokens)
print(result.total_cost_usd)

# Reasoning traces (when available)
print(result.reasoning_traces)

# Subagent invocations
print(result.subagent_invocations)
```

### Model Comparison

```python
MODELS = ["claude-sonnet-4", "gpt-4.1"]

@pytest.mark.parametrize("model", MODELS)
async def test_fibonacci(copilot_run, tmp_path, model):
    agent = CopilotAgent(name=f"model-{model}", model=model, ...)
    result = await copilot_run(agent, "Create fibonacci.py")
    assert result.success
```

### Instruction Testing

```python
@pytest.mark.parametrize("style,instructions", [
    ("concise", "Write minimal code."),
    ("verbose", "Write well-documented code with docstrings."),
])
async def test_style(copilot_run, tmp_path, style, instructions):
    agent = CopilotAgent(name=f"style-{style}", instructions=instructions, ...)
    result = await copilot_run(agent, "Create calculator.py")
    assert result.success
```

### pytest-aitest Integration

Install with the `aitest` extra to get HTML reports with AI analysis:

```bash
uv add "pytest-codingagents[aitest]"
```

Results automatically integrate with pytest-aitest's reporting pipeline, including leaderboards, failure analysis, and AI insights.

## Configuration

### CopilotAgent Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Agent identifier for reports |
| `model` | `str \| None` | `None` | Model to use (e.g., `claude-sonnet-4`) |
| `instructions` | `str \| None` | `None` | System prompt / instructions |
| `working_directory` | `str \| None` | `None` | Working directory for file operations |
| `max_turns` | `int` | `25` | Maximum conversation turns |
| `timeout_s` | `float` | `120.0` | Timeout in seconds |
| `auto_confirm` | `bool` | `True` | Auto-approve tool permissions |
| `reasoning_effort` | `str \| None` | `None` | Reasoning effort (`low`, `medium`, `high`) |
| `allowed_tools` | `list[str] \| None` | `None` | Whitelist of allowed tools |
| `excluded_tools` | `list[str] \| None` | `None` | Blacklist of excluded tools |
| `mcp_servers` | `list[dict] \| None` | `None` | MCP server configurations |
| `custom_agents` | `list[dict] \| None` | `None` | Custom agent configurations |
| `skill_directories` | `list[str] \| None` | `None` | Paths to skill directories |
| `disabled_skills` | `list[str] \| None` | `None` | Skills to disable |

## Development

```bash
# Install in development mode
uv sync --all-extras

# Run unit tests (fast, no Copilot needed)
uv run pytest tests/unit/ -v

# Run integration tests (requires Copilot CLI)
uv run pytest tests/ -v -m copilot

# Lint
uv run ruff check src tests
uv run pyright src
```

## License

MIT
