# pytest-codingagents

A pytest plugin for testing coding agents via their native SDKs.

You give a coding agent a task. Did it pick the right tools? Did it produce working code? Did it follow your instructions? **pytest-codingagents lets you answer these questions with automated tests.**

## Why?

You're rolling out GitHub Copilot to your team. But which model actually works best for your codebase? Do your custom instructions improve output quality? Does the agent use your MCP tools correctly?

You can't answer these questions by trying things manually. You need **repeatable, automated tests** that:

- Run the real agent against real tasks
- Assert on tool usage, file creation, and response quality
- Compare models and instructions side-by-side
- Track token costs and performance over time

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


async def test_create_file(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Create files as requested.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create hello.py with print('hello')")
    assert result.success
    assert result.tool_was_called("create_file")
    assert (tmp_path / "hello.py").exists()
```

## Authentication

The plugin authenticates with GitHub Copilot in this order:

1. **`GITHUB_TOKEN` env var** — ideal for CI (set via `gh auth token` or a GitHub Actions secret)
2. **Logged-in user** via `gh` CLI / OAuth — works automatically for local development

```bash
# CI: set the token in your workflow
export GITHUB_TOKEN=$(gh auth token)

# Local: just make sure you're logged into gh CLI
gh auth status
```

## Features

### Native SDK Integration

Tests run against the real Copilot CLI — no mocks, no wrappers:

```python
async def test_review(copilot_run, tmp_path):
    agent = CopilotAgent(
        name="reviewer",
        model="claude-sonnet-4",
        instructions="You are a Python code reviewer.",
        working_directory=str(tmp_path),
        max_turns=10,
    )
    result = await copilot_run(agent, "Review main.py for bugs")
    assert result.success
```

### Rich Results

Every execution returns a `CopilotResult` with full observability:

```python
result = await copilot_run(agent, "Create a fibonacci function")

# Tool tracking
assert result.tool_was_called("create_file")
assert result.tool_call_count("create_file") == 1
assert len(result.all_tool_calls) > 0
print(result.tool_names_called)  # {"create_file", "read_file"}

# Final response
print(result.final_response)

# Token usage & cost
print(result.total_tokens)       # input + output
print(result.total_cost_usd)     # aggregated across all turns

# Reasoning traces (when available)
print(result.reasoning_traces)

# Subagent invocations
print(result.subagent_invocations)

# Model actually used
print(result.model_used)

# Duration
print(f"{result.duration_ms:.0f}ms")
```

### Model Comparison

```python
import pytest
from pytest_codingagents import CopilotAgent

MODELS = ["claude-sonnet-4", "gpt-4.1"]

@pytest.mark.parametrize("model", MODELS)
async def test_fibonacci(copilot_run, tmp_path, model):
    agent = CopilotAgent(
        name=f"model-{model}",
        model=model,
        instructions="Create files as requested.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create fibonacci.py")
    assert result.success
```

### Instruction Testing

```python
import pytest
from pytest_codingagents import CopilotAgent

@pytest.mark.parametrize("style,instructions", [
    ("concise", "Write minimal code, no comments."),
    ("verbose", "Write well-documented code with docstrings."),
])
async def test_coding_style(copilot_run, tmp_path, style, instructions):
    agent = CopilotAgent(
        name=f"style-{style}",
        instructions=instructions,
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create calculator.py with add/subtract")
    assert result.success
```

### MCP Server Testing

Attach MCP servers to test how Copilot uses your custom tools:

```python
async def test_with_mcp_server(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Use the database tools to answer questions.",
        working_directory=str(tmp_path),
        mcp_servers={
            "my-db-server": {
                "command": "python",
                "args": ["-m", "my_db_mcp_server"],
            }
        },
    )
    result = await copilot_run(agent, "List all users in the database")
    assert result.success
    assert result.tool_was_called("list_users")
```

### Tool Control

Restrict which tools the agent can use:

```python
# Only allow specific tools
agent = CopilotAgent(
    instructions="Create files only.",
    allowed_tools=["create_file", "read_file"],
)

# Block specific tools
agent = CopilotAgent(
    instructions="Review code without modifying it.",
    excluded_tools=["create_file", "replace_string_in_file"],
)
```

### pytest-aitest Integration

Install with the `aitest` extra to get HTML reports with AI analysis:

```bash
uv add "pytest-codingagents[aitest]"
```

Results automatically integrate with pytest-aitest's reporting pipeline. The `copilot_run` fixture stashes results in a format compatible with pytest-aitest, giving you leaderboards, failure analysis, Mermaid diagrams, and AI insights — for free.

## Configuration

### CopilotAgent Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | `"copilot"` | Agent identifier for reports |
| `model` | `str \| None` | `None` | Model to use (e.g., `claude-sonnet-4`) |
| `reasoning_effort` | `Literal["low", "medium", "high", "xhigh"] \| None` | `None` | Reasoning effort level |
| `instructions` | `str \| None` | `None` | System prompt / instructions |
| `system_message_mode` | `Literal["append", "replace"]` | `"append"` | How instructions are applied |
| `working_directory` | `str \| None` | `None` | Working directory for file operations |
| `allowed_tools` | `list[str] \| None` | `None` | Allowlist of tools (None = all) |
| `excluded_tools` | `list[str] \| None` | `None` | Blocklist of tools |
| `max_turns` | `int` | `25` | Maximum conversation turns |
| `timeout_s` | `float` | `120.0` | Timeout in seconds |
| `auto_confirm` | `bool` | `True` | Auto-approve tool permissions |
| `mcp_servers` | `dict[str, Any]` | `{}` | MCP server configurations |
| `custom_agents` | `list[dict[str, Any]]` | `[]` | Custom sub-agent configurations |
| `skill_directories` | `list[str]` | `[]` | Paths to skill directories |
| `disabled_skills` | `list[str]` | `[]` | Skills to disable |
| `extra_config` | `dict[str, Any]` | `{}` | SDK passthrough for unmapped fields |

### CopilotResult Properties

| Property | Type | Description |
|----------|------|-------------|
| `success` | `bool` | Whether execution completed without errors |
| `error` | `str \| None` | Error message if failed |
| `final_response` | `str \| None` | Last assistant message |
| `all_responses` | `list[str]` | All assistant messages |
| `all_tool_calls` | `list[ToolCall]` | All tool calls across all turns |
| `tool_names_called` | `set[str]` | Set of tool names used |
| `tool_was_called(name)` | `bool` | Check if a specific tool was called |
| `tool_call_count(name)` | `int` | Count calls to a specific tool |
| `tool_calls_for(name)` | `list[ToolCall]` | All calls to a specific tool |
| `total_tokens` | `int` | Total tokens (input + output) |
| `total_input_tokens` | `int` | Total input tokens |
| `total_output_tokens` | `int` | Total output tokens |
| `total_cost_usd` | `float` | Total cost in USD |
| `reasoning_traces` | `list[str]` | Captured reasoning traces |
| `subagent_invocations` | `list[SubagentInvocation]` | Subagent delegations |
| `model_used` | `str \| None` | Model actually used |
| `duration_ms` | `float` | Execution duration in milliseconds |
| `permission_requested` | `bool` | Whether permissions were requested |

## Development

```bash
# Install in development mode
uv sync --all-extras

# Run unit tests (fast, no Copilot needed)
uv run pytest tests/unit/ -v

# Run integration tests (requires Copilot credentials)
uv run pytest tests/ -v -m copilot

# Lint & type check
uv run ruff check src tests
uv run pyright src
```

## License

MIT
