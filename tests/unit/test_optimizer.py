"""Unit tests for optimize_instruction() and InstructionSuggestion."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from pytest_codingagents.copilot.optimizer import InstructionSuggestion, optimize_instruction
from pytest_codingagents.copilot.result import CopilotResult, ToolCall, Turn


def _make_result(
    *,
    success: bool = True,
    final_response: str = "Here is the code.",
    tools: list[str] | None = None,
) -> CopilotResult:
    tool_calls = [ToolCall(name=t, arguments={}) for t in (tools or [])]
    return CopilotResult(
        success=success,
        turns=[
            Turn(role="assistant", content=final_response, tool_calls=tool_calls),
        ],
    )


def _make_agent_mock(instruction: str, reasoning: str, changes: str) -> MagicMock:
    """Build a pydantic-ai Agent mock that returns a structured suggestion."""
    output = MagicMock()
    output.instruction = instruction
    output.reasoning = reasoning
    output.changes = changes

    run_result = MagicMock()
    run_result.output = output

    agent_instance = MagicMock()
    agent_instance.run = AsyncMock(return_value=run_result)

    agent_class = MagicMock(return_value=agent_instance)
    return agent_class


class TestInstructionSuggestion:
    """Tests for the InstructionSuggestion dataclass."""

    def test_str_contains_instruction(self):
        s = InstructionSuggestion(
            instruction="Always add docstrings.",
            reasoning="The original instruction omits documentation requirements.",
            changes="Added docstring mandate.",
        )
        assert "Always add docstrings." in str(s)

    def test_str_contains_reasoning(self):
        s = InstructionSuggestion(
            instruction="inst",
            reasoning="because reasons",
            changes="changed x",
        )
        assert "because reasons" in str(s)

    def test_str_contains_changes(self):
        s = InstructionSuggestion(
            instruction="inst",
            reasoning="reason",
            changes="Added docstring mandate.",
        )
        assert "Added docstring mandate." in str(s)

    def test_fields_accessible(self):
        s = InstructionSuggestion(
            instruction="inst",
            reasoning="reason",
            changes="changes",
        )
        assert s.instruction == "inst"
        assert s.reasoning == "reason"
        assert s.changes == "changes"


class TestOptimizeInstruction:
    """Tests for optimize_instruction()."""

    async def test_returns_instruction_suggestion(self):
        """optimize_instruction returns an InstructionSuggestion."""
        agent_class = _make_agent_mock(
            instruction="Always add Google-style docstrings.",
            reasoning="The original instruction omits documentation.",
            changes="Added docstring mandate.",
        )

        # patch pydantic_ai.Agent in the module where it's imported
        sys.modules["pydantic_ai"].Agent = agent_class  # type: ignore[attr-defined]

        result = await optimize_instruction(
            "Write Python code.",
            _make_result(),
            "Agent should add docstrings.",
        )

        assert isinstance(result, InstructionSuggestion)
        assert result.instruction == "Always add Google-style docstrings."
        assert result.reasoning == "The original instruction omits documentation."
        assert result.changes == "Added docstring mandate."

    async def test_uses_default_model(self):
        """optimize_instruction defaults to openai:gpt-4o-mini."""
        agent_class = _make_agent_mock("inst", "reason", "changes")
        sys.modules["pydantic_ai"].Agent = agent_class  # type: ignore[attr-defined]

        await optimize_instruction("inst", _make_result(), "criterion")

        agent_class.assert_called_once()
        assert agent_class.call_args[0][0] == "openai:gpt-4o-mini"

    async def test_accepts_custom_model(self):
        """optimize_instruction accepts a custom model string."""
        agent_class = _make_agent_mock("inst", "reason", "changes")
        sys.modules["pydantic_ai"].Agent = agent_class  # type: ignore[attr-defined]

        await optimize_instruction(
            "inst",
            _make_result(),
            "criterion",
            model="anthropic:claude-3-haiku-20240307",
        )

        assert agent_class.call_args[0][0] == "anthropic:claude-3-haiku-20240307"

    async def test_includes_criterion_in_prompt(self):
        """The LLM prompt includes the criterion text."""
        agent_class = _make_agent_mock("improved", "reason", "change")
        agent_instance = agent_class.return_value
        sys.modules["pydantic_ai"].Agent = agent_class  # type: ignore[attr-defined]

        await optimize_instruction(
            "Write code.",
            _make_result(),
            "Agent must use type hints on all functions.",
        )

        prompt = agent_instance.run.call_args[0][0]
        assert "type hints" in prompt

    async def test_includes_current_instruction_in_prompt(self):
        """The LLM prompt contains the current instruction."""
        agent_class = _make_agent_mock("inst", "reason", "changes")
        agent_instance = agent_class.return_value
        sys.modules["pydantic_ai"].Agent = agent_class  # type: ignore[attr-defined]

        await optimize_instruction(
            "Always use FastAPI for web APIs.",
            _make_result(),
            "criterion",
        )

        prompt = agent_instance.run.call_args[0][0]
        assert "FastAPI" in prompt

    async def test_includes_agent_output_in_prompt(self):
        """The LLM prompt contains the agent's final response."""
        agent_class = _make_agent_mock("inst", "reason", "changes")
        agent_instance = agent_class.return_value
        sys.modules["pydantic_ai"].Agent = agent_class  # type: ignore[attr-defined]

        result = _make_result(final_response="def add(a, b): return a + b")
        await optimize_instruction("inst", result, "criterion")

        prompt = agent_instance.run.call_args[0][0]
        assert "def add" in prompt

    async def test_handles_no_final_response(self):
        """optimize_instruction handles results with no turns gracefully."""
        agent_class = _make_agent_mock("inst", "reason", "changes")
        sys.modules["pydantic_ai"].Agent = agent_class  # type: ignore[attr-defined]

        empty_result = CopilotResult(success=False, turns=[])
        result = await optimize_instruction("inst", empty_result, "criterion")

        assert isinstance(result, InstructionSuggestion)

    async def test_handles_empty_instruction(self):
        """optimize_instruction handles empty current instruction."""
        agent_class = _make_agent_mock("new inst", "reason", "changes")
        sys.modules["pydantic_ai"].Agent = agent_class  # type: ignore[attr-defined]

        result = await optimize_instruction("", _make_result(), "criterion")
        assert isinstance(result, InstructionSuggestion)

    async def test_includes_tool_calls_in_prompt(self):
        """The LLM prompt includes tool call information."""
        agent_class = _make_agent_mock("inst", "reason", "changes")
        agent_instance = agent_class.return_value
        sys.modules["pydantic_ai"].Agent = agent_class  # type: ignore[attr-defined]

        result = _make_result(tools=["create_file", "read_file"])
        await optimize_instruction("inst", result, "criterion")

        prompt = agent_instance.run.call_args[0][0]
        assert "create_file" in prompt


class TestOptimizeInstructionImportError:
    """Test ImportError when pydantic-ai is not installed."""

    async def test_raises_import_error_when_pydantic_ai_missing(self):
        """optimize_instruction raises ImportError if pydantic-ai not installed."""
        saved = sys.modules.get("pydantic_ai")
        try:
            sys.modules["pydantic_ai"] = None  # type: ignore

            with pytest.raises(ImportError, match="pydantic-ai"):
                await optimize_instruction("inst", _make_result(), "criterion")
        finally:
            if saved is not None:
                sys.modules["pydantic_ai"] = saved
            else:
                del sys.modules["pydantic_ai"]

    async def test_import_error_includes_install_hint(self):
        """ImportError message includes the uv add install hint."""
        saved = sys.modules.get("pydantic_ai")
        try:
            sys.modules["pydantic_ai"] = None  # type: ignore

            with pytest.raises(ImportError, match="uv add pydantic-ai"):
                await optimize_instruction("inst", _make_result(), "criterion")
        finally:
            if saved is not None:
                sys.modules["pydantic_ai"] = saved
            else:
                del sys.modules["pydantic_ai"]
