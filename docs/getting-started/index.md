# Getting Started

## Installation

```bash
uv add pytest-codingagents
```

## Prerequisites

- Python 3.11+
- GitHub Copilot access (the SDK uses the Copilot CLI bundled with the package)
- Authentication: either `gh` CLI login or a `GITHUB_TOKEN` environment variable

## Your First Test

```python
from pytest_codingagents import CopilotAgent


async def test_hello_world(copilot_run, tmp_path):
    agent = CopilotAgent(
        name="hello-test",
        instructions="Create files as requested.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create hello.py that prints 'hello world'")

    assert result.success
    assert (tmp_path / "hello.py").exists()
```

## How It Works

1. **You define a `CopilotAgent`** — model, instructions, working directory
2. **You write a prompt** — what the agent should do
3. **The SDK runs it** — against the real Copilot CLI, no mocks
4. **You assert on `CopilotResult`** — success, tool calls, file changes, tokens

## What's Next

- [Model Comparison](model-comparison.md) — Compare different models
- [Instruction Testing](instruction-testing.md) — Test different system prompts
