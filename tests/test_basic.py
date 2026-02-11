"""Basic Copilot tool usage tests.

Tests that Copilot can perform fundamental file operations
when given clear instructions.
"""

from __future__ import annotations

import pytest

from pytest_codingagents.copilot.agent import CopilotAgent


@pytest.mark.copilot
class TestFileOperations:
    """Test basic file creation and reading."""

    async def test_create_file(self, copilot_run, tmp_path):
        """Copilot can create a file when asked."""
        agent = CopilotAgent(
            name="file-creator",
            instructions="You are a helpful coding assistant. Create files as requested.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(agent, "Create a file called hello.py containing: print('hello world')")
        assert result.success, f"Expected success, got error: {result.error}"
        assert (tmp_path / "hello.py").exists(), "hello.py was not created"

    async def test_create_and_read_file(self, copilot_run, tmp_path):
        """Copilot can create a file and confirm its contents."""
        agent = CopilotAgent(
            name="file-manager",
            instructions="You are a helpful coding assistant.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Create a file called greet.py with a function greet(name) that returns f'Hello, {name}!'. "
            "Then read the file back and confirm it looks correct.",
        )
        assert result.success
        assert (tmp_path / "greet.py").exists()
        content = (tmp_path / "greet.py").read_text()
        assert "def greet" in content
        assert "Hello" in content


@pytest.mark.copilot
class TestToolUsage:
    """Test that Copilot uses the right tools."""

    async def test_uses_create_file_tool(self, copilot_run, tmp_path):
        """Copilot uses the create_file tool to write files."""
        agent = CopilotAgent(
            name="tool-tracker",
            instructions="Create files as requested.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(agent, "Create a file called test.txt with 'hello'")
        assert result.success
        assert len(result.all_tool_calls) > 0, "Expected at least one tool call"

    async def test_multi_file_creation(self, copilot_run, tmp_path):
        """Copilot can create multiple files in one prompt."""
        agent = CopilotAgent(
            name="multi-file",
            instructions="Create all requested files.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Create two files: "
            "1. utils.py with a function add(a, b) that returns a + b "
            "2. test_utils.py that imports add and has a test_add function",
        )
        assert result.success
        assert (tmp_path / "utils.py").exists()
        assert (tmp_path / "test_utils.py").exists()
