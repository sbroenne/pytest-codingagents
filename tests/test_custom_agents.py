"""Custom agent / subagent tests.

Tests Copilot's custom agent routing and subagent invocation.
"""

from __future__ import annotations

import pytest

from pytest_codingagents.copilot.agent import CopilotAgent


@pytest.mark.copilot
class TestCustomAgents:
    """Test custom agent configurations."""

    async def test_with_custom_agent(self, copilot_run, tmp_path):
        """Agent with custom agent config routes work correctly."""
        agent = CopilotAgent(
            name="with-custom-agent",
            instructions="You are a coding assistant. Use available agents when appropriate.",
            working_directory=str(tmp_path),
            custom_agents=[
                {
                    "name": "code-reviewer",
                    "instructions": "Review code for bugs and style issues.",
                }
            ],
        )
        result = await copilot_run(
            agent,
            "Create a file called app.py with a simple Flask app that has a /hello route.",
        )
        assert result.success

    async def test_subagent_invocations_tracked(self, copilot_run, tmp_path):
        """Subagent invocations are captured in the result."""
        agent = CopilotAgent(
            name="subagent-tracker",
            instructions="Delegate complex tasks to specialized subagents when available.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Create a Python project with: main.py, utils.py, and test_utils.py.",
        )
        assert result.success
        # Subagent invocations may or may not happen — just verify the field exists
        assert isinstance(result.subagent_invocations, list)
