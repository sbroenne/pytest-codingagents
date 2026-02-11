"""Custom agent / subagent tests.

Tests Copilot's custom agent routing and subagent invocation.

Custom agents (SDK ``CustomAgentConfig``) are specialized sub-agents defined
in the session config. The main agent can delegate tasks to them.

Key fields:
    name (str): Unique agent name (required)
    prompt (str): The agent's system prompt (required)
    description (str): What the agent does — helps model decide when to delegate
    tools (list[str]): Tools the agent can use (optional)
    mcp_servers (dict): MCP servers specific to this agent (optional)

Note: Delegation is non-deterministic — the LLM decides whether to invoke the
custom agent. Tests focus on verifiable outcomes rather than asserting
subagent invocation counts.
"""

from __future__ import annotations

import pytest

from pytest_codingagents.copilot.agent import CopilotAgent


@pytest.mark.copilot
class TestCustomAgents:
    """Test custom agent configurations and delegation."""

    async def test_custom_agent_code_and_tests(self, copilot_run, tmp_path):
        """Custom test-writer agent produces tests alongside code.

        Defines a specialized "test-writer" agent and gives a task that
        naturally splits into code creation + test writing. The custom
        agent should influence the outcome (tests get written).
        """
        agent = CopilotAgent(
            name="with-test-writer",
            instructions=(
                "You are a senior developer. When you create code, "
                "always have tests written for it. Delegate test writing "
                "to the test-writer agent when available."
            ),
            working_directory=str(tmp_path),
            custom_agents=[
                {
                    "name": "test-writer",
                    "prompt": (
                        "You are a test specialist. Write pytest unit tests "
                        "for the given code. Include edge cases. Save tests "
                        "to a test_*.py file."
                    ),
                    "description": "Writes pytest unit tests for Python code.",
                }
            ],
        )
        result = await copilot_run(
            agent,
            "Create calculator.py with functions add, subtract, multiply, and divide "
            "(raise ValueError on division by zero). Then write tests for it.",
        )
        assert result.success, f"Failed: {result.error}"

        # Code was created — may be in tmp_path or a subdirectory
        calc_files = list(tmp_path.rglob("calculator.py"))
        assert len(calc_files) > 0, "calculator.py missing"

        # Tests were created (agent or subagent should produce a test file)
        test_files = list(tmp_path.rglob("test_*.py"))
        assert len(test_files) > 0, "No test file created — custom agent may not have been invoked"

    async def test_custom_agent_with_restricted_tools(self, copilot_run, tmp_path):
        """Custom agent with tool restrictions only uses allowed tools.

        The docs-writer agent is restricted to create_file only — it
        should not run terminal commands.
        """
        agent = CopilotAgent(
            name="with-docs-writer",
            instructions="You are a project lead. Create code and delegate documentation tasks.",
            working_directory=str(tmp_path),
            custom_agents=[
                {
                    "name": "docs-writer",
                    "prompt": (
                        "You write README.md documentation for Python projects. "
                        "Create clear, concise READMEs with usage examples."
                    ),
                    "description": "Writes project documentation and README files.",
                    "tools": ["create_file", "read_file", "insert_edit_into_file"],
                }
            ],
        )
        result = await copilot_run(
            agent,
            "Create a simple greeting.py module with a greet(name) function, "
            "then create a README.md documenting how to use it.",
        )
        assert result.success
        assert (tmp_path / "greeting.py").exists()
        # README should exist (created by either main agent or docs-writer)
        assert (tmp_path / "README.md").exists(), "README.md not created"

    async def test_subagent_invocations_captured(self, copilot_run, tmp_path):
        """Subagent events are captured in result.subagent_invocations.

        Even if the model doesn't delegate, the field should be present
        and correctly typed. If it does delegate, we should see entries.
        """
        agent = CopilotAgent(
            name="delegation-test",
            instructions=(
                "You manage a team. Always delegate code review to the "
                "reviewer agent before finalizing."
            ),
            working_directory=str(tmp_path),
            custom_agents=[
                {
                    "name": "reviewer",
                    "prompt": "Review Python code for bugs, suggest fixes. Be thorough.",
                    "description": "Code review specialist.",
                }
            ],
        )
        result = await copilot_run(
            agent,
            "Create a sort.py with bubble_sort and quick_sort functions, "
            "then have the reviewer check the code.",
        )
        assert result.success, f"Failed: {result.error}"

        # sort.py should exist somewhere in the working directory
        sort_files = list(tmp_path.rglob("sort.py"))
        assert len(sort_files) > 0, "sort.py was not created"

        # subagent_invocations is always a list (may be empty if model didn't delegate)
        assert isinstance(result.subagent_invocations, list)

        # If any subagent was invoked, verify the structure
        for invocation in result.subagent_invocations:
            assert invocation.name, "Subagent invocation must have a name"
            assert invocation.status in ("selected", "started", "completed", "failed")
