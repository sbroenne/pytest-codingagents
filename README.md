# pytest-codingagents

A pytest plugin for testing coding agents via their native SDKs.

You give a coding agent a task. Did it pick the right tools? Did it produce working code? Did it follow your instructions? **pytest-codingagents lets you answer these questions with automated tests.**

## Why?

You're rolling out GitHub Copilot to your team. But which model works best for your codebase? Do your custom instructions improve quality? Does the agent use your MCP servers correctly? Can it operate your CLI tools? Do your custom agents and skills actually help?

You can't answer these questions by trying things manually. You need **repeatable, automated tests** that evaluate:

- **Instructions** — Do your custom instructions produce the desired behavior?
- **MCP Servers** — Can the agent discover and use your custom tools?
- **CLI Tools** — Can the agent operate command-line interfaces correctly?
- **Custom Agents** — Do your sub-agents handle delegated tasks?
- **Skills** — Does domain knowledge improve agent performance?
- **Models** — Which model works best for your use case and budget?

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

### Skill Testing

Provide domain knowledge via skill directories and test whether it improves agent behavior:

```python
async def test_with_coding_standards(copilot_run, tmp_path):
    # Create a skill with coding standards
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    (skill_dir / "coding-standards.md").write_text(
        "# Coding Standards\n\n"
        "All Python functions MUST have type hints and docstrings.\n"
    )

    agent = CopilotAgent(
        name="with-skill",
        instructions="Follow all coding standards from your skills.",
        working_directory=str(tmp_path),
        skill_directories=[str(skill_dir)],
    )
    result = await copilot_run(agent, "Create math_utils.py with add and multiply")
    assert result.success
    content = (tmp_path / "math_utils.py").read_text()
    assert "def add" in content
```

Compare with and without skills to measure their impact:

```python
@pytest.mark.parametrize("use_skill", [True, False])
async def test_skill_impact(copilot_run, tmp_path, use_skill):
    skill_dirs = [str(tmp_path / "skills")] if use_skill else []
    agent = CopilotAgent(
        name=f"skill-{'on' if use_skill else 'off'}",
        skill_directories=skill_dirs,
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create a utility module")
    assert result.success
```

### CLI Tool Testing

Test that the agent can operate command-line tools:

```python
async def test_git_operations(copilot_run, tmp_path):
    agent = CopilotAgent(
        name="git-operator",
        instructions="Use git commands as requested.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(
        agent,
        "Initialize a git repo, create a .gitignore for Python, and make an initial commit.",
    )
    assert result.success
    assert (tmp_path / ".git").is_dir()
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

> **See it in action:** [Basic Report](https://sbroenne.github.io/pytest-codingagents/demo/basic-report.html) · [Model Comparison](https://sbroenne.github.io/pytest-codingagents/demo/model-comparison-report.html) · [Instruction Testing](https://sbroenne.github.io/pytest-codingagents/demo/instruction-testing-report.html)

Install with the `aitest` extra to get HTML reports with AI analysis:

```bash
uv add "pytest-codingagents[aitest]"
```

Results automatically integrate with pytest-aitest's reporting pipeline. The `copilot_run` fixture stashes results in a format compatible with pytest-aitest, giving you leaderboards, failure analysis, Mermaid diagrams, and AI insights — for free.

To generate reports with AI-powered analysis, pass `--aitest-summary-model` and `--aitest-html`:

```bash
# Run tests and generate an HTML report with AI insights
uv run pytest tests/ -m copilot \
    --aitest-html=report.html \
    --aitest-summary-model=azure/gpt-5.2-chat
```

Or configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = """
    --aitest-html=aitest-reports/report.html
    --aitest-summary-model=azure/gpt-5.2-chat
"""
```

## Configuration

### CopilotAgent Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | `"copilot"` | Agent identifier for reports |
| `model` | `str \| None` | `None` | Model to use (e.g., `claude-sonnet-4`) |
| `reasoning_effort` | `Literal["low", "medium", "high", "xhigh"] \| None` | `None` | Reasoning effort level |
| `instructions` | `str \| None` | `None` | Instructions for the agent (maps to SDK `system_message.content`) |
| `system_message_mode` | `Literal["append", "replace"]` | `"append"` | `"append"` adds to Copilot's built-in system message; `"replace"` overrides it entirely (removes SDK guardrails) |
| `working_directory` | `str \| None` | `None` | Working directory for file operations |
| `allowed_tools` | `list[str] \| None` | `None` | Allowlist of tools (None = all) |
| `excluded_tools` | `list[str] \| None` | `None` | Blocklist of tools |
| `max_turns` | `int` | `25` | Maximum conversation turns (informational — enforced via `timeout_s`, not in SDK) |
| `timeout_s` | `float` | `300.0` | Timeout in seconds |
| `auto_confirm` | `bool` | `True` | Auto-approve tool permissions |
| `mcp_servers` | `dict[str, Any]` | `{}` | MCP server configurations |
| `custom_agents` | `list[dict[str, Any]]` | `[]` | Custom sub-agent configurations |
| `skill_directories` | `list[str]` | `[]` | Paths to skill directories |
| `disabled_skills` | `list[str]` | `[]` | Skills to disable |
| `extra_config` | `dict[str, Any]` | `{}` | SDK passthrough for unmapped fields |

### CopilotResult

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether execution completed without errors |
| `error` | `str \| None` | Error message if failed |
| `model_used` | `str \| None` | Model actually used by Copilot |
| `duration_ms` | `float` | Execution duration in milliseconds |
| `turns` | `list[Turn]` | All conversation turns |
| `usage` | `list[UsageInfo]` | Per-turn token usage and cost |
| `reasoning_traces` | `list[str]` | Captured reasoning traces |
| `subagent_invocations` | `list[SubagentInvocation]` | Subagent delegations |
| `permission_requested` | `bool` | Whether any permissions were requested |
| `permissions` | `list[dict]` | Permission requests made during execution |
| `raw_events` | `list[Any]` | All raw SDK events (for debugging) |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `final_response` | `str \| None` | Last assistant message |
| `all_responses` | `list[str]` | All assistant messages |
| `all_tool_calls` | `list[ToolCall]` | All tool calls across all turns |
| `tool_names_called` | `set[str]` | Set of tool names used |
| `total_tokens` | `int` | Total tokens (input + output) |
| `total_input_tokens` | `int` | Total input tokens |
| `total_output_tokens` | `int` | Total output tokens |
| `total_cost_usd` | `float` | Total cost in USD |
| `cost_usd` | `float` | Alias for `total_cost_usd` (pytest-aitest compat) |
| `token_usage` | `dict[str, int]` | Token counts dict (pytest-aitest compat) |

#### Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `tool_was_called(name)` | `bool` | Check if a specific tool was called |
| `tool_call_count(name)` | `int` | Count calls to a specific tool |
| `tool_calls_for(name)` | `list[ToolCall]` | All calls to a specific tool |

### Turn

Represents a single conversation turn (assistant response + tool calls).

| Field | Type | Description |
|-------|------|-------------|
| `role` | `str` | Turn role (`"assistant"`, `"user"`, `"tool"`) |
| `content` | `str` | Text content |
| `tool_calls` | `list[ToolCall]` | Tool calls made in this turn |

### ToolCall

Represents a single tool invocation.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Tool name (e.g., `"create_file"`) |
| `arguments` | `dict[str, Any] \| str` | Arguments passed to the tool |
| `result` | `str \| None` | Tool result (if captured) |
| `error` | `str \| None` | Error message (if tool failed) |
| `duration_ms` | `float \| None` | Tool execution duration |
| `tool_call_id` | `str \| None` | SDK tool call identifier |

### UsageInfo

Token usage and cost for a single LLM call.

| Field | Type | Description |
|-------|------|-------------|
| `model` | `str` | Model used for this call |
| `input_tokens` | `int` | Input tokens |
| `output_tokens` | `int` | Output tokens |
| `cache_read_tokens` | `int` | Cached input tokens |
| `cost_usd` | `float` | Cost in USD (computed from litellm pricing) |
| `duration_ms` | `float` | Duration of the LLM call |

### SubagentInvocation

Represents an observed sub-agent delegation.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Name of the sub-agent |
| `status` | `str` | Status (`"selected"`, `"started"`, `"completed"`, `"failed"`) |
| `duration_ms` | `float \| None` | Duration of the sub-agent call |

## Hooks

### `pytest_aitest_analysis_prompt`

When used with pytest-aitest, this plugin implements the `pytest_aitest_analysis_prompt` hook to inject Copilot-specific context into AI analysis. The hook provides:

- **Coding-agent framing** — the AI analyzer understands it's evaluating models, instructions, and tools (not MCP servers)
- **Dynamic pricing table** — model pricing data is pulled live from litellm's `model_cost` database, so cost analysis stays current without manual updates

This happens automatically — no configuration needed. Just install both plugins:

```bash
uv add "pytest-codingagents[aitest]"
```

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
