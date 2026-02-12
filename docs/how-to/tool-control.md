# Tool Control

Restrict which tools the agent can use with allowlists and blocklists.

## Allowlist (Whitelist)

Only permit specific tools — the agent cannot use anything else:

```python
from pytest_codingagents import CopilotAgent


async def test_read_only(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Answer questions about the codebase.",
        working_directory=str(tmp_path),
        allowed_tools=["read_file", "grep_search", "list_dir"],
    )
    result = await copilot_run(agent, "What files are in this directory?")
    assert result.success
    # Agent can only read — no file creation or modification
```

## Blocklist (Blacklist)

Block specific tools while allowing everything else:

```python
async def test_no_write(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Review code without modifying it.",
        working_directory=str(tmp_path),
        excluded_tools=["create_file", "replace_string_in_file", "run_in_terminal"],
    )
    result = await copilot_run(agent, "Review this project for potential bugs")
    assert result.success
```

## Comparing Tool Restrictions

Test whether restricting tools changes agent behavior:

```python
import pytest
from pytest_codingagents import CopilotAgent


@pytest.mark.parametrize(
    "mode,allowed,excluded",
    [
        ("unrestricted", None, None),
        ("read-only", ["read_file", "grep_search", "list_dir"], None),
        ("no-terminal", None, ["run_in_terminal"]),
    ],
)
async def test_tool_restrictions(copilot_run, tmp_path, mode, allowed, excluded):
    agent = CopilotAgent(
        name=f"tools-{mode}",
        instructions="Complete the task using available tools.",
        working_directory=str(tmp_path),
        allowed_tools=allowed,
        excluded_tools=excluded,
    )
    result = await copilot_run(agent, "Create a hello.py file")
    # In read-only mode, this should fail (no create_file tool)
    if mode == "read-only":
        assert not result.tool_was_called("create_file")
    else:
        assert result.success
```

## Use Cases

| Scenario | Configuration |
|---|---|
| Code review agent | `allowed_tools=["read_file", "grep_search", "list_dir"]` |
| File creation only | `allowed_tools=["create_file", "read_file"]` |
| No terminal access | `excluded_tools=["run_in_terminal"]` |
| No file modification | `excluded_tools=["create_file", "replace_string_in_file"]` |

## Notes

- `allowed_tools` and `excluded_tools` are mutually exclusive — use one or the other
- When `allowed_tools` is `None` (default), all tools are available
- Tool names correspond to the Copilot SDK tool names (e.g., `create_file`, `read_file`, `run_in_terminal`)
