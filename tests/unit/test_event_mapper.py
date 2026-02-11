"""Unit tests for EventMapper.

These are pure logic tests — no LLM calls, no SDK.
They verify that EventMapper correctly maps mock events to CopilotResult.
"""

from __future__ import annotations

from types import SimpleNamespace

from pytest_codingagents.copilot.events import EventMapper


def _make_event(event_type: str, **data_fields) -> SimpleNamespace:
    """Create a mock SessionEvent with the given type and data fields."""
    # Use SimpleNamespace so getattr(data, field, default) returns default
    # for missing fields (unlike MagicMock which auto-creates them).
    data = SimpleNamespace(**data_fields)
    return SimpleNamespace(type=event_type, data=data)


class TestEventMapperAssistantMessage:
    """Test assistant.message event handling."""

    def test_captures_content(self):
        mapper = EventMapper()
        event = _make_event("assistant.message", content="Hello world")
        mapper.handle(event)
        result = mapper.build()
        assert result.final_response == "Hello world"

    def test_multiple_messages_appended(self):
        mapper = EventMapper()
        mapper.handle(_make_event("assistant.message", content="First"))
        mapper.handle(_make_event("assistant.message", content="Second"))
        result = mapper.build()
        assert result.final_response == "Second"

    def test_empty_content_skipped(self):
        mapper = EventMapper()
        mapper.handle(_make_event("assistant.message", content=None))
        result = mapper.build()
        assert result.final_response is None


class TestEventMapperToolCalls:
    """Test tool execution event handling."""

    def test_tool_start_and_complete(self):
        mapper = EventMapper()
        mapper.handle(
            _make_event(
                "tool.execution_start",
                tool_name="create_file",
                tool_call_id="tc_1",
                arguments='{"path": "test.py"}',
            )
        )
        result_obj = SimpleNamespace(content="File created")
        mapper.handle(
            _make_event(
                "tool.execution_complete",
                tool_name="create_file",
                tool_call_id="tc_1",
                result=result_obj,
            )
        )
        result = mapper.build()
        assert len(result.all_tool_calls) == 1
        tc = result.all_tool_calls[0]
        assert tc.name == "create_file"
        assert tc.result == "File created"

    def test_tool_without_complete(self):
        mapper = EventMapper()
        mapper.handle(
            _make_event(
                "tool.execution_start",
                tool_name="read_file",
                tool_call_id="tc_2",
                arguments="{}",
            )
        )
        result = mapper.build()
        assert len(result.all_tool_calls) == 1
        assert result.all_tool_calls[0].result is None


class TestEventMapperUsage:
    """Test usage tracking."""

    def test_usage_captured(self):
        mapper = EventMapper()
        mapper.handle(
            _make_event(
                "assistant.usage",
                model="gpt-4.1",
                input_tokens=100,
                output_tokens=50,
                cost=0.001,
                duration=500,
                cache_read_tokens=10,
            )
        )
        result = mapper.build()
        assert len(result.usage) == 1
        u = result.usage[0]
        assert u.model == "gpt-4.1"
        assert u.input_tokens == 100
        assert u.output_tokens == 50
        # cost_usd computed from litellm pricing, not from SDK's cost field
        # (SDK's cost field uses an unknown unit, not USD)
        assert u.cost_usd >= 0.0  # litellm may or may not have pricing


class TestEventMapperReasoning:
    """Test reasoning trace capture."""

    def test_reasoning_collected(self):
        mapper = EventMapper()
        mapper.handle(_make_event("assistant.reasoning", reasoning_text="Let me think..."))
        mapper.handle(
            _make_event("assistant.reasoning", reasoning_text="I should use binary search.")
        )
        result = mapper.build()
        assert len(result.reasoning_traces) == 2
        assert result.reasoning_traces[0] == "Let me think..."


class TestEventMapperSubagents:
    """Test subagent lifecycle tracking."""

    def test_subagent_lifecycle(self):
        mapper = EventMapper()
        mapper.handle(_make_event("subagent.started", agent_name="code-reviewer"))
        mapper.handle(_make_event("subagent.completed", agent_name="code-reviewer", duration=1000))
        result = mapper.build()
        assert len(result.subagent_invocations) == 1
        sa = result.subagent_invocations[0]
        assert sa.name == "code-reviewer"
        assert sa.status == "completed"


class TestEventMapperSessionEvents:
    """Test session-level event handling."""

    def test_session_start_captures_model(self):
        mapper = EventMapper()
        mapper.handle(_make_event("session.start", selected_model="claude-sonnet-4"))
        result = mapper.build()
        assert result.model_used == "claude-sonnet-4"

    def test_session_error_captured(self):
        mapper = EventMapper()
        mapper.handle(_make_event("session.error", message="Rate limit exceeded"))
        result = mapper.build()
        assert result.error == "Rate limit exceeded"
        assert not result.success


class TestEventMapperBuild:
    """Test build() produces correct CopilotResult."""

    def test_empty_mapper_builds(self):
        mapper = EventMapper()
        result = mapper.build()
        assert result.success  # No error = success
        assert result.final_response is None
        assert result.all_tool_calls == []
        assert result.usage == []

    def test_raw_events_collected(self):
        mapper = EventMapper()
        e1 = _make_event("assistant.message", content="hi")
        e2 = _make_event("assistant.message", content="bye")
        mapper.handle(e1)
        mapper.handle(e2)
        result = mapper.build()
        assert len(result.raw_events) == 2
