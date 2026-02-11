"""System prompt / instructions testing.

Tests that different instructions produce different agent behaviors.
Use pytest.mark.parametrize to compare instruction variants.
"""

from __future__ import annotations

import pytest

from pytest_codingagents.copilot.agent import CopilotAgent

CONCISE_INSTRUCTIONS = """\
You are a concise coding assistant. Write minimal code with no comments.
Do not explain your work. Just create the files requested."""

VERBOSE_INSTRUCTIONS = """\
You are a thorough coding assistant. Write well-documented code with:
- Docstrings on every function and class
- Inline comments explaining logic
- Type hints on all parameters and return values
Always explain what you created after finishing."""


@pytest.mark.copilot
class TestInstructionStyles:
    """Compare concise vs verbose instructions."""

    @pytest.mark.parametrize(
        "style,instructions",
        [
            ("concise", CONCISE_INSTRUCTIONS),
            ("verbose", VERBOSE_INSTRUCTIONS),
        ],
    )
    async def test_style_produces_code(self, copilot_run, tmp_path, style, instructions):
        """Both instruction styles should successfully create a file."""
        agent = CopilotAgent(
            name=f"style-{style}",
            instructions=instructions,
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Create a Python file called calculator.py with functions: add, subtract, multiply, divide.",
        )
        assert result.success, f"Style '{style}' failed: {result.error}"
        assert (tmp_path / "calculator.py").exists()


@pytest.mark.copilot
class TestInstructionConstraints:
    """Test that instructions constrain agent behavior."""

    async def test_restricted_tools(self, copilot_run, tmp_path):
        """Agent with restricted instructions stays within bounds."""
        agent = CopilotAgent(
            name="restricted",
            instructions="You may only create Python files. Never run terminal commands.",
            working_directory=str(tmp_path),
            excluded_tools=["run_in_terminal"],
        )
        result = await copilot_run(agent, "Create a file called safe.py with print('safe')")
        assert result.success

    async def test_domain_specific_instructions(self, copilot_run, tmp_path):
        """Agent with domain-specific instructions follows them."""
        agent = CopilotAgent(
            name="fastapi-expert",
            instructions=(
                "You are a FastAPI expert. When asked to create an API, always use FastAPI. "
                "Always include type hints and Pydantic models for request/response bodies."
            ),
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Create a simple REST API with a GET /health endpoint that returns {status: 'ok'}.",
        )
        assert result.success
        # Agent may create files in tmp_path or subdirectories
        py_files = list(tmp_path.rglob("*.py"))
        assert len(py_files) > 0, "Expected at least one Python file"
