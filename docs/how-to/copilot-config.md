# Load from Copilot Config Files

`CopilotAgent.from_copilot_config()` builds a `CopilotAgent` directly from
your real GitHub Copilot configuration files — no manual copy-paste of
instructions or agent definitions required.

## What it loads

| Source | Path | Maps to |
|--------|------|---------|
| Project instructions | `.github/copilot-instructions.md` | `instructions` |
| Project custom agents | `.github/agents/*.agent.md` | `custom_agents` |
| Global custom agents | `~/.config/copilot/agents/*.agent.md` | `custom_agents` |

**Precedence:** project-level agents override global agents with the same name.

## Basic usage

```python
from pytest_codingagents import CopilotAgent

agent = CopilotAgent.from_copilot_config()
```

By default `project_path` is the current working directory and global agents
are included (`include_global=True`).

## A/B testing with your production config

The most powerful use case is using your real config as the **baseline** and
comparing it against a variant — no duplication needed:

```python
import pytest
from pytest_codingagents import CopilotAgent

@pytest.fixture
def baseline():
    """Your actual production Copilot config."""
    return CopilotAgent.from_copilot_config()

@pytest.fixture
def treatment():
    """Same config, but with tightened instructions."""
    return CopilotAgent.from_copilot_config(
        instructions="Always add type hints to every function.",
    )
```

## Override specific fields

Any keyword argument overrides the loaded value:

```python
# Use production config but force a specific model
agent = CopilotAgent.from_copilot_config(model="claude-opus-4.5")

# Skip global agents
agent = CopilotAgent.from_copilot_config(include_global=False)

# Load config from a different project
agent = CopilotAgent.from_copilot_config("../other-project")
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

## Config file locations

GitHub Copilot CLI uses two levels of custom agent config:

| Level | Location |
|-------|----------|
| Project | `.github/agents/*.agent.md` |
| Global (user) | `~/.config/copilot/agents/*.agent.md` |

Create agents in the CLI with `/agent → Create new agent` and choose
**Project** or **User** scope.

## See also

- [A/B Testing Guide](ab-testing.md)
- [GitHub Copilot custom agents docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli)
- [Custom agents configuration reference](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
