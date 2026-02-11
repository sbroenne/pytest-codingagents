"""CLI tool testing.

Tests that Copilot can operate command-line tools correctly.
Copilot has built-in terminal access — these tests verify it can
use CLI tools to accomplish tasks.
"""

from __future__ import annotations

import pytest

from pytest_codingagents.copilot.agent import CopilotAgent


@pytest.mark.copilot
class TestCLIOperations:
    """Test that Copilot can operate CLI tools."""

    async def test_run_python_script(self, copilot_run, tmp_path):
        """Agent can create and run a Python script via CLI."""
        agent = CopilotAgent(
            name="cli-runner",
            instructions="Create and run Python scripts as requested.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Create a file called greet.py that prints 'Hello from CLI'. "
            "Then run it with python and confirm it works.",
        )
        assert result.success
        assert (tmp_path / "greet.py").exists()
        # Agent should have used terminal (may be called run_in_terminal or powershell)
        assert result.tool_was_called("run_in_terminal") or result.tool_was_called("powershell"), (
            f"Expected terminal tool, got: {result.tool_names_called}"
        )

    async def test_use_git_cli(self, copilot_run, tmp_path):
        """Agent can use git CLI to initialize a repository."""
        agent = CopilotAgent(
            name="git-operator",
            instructions="Use git commands as requested. Do not ask for confirmation.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Initialize a git repository, create a .gitignore for Python, and make an initial commit.",
        )
        assert result.success
        assert (tmp_path / ".git").is_dir()

    async def test_cli_tool_output_captured(self, copilot_run, tmp_path):
        """Agent processes CLI output and uses it in its response."""
        # Create a file to inspect
        (tmp_path / "data.txt").write_text("line1\nline2\nline3\nline4\nline5\n")

        agent = CopilotAgent(
            name="cli-analyzer",
            instructions="Use terminal commands to analyze files. Report findings clearly.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Count the number of lines in data.txt using a terminal command and tell me the count.",
        )
        assert result.success
        assert result.final_response is not None
        assert "5" in result.final_response


@pytest.mark.copilot
class TestCLIWithToolControl:
    """Test CLI behavior with tool restrictions."""

    async def test_no_terminal_when_excluded(self, copilot_run, tmp_path):
        """Agent cannot use terminal when it's excluded."""
        agent = CopilotAgent(
            name="no-cli",
            instructions="Create files as requested. Do not run commands.",
            working_directory=str(tmp_path),
            excluded_tools=["run_in_terminal"],
        )
        result = await copilot_run(
            agent,
            "Create a file called safe.py with print('safe')",
        )
        assert result.success
        assert not result.tool_was_called("run_in_terminal")
