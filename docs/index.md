# pytest-codingagents

A pytest plugin for testing coding agents via their native SDKs.

You give a coding agent a task. Did it pick the right tools? Did it produce working code? Did it follow your instructions? **pytest-codingagents lets you answer these questions with automated tests.**

## Why?

You're rolling out GitHub Copilot to your team. But which model works best for your codebase? Do your custom instructions improve quality? Does the agent use your MCP servers correctly? Can it operate your CLI tools? Do your custom agents and skills actually help?

You can't answer these questions by trying things manually. You need **repeatable, automated tests** that evaluate:

- **Instructions** — Do your system prompts produce the desired behavior?
- **MCP Servers** — Can the agent discover and use your custom tools?
- **CLI Tools** — Can the agent operate command-line interfaces correctly?
- **Custom Agents** — Do your sub-agents handle delegated tasks?
- **Skills** — Does domain knowledge improve agent performance?
- **Models** — Which model works best for your use case and budget?

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

## Supported Agents

| Agent | SDK | Status |
|-------|-----|--------|
| GitHub Copilot | `github-copilot-sdk` | :white_check_mark: Implemented |

## Next Steps

- [Getting Started](getting-started/index.md) — Install and write your first test
- [API Reference](reference/api.md) — Full API documentation
- [Contributing](contributing/index.md) — How to contribute
