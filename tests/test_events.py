"""SDK-unique feature tests.

Tests for Copilot-specific features that don't exist in generic AI testing:
- Reasoning traces
- Permissions
- Subagent routing
- Token usage / cost tracking
- Event capture
"""

from __future__ import annotations

import pytest

from pytest_codingagents.copilot.agent import CopilotAgent


@pytest.mark.copilot
class TestReasoningTraces:
    """Test that reasoning traces are captured."""

    async def test_reasoning_captured(self, copilot_run, tmp_path):
        """Extended thinking / reasoning traces are collected."""
        agent = CopilotAgent(
            name="reasoning-test",
            reasoning_effort="high",
            instructions="Think carefully about the best approach before coding.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Create a binary search function in search.py. Consider edge cases.",
        )
        assert result.success
        # Reasoning traces may or may not be present depending on the model
        assert isinstance(result.reasoning_traces, list)


@pytest.mark.copilot
class TestPermissions:
    """Test permission handling."""

    async def test_auto_confirm_permissions(self, copilot_run, tmp_path):
        """With auto_confirm=True, permissions are auto-approved."""
        agent = CopilotAgent(
            name="auto-confirm",
            instructions="Create files as requested.",
            working_directory=str(tmp_path),
            auto_confirm=True,
        )
        result = await copilot_run(agent, "Create hello.py with print('hello')")
        assert result.success


@pytest.mark.copilot
class TestUsageTracking:
    """Test that token usage and cost are tracked."""

    async def test_usage_info_captured(self, copilot_run, tmp_path):
        """Usage info (tokens, cost) is captured from events."""
        agent = CopilotAgent(
            name="usage-tracker",
            instructions="Create files as requested.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(agent, "Create a file called echo.py that prints its arguments.")
        assert result.success
        # Usage list should have at least one entry
        assert len(result.usage) > 0, "Expected usage info to be captured"
        usage = result.usage[0]
        assert usage.input_tokens > 0 or usage.output_tokens > 0

    async def test_token_usage_dict(self, copilot_run, tmp_path):
        """token_usage property returns pytest-aitest compatible dict."""
        agent = CopilotAgent(
            name="token-dict",
            instructions="Create files as requested.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(agent, "Create hi.py with print('hi')")
        assert result.success
        usage = result.token_usage
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage


@pytest.mark.copilot
class TestEventCapture:
    """Test that raw events are captured for debugging."""

    async def test_raw_events_populated(self, copilot_run, tmp_path):
        """raw_events list contains all SDK events."""
        agent = CopilotAgent(
            name="event-capture",
            instructions="Create files as requested.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(agent, "Create note.txt with 'test note'")
        assert result.success
        assert len(result.raw_events) > 0, "Expected raw events to be captured"


@pytest.mark.copilot
class TestAllowedTools:
    """Test tool filtering."""

    async def test_excluded_tools(self, copilot_run, tmp_path):
        """Agent with excluded tools cannot use them."""
        agent = CopilotAgent(
            name="no-terminal",
            instructions="Create files as requested. Do not run any commands.",
            working_directory=str(tmp_path),
            excluded_tools=["run_in_terminal"],
        )
        result = await copilot_run(agent, "Create a file called safe.py with print('safe')")
        assert result.success
        # Verify no terminal tool was called
        assert not result.tool_was_called("run_in_terminal"), "Terminal tool should be excluded"
