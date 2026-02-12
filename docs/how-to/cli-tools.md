# CLI Tool Testing

Test that GitHub Copilot can operate command-line tools correctly.

## Basic Usage

Give the agent a task that requires CLI tools and verify the outcome:

```python
from pytest_codingagents import CopilotAgent


async def test_git_init(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Use git commands as requested.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(
        agent,
        "Initialize a git repo, create a .gitignore for Python, and make an initial commit.",
    )
    assert result.success
    assert (tmp_path / ".git").is_dir()
    assert (tmp_path / ".gitignore").exists()
```

## Verifying File Output

Check that CLI operations produce the expected files:

```python
async def test_project_scaffold(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Create project structures as requested.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(
        agent,
        "Create a Python package called 'mylib' with __init__.py, "
        "a pyproject.toml using hatchling, and a tests/ directory.",
    )
    assert result.success
    assert (tmp_path / "src" / "mylib" / "__init__.py").exists() or (
        tmp_path / "mylib" / "__init__.py"
    ).exists()
    assert (tmp_path / "pyproject.toml").exists()
```

## Testing Complex Workflows

Chain multiple CLI operations into a single task:

```python
async def test_git_workflow(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Perform git operations as requested. Use git commands directly.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(
        agent,
        "Initialize a git repo, create hello.py with print('hello'), "
        "add it, commit with message 'initial', then create a 'feature' branch.",
    )
    assert result.success
    assert (tmp_path / "hello.py").exists()
```

## Comparing Instructions for CLI Tasks

Test which instructions produce better CLI usage:

```python
import pytest
from pytest_codingagents import CopilotAgent


@pytest.mark.parametrize(
    "style,instructions",
    [
        ("minimal", "Execute commands as requested."),
        ("guided", "You are a DevOps assistant. Use standard CLI tools. "
         "Always verify operations succeed before proceeding."),
    ],
)
async def test_cli_instructions(copilot_run, tmp_path, style, instructions):
    agent = CopilotAgent(
        name=f"cli-{style}",
        instructions=instructions,
        working_directory=str(tmp_path),
    )
    result = await copilot_run(
        agent,
        "Create a Python virtual environment and install requests",
    )
    assert result.success
```
