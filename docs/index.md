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

## Supported Agents

| Agent | SDK | Status |
|-------|-----|--------|
| GitHub Copilot | `github-copilot-sdk` | :white_check_mark: Implemented |

## Next Steps

- [Getting Started](getting-started/index.md) — Install and write your first test
- [API Reference](reference/api.md) — Full API documentation
- [Contributing](contributing/index.md) — How to contribute
