# Load from Copilot Config Files

`CopilotAgent.from_copilot_config()` builds a `CopilotAgent` from any directory
that contains GitHub Copilot config files — your production project, a dedicated
test fixture project, a shared team config repo, or anything else.

## What it loads

| Source | Path (relative to the root you point at) | Maps to |
|--------|------------------------------------------|---------|
| Instructions | `.github/copilot-instructions.md` | `instructions` |
| Custom agents | `.github/agents/*.agent.md` | `custom_agents` |

## Basic usage

```python
from pytest_codingagents import CopilotAgent

# Current directory (default)
agent = CopilotAgent.from_copilot_config()

# Explicit path
agent = CopilotAgent.from_copilot_config("path/to/any/dir")
```

## A/B testing with your production config

The main use case: use your real config as the **baseline** and compare
against a variant — no duplication needed.

```python
import pytest
from pytest_codingagents import CopilotAgent

@pytest.fixture
def baseline():
    """The actual production Copilot config."""
    return CopilotAgent.from_copilot_config()

@pytest.fixture
def treatment():
    """Same config, one instruction changed."""
    return CopilotAgent.from_copilot_config(
        instructions="Always add type hints to every function.",
    )
```

## Point at any directory

There is no concept of "global" vs "project" — just a path. Point it
wherever your config lives:

```python
# Production project
baseline = CopilotAgent.from_copilot_config("/src/my-app")

# Dedicated test fixture project with stricter agents
treatment = CopilotAgent.from_copilot_config("tests/fixtures/strict-agents")

# Shared team config library (checked into a separate repo)
shared = CopilotAgent.from_copilot_config("/shared/team/copilot-config")
```

## Override fields after loading

Any keyword argument overrides the loaded value:

```python
# Load from the current project but force a specific model
agent = CopilotAgent.from_copilot_config(model="claude-opus-4.5")

# Load from a different path and override instructions
agent = CopilotAgent.from_copilot_config(
    "tests/fixtures/baseline",
    instructions="Tightened: always add type hints.",
)
```

## Custom agent file format

Custom agents are defined in `.agent.md` files with optional YAML frontmatter:

```markdown
---
name: test-specialist
description: Focuses on test coverage and quality
tools:
  - read
  - search
  - edit
---

You are a testing specialist. Your responsibilities:

- Analyse existing tests and identify coverage gaps
- Write unit and integration tests following best practices
- Focus only on test files; do not modify production code
```

The frontmatter supports `name`, `description`, `tools`, and `mcp-servers`.
The Markdown body becomes the agent's prompt.

## See also

- [A/B Testing Guide](ab-testing.md)
- [GitHub Copilot custom agents docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli)
- [Custom agents configuration reference](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
