"""Instruction optimizer for test-driven prompt engineering.

Provides :func:`optimize_instruction`, which uses an LLM to analyze the gap
between a current agent instruction and the observed behavior, and suggests a
concrete improvement.

Requires ``pydantic-ai``:

    uv add pydantic-ai
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from pytest_codingagents.copilot.result import CopilotResult

__all__ = ["InstructionSuggestion", "optimize_instruction"]


@dataclass
class InstructionSuggestion:
    """A suggested improvement to a Copilot agent instruction.

    Returned by :func:`optimize_instruction`. Designed to drop into
    ``pytest.fail()`` so the failure message includes an actionable fix.

    Attributes:
        instruction: The improved instruction text to use instead.
        reasoning: Explanation of why this change would close the gap.
        changes: Short description of what was changed (one sentence).

    Example::

        suggestion = await optimize_instruction(
            agent.instructions,
            result,
            "Agent should add docstrings to all functions.",
        )
        pytest.fail(f"No docstrings found.\\n\\n{suggestion}")
    """

    instruction: str
    reasoning: str
    changes: str

    def __str__(self) -> str:
        return (
            f"💡 Suggested instruction:\n\n"
            f"  {self.instruction}\n\n"
            f"  Changes: {self.changes}\n"
            f"  Reasoning: {self.reasoning}"
        )


class _OptimizationOutput(BaseModel):
    """Structured output schema for the optimizer LLM call."""

    instruction: str
    reasoning: str
    changes: str


async def optimize_instruction(
    current_instruction: str,
    result: CopilotResult,
    criterion: str,
    *,
    model: str = "openai:gpt-4o-mini",
) -> InstructionSuggestion:
    """Analyze a result and suggest an improved instruction.

    Uses pydantic-ai structured output to analyze the gap between a
    current instruction and the agent's observed behavior, returning a
    concrete, actionable improvement.

    Designed to drop into ``pytest.fail()`` so the failure message
    contains a ready-to-use fix:

    Example::

        result = await copilot_run(agent, task)
        if '\"\"\"' not in result.file("main.py"):
            suggestion = await optimize_instruction(
                agent.instructions or "",
                result,
                "Agent should add docstrings to all functions.",
            )
            pytest.fail(f"No docstrings found.\\n\\n{suggestion}")

    Args:
        current_instruction: The agent's current instruction text.
        result: The ``CopilotResult`` from the (failed) run.
        criterion: What the agent *should* have done — the test expectation
            in plain English (e.g. ``"Always write docstrings"``).
        model: LiteLLM-style model string (e.g. ``"openai:gpt-4o-mini"``
            or ``"anthropic:claude-3-haiku-20240307"``).

    Returns:
        An :class:`InstructionSuggestion` with the improved instruction.

    Raises:
        ImportError: If pydantic-ai is not installed.
    """
    try:
        from pydantic_ai import Agent as PydanticAgent
    except ImportError as exc:
        msg = (
            "pydantic-ai is required for optimize_instruction(). "
            "Install it with: uv add pydantic-ai"
        )
        raise ImportError(msg) from exc

    final_output = result.final_response or "(no response)"
    tool_calls = ", ".join(sorted(result.tool_names_called)) or "none"

    prompt = f"""You are helping improve a GitHub Copilot agent instruction.

## Current instruction
{current_instruction or "(no instruction)"}

## Task the agent performed
{criterion}

## What actually happened
The agent produced:
{final_output[:1500]}

Tools called: {tool_calls}
Run succeeded: {result.success}

## Expected criterion
The agent SHOULD have satisfied this criterion:
{criterion}

Analyze the gap between the instruction and the observed behaviour.
Suggest a specific, concise, directive improvement to the instruction
that would make the agent satisfy the criterion.
Keep the instruction under 200 words. Do not add unrelated rules."""

    optimizer_agent = PydanticAgent(model, output_type=_OptimizationOutput)
    run_result = await optimizer_agent.run(prompt)
    output = run_result.output

    return InstructionSuggestion(
        instruction=output.instruction,
        reasoning=output.reasoning,
        changes=output.changes,
    )
