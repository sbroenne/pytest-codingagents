"""Unit tests for CopilotResult."""

from __future__ import annotations

import pytest

from pytest_codingagents.copilot.result import CopilotResult, ToolCall, Turn, UsageInfo


class TestCopilotResultProperties:
    """Test computed properties."""

    def test_final_response_from_turns(self):
        result = CopilotResult(
            turns=[
                Turn(role="user", content="hello"),
                Turn(role="assistant", content="Hi there!"),
                Turn(role="assistant", content="Anything else?"),
            ],
        )
        assert result.final_response == "Anything else?"

    def test_final_response_none_when_no_assistant(self):
        result = CopilotResult(
            turns=[Turn(role="user", content="hello")],
        )
        assert result.final_response is None

    def test_final_response_empty_turns(self):
        result = CopilotResult()
        assert result.final_response is None


class TestToolTracking:
    """Test tool call tracking."""

    def test_all_tool_calls(self):
        tc1 = ToolCall(name="create_file", arguments='{"path": "a.py"}')
        tc2 = ToolCall(name="read_file", arguments='{"path": "a.py"}')
        result = CopilotResult(
            turns=[
                Turn(role="assistant", content="Creating files", tool_calls=[tc1, tc2]),
            ],
        )
        assert len(result.all_tool_calls) == 2

    def test_tool_was_called(self):
        tc = ToolCall(name="create_file", arguments="{}")
        result = CopilotResult(
            turns=[Turn(role="assistant", content="done", tool_calls=[tc])],
        )
        assert result.tool_was_called("create_file")
        assert not result.tool_was_called("delete_file")

    def test_tool_names_called(self):
        tc1 = ToolCall(name="create_file", arguments="{}")
        tc2 = ToolCall(name="create_file", arguments="{}")
        tc3 = ToolCall(name="read_file", arguments="{}")
        result = CopilotResult(
            turns=[Turn(role="assistant", content="done", tool_calls=[tc1, tc2, tc3])],
        )
        assert result.tool_names_called == {"create_file", "read_file"}


class TestUsageTracking:
    """Test usage/cost properties."""

    def test_total_tokens(self):
        result = CopilotResult(
            usage=[
                UsageInfo(model="gpt-4.1", input_tokens=100, output_tokens=50),
                UsageInfo(model="gpt-4.1", input_tokens=200, output_tokens=100),
            ],
        )
        assert result.total_tokens == 450

    def test_total_cost(self):
        result = CopilotResult(
            usage=[
                UsageInfo(model="gpt-4.1", input_tokens=0, output_tokens=0, cost_usd=0.01),
                UsageInfo(model="gpt-4.1", input_tokens=0, output_tokens=0, cost_usd=0.02),
            ],
        )
        assert result.total_cost_usd == pytest.approx(0.03)

    def test_token_usage_dict(self):
        result = CopilotResult(
            usage=[
                UsageInfo(model="gpt-4.1", input_tokens=100, output_tokens=50),
            ],
        )
        d = result.token_usage
        assert d["prompt"] == 100
        assert d["completion"] == 50
        assert d["total"] == 150

    def test_cost_usd_alias(self):
        result = CopilotResult(
            usage=[
                UsageInfo(model="m", input_tokens=0, output_tokens=0, cost_usd=0.05),
            ],
        )
        assert result.cost_usd == pytest.approx(0.05)


class TestSuccessError:
    """Test success/error states."""

    def test_default_success(self):
        result = CopilotResult()
        assert result.success is True
        assert result.error is None

    def test_explicit_error(self):
        result = CopilotResult(success=False, error="timeout")
        assert not result.success
        assert result.error == "timeout"
