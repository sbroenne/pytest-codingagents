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

    from _pytest.nodes import Item

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

        # Stash for pytest-aitest's reporting plugin.
        # The plugin hook also does this automatically for tests that
        # call run_copilot() directly, but explicit stashing from the
        # fixture ensures it works even if the hook order changes.
        stash_on_item(request.node, agent, result)

        return result

    return _run


def _convert_to_aitest(
    agent: CopilotAgent,
    result: CopilotResult,
) -> tuple[Any, Any] | None:
    """Convert CopilotResult to pytest-aitest types.

    Returns ``(AgentResult, Agent)`` tuple, or ``None`` if pytest-aitest
    is not installed.

    Since CopilotResult already uses pytest-aitest's Turn and ToolCall types,
    the turns can be passed through directly without rebuilding.
    """
    try:
        from pytest_aitest.core.agent import Agent, Provider
        from pytest_aitest.core.result import AgentResult

        # Turns already use aitest's Turn/ToolCall types — pass through directly
        aitest_result = AgentResult(
            turns=list(result.turns),
            success=result.success,
            error=result.error,
            duration_ms=result.duration_ms,
            token_usage=result.token_usage,
            cost_usd=result.cost_usd,
            effective_system_prompt=agent.instructions or "",
        )

        aitest_agent = Agent(
            name=agent.name,
            provider=Provider(model=result.model_used or agent.model or "copilot-default"),
            system_prompt=agent.instructions,
            max_turns=agent.max_turns,
        )

        return aitest_result, aitest_agent

    except ImportError:
        # pytest-aitest not installed — tests still work, just no HTML reports
        return None


def stash_on_item(
    item: Item,
    agent: CopilotAgent,
    result: CopilotResult,
) -> None:
    """Stash result on the test node for pytest-aitest compatibility.

    pytest-aitest's plugin reads ``node._aitest_result`` and
    ``node._aitest_agent`` in its ``pytest_runtest_makereport`` hook
    to build HTML reports. We produce compatible objects so Copilot
    test results appear in the same reports as synthetic agent tests.

    Called automatically by the ``copilot_run`` fixture and by the
    ``pytest_runtest_makereport`` plugin hook; consumers should rarely
    need to call this directly.
    """
    converted = _convert_to_aitest(agent, result)
    if converted is not None:
        item._aitest_result = converted[0]  # type: ignore[attr-defined]
        item._aitest_agent = converted[1]  # type: ignore[attr-defined]


def _stash_for_aitest(
    request: pytest.FixtureRequest,
    agent: CopilotAgent,
    result: CopilotResult,
) -> None:
    """Stash result via fixture request (backward-compatible helper).

    .. deprecated::
        Use :func:`stash_on_item` instead, passing ``request.node``
        as the ``item`` parameter.
    """
    stash_on_item(request.node, agent, result)  # type: ignore[arg-type]
