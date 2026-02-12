# Skill Testing

Test whether domain knowledge injected via skill directories improves agent behavior.

## What Are Skills?

Skills are directories containing markdown files with domain-specific knowledge — coding standards, API conventions, architectural guidelines, etc. When attached to a `CopilotAgent`, these files are loaded into the agent's context.

## Basic Usage

Create a skill directory and test that the agent follows its guidance:

```python
from pytest_codingagents import CopilotAgent


async def test_coding_standards(copilot_run, tmp_path):
    # Create a skill with coding standards
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    (skill_dir / "coding-standards.md").write_text(
        "# Coding Standards\n\n"
        "All Python functions MUST have type hints and docstrings.\n"
        "Use snake_case for all function names.\n"
    )

    agent = CopilotAgent(
        name="with-standards",
        instructions="Follow all coding standards from your skills.",
        working_directory=str(tmp_path),
        skill_directories=[str(skill_dir)],
    )
    result = await copilot_run(agent, "Create math_utils.py with add and multiply")
    assert result.success
    content = (tmp_path / "math_utils.py").read_text()
    assert "def add" in content
```

## Measuring Skill Impact

Parametrize tests with and without skills to measure whether they improve results:

```python
import pytest
from pytest_codingagents import CopilotAgent


@pytest.mark.parametrize("use_skill", [True, False], ids=["with-skill", "without-skill"])
async def test_skill_impact(copilot_run, tmp_path, use_skill):
    # Set up skill directory
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    (skill_dir / "standards.md").write_text(
        "All functions MUST have type hints and docstrings."
    )

    skill_dirs = [str(skill_dir)] if use_skill else []
    agent = CopilotAgent(
        name=f"skill-{'on' if use_skill else 'off'}",
        instructions="Create clean Python code.",
        working_directory=str(tmp_path),
        skill_directories=skill_dirs,
    )
    result = await copilot_run(agent, "Create a utility module with 3 helper functions")
    assert result.success
```

The AI analysis report highlights differences in behavior and quality between skill-on and skill-off runs.

## Multiple Skill Directories

Load skills from several directories:

```python
agent = CopilotAgent(
    instructions="Follow all project guidelines.",
    working_directory=str(tmp_path),
    skill_directories=[
        "skills/coding-standards",
        "skills/api-conventions",
        "skills/testing-patterns",
    ],
)
```

## Disabling Specific Skills

Selectively disable skills to isolate their effects:

```python
agent = CopilotAgent(
    instructions="Follow project guidelines.",
    working_directory=str(tmp_path),
    skill_directories=["skills/"],
    disabled_skills=["deprecated-patterns"],
)
```

## Comparing Skill Versions

Test different versions of the same skill to find the most effective phrasing:

```python
import pytest
from pytest_codingagents import CopilotAgent

SKILL_VERSIONS = {
    "concise": "Use type hints. Use docstrings. Use snake_case.",
    "detailed": (
        "# Coding Standards\n\n"
        "## Type Hints\n"
        "Every function parameter and return value MUST have a type hint.\n\n"
        "## Docstrings\n"
        "Every public function MUST have a Google-style docstring.\n"
    ),
}


@pytest.mark.parametrize("style", SKILL_VERSIONS.keys())
async def test_skill_phrasing(copilot_run, tmp_path, style):
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    (skill_dir / "standards.md").write_text(SKILL_VERSIONS[style])

    agent = CopilotAgent(
        name=f"skill-{style}",
        instructions="Follow the coding standards.",
        working_directory=str(tmp_path),
        skill_directories=[str(skill_dir)],
    )
    result = await copilot_run(agent, "Create a data processing module")
    assert result.success
```
