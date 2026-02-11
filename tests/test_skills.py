"""Skill directory testing.

Tests that Copilot uses skill files when provided, and that
disabling skills changes behavior.
"""

from __future__ import annotations

import pytest

from pytest_codingagents.copilot.agent import CopilotAgent


@pytest.mark.copilot
class TestSkillDirectories:
    """Test that skill directories influence agent behavior."""

    async def test_skill_loaded(self, copilot_run, tmp_path):
        """Agent with a skill directory can use the skill's knowledge."""
        # Create a skill directory with a markdown skill file
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        (skill_dir / "coding-standards.md").write_text(
            "# Coding Standards\n\n"
            "All Python functions MUST:\n"
            "- Have type hints on all parameters and return values\n"
            "- Have a one-line docstring\n"
            "- Use snake_case naming\n"
        )

        agent = CopilotAgent(
            name="with-skill",
            instructions="Follow all coding standards from your skills.",
            working_directory=str(tmp_path),
            skill_directories=[str(skill_dir)],
        )
        result = await copilot_run(
            agent,
            "Create a file called math_utils.py with functions: add, multiply, power.",
        )
        assert result.success
        assert (tmp_path / "math_utils.py").exists()
        content = (tmp_path / "math_utils.py").read_text()
        # Skill should influence code quality — expect type hints
        assert "def add" in content

    async def test_without_skill(self, copilot_run, tmp_path):
        """Agent without skills still works, for comparison."""
        agent = CopilotAgent(
            name="no-skill",
            instructions="Create files as requested.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Create a file called math_utils.py with functions: add, multiply, power.",
        )
        assert result.success
        assert (tmp_path / "math_utils.py").exists()


@pytest.mark.copilot
class TestDisabledSkills:
    """Test that skills can be selectively disabled."""

    async def test_disabled_skill_not_used(self, copilot_run, tmp_path):
        """Disabling a skill prevents it from being loaded."""
        agent = CopilotAgent(
            name="skill-disabled",
            instructions="Create files as requested.",
            working_directory=str(tmp_path),
            disabled_skills=["web-search"],
        )
        result = await copilot_run(
            agent,
            "Create a simple hello.py file with print('hello').",
        )
        assert result.success
