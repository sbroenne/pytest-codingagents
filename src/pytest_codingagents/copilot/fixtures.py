"""Pytest fixtures for GitHub Copilot testing.

Provides the ``copilot_run`` fixture that executes prompts against Copilot
and stashes results for pytest-aitest reporting (if installed).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from pytest_codingagents.copilot.runner import run_copilot

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from pytest_codingagents.copilot.agent import CopilotAgent
    from pytest_codingagents.copilot.result import CopilotResult


@pytest.fixture
def copilot_run(
    request: pytest.FixtureRequest,
) -> Callable[..., Coroutine[Any, Any, CopilotResult]]:
    """Execute a prompt against a CopilotAgent and capture results.

    Results are automatically stashed on the test node for pytest-aitest's
    reporting plugin (if installed). This gives you full HTML reports —
    leaderboard, AI insights, Mermaid diagrams — for free.

    Example:
        async def test_file_creation(copilot_run, tmp_path):
            agent = CopilotAgent(
                instructions="Create files as requested.",
                working_directory=str(tmp_path),
            )
            result = await copilot_run(agent, "Create hello.py with print('hello')")
            assert result.success
            assert result.tool_was_called("create_file")
    """

    async def _run(agent: CopilotAgent, prompt: str) -> CopilotResult:
        result = await run_copilot(agent, prompt)

        # Stash for pytest-aitest's reporting plugin
        # pytest-aitest reads these in pytest_runtest_makereport
        _stash_for_aitest(request, agent, result)

        return result

    return _run


def _stash_for_aitest(
    request: pytest.FixtureRequest,
    agent: CopilotAgent,
    result: CopilotResult,
) -> None:
    """Stash result on the test node for pytest-aitest compatibility.

    pytest-aitest's plugin reads ``node._aitest_result`` and
    ``node._aitest_agent`` in its ``pytest_runtest_makereport`` hook
    to build HTML reports. We produce compatible objects so Copilot
    test results appear in the same reports as synthetic agent tests.
    """
    try:
        from pytest_aitest.core.agent import Agent, Provider
        from pytest_aitest.core.result import AgentResult
        from pytest_aitest.core.result import ToolCall as AitestToolCall
        from pytest_aitest.core.result import Turn as AitestTurn

        # Convert turns
        aitest_turns = []
        for turn in result.turns:
            aitest_tool_calls = [
                AitestToolCall(
                    name=tc.name,
                    arguments=tc.arguments if isinstance(tc.arguments, dict) else {},
                    result=tc.result,
                    error=tc.error,
                    duration_ms=tc.duration_ms,
                )
                for tc in turn.tool_calls
            ]
            aitest_turns.append(
                AitestTurn(
                    role=turn.role,
                    content=turn.content,
                    tool_calls=aitest_tool_calls,
                )
            )

        # Build AgentResult
        aitest_result = AgentResult(
            turns=aitest_turns,
            success=result.success,
            error=result.error,
            duration_ms=result.duration_ms,
            token_usage=result.token_usage,
            cost_usd=result.cost_usd,
        )

        # Build Agent
        aitest_agent = Agent(
            name=agent.name,
            provider=Provider(model=result.model_used or agent.model or "copilot-default"),
            system_prompt=agent.instructions,
            max_turns=agent.max_turns,
        )

        # Stash on the test node
        request.node._aitest_result = aitest_result  # type: ignore[attr-defined]
        request.node._aitest_agent = aitest_agent  # type: ignore[attr-defined]

    except ImportError:
        # pytest-aitest not installed — tests still work, just no HTML reports
        pass
