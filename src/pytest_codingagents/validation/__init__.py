"""Validation utilities for coding agent output.

Submodules:
    context — Workspace source-file collection for judge evaluation.
    judge   — LLM-as-judge evaluation with two-layer scoring architecture.
"""

from __future__ import annotations

from pytest_codingagents.validation.context import collect_source_files

__all__: list[str] = [
    "collect_source_files",
    "JudgeResult",
    "ScoringDimension",
    "assert_judge_score",
    "judge_agent_process",
    "judge_instruction_adherence",
    "judge_text",
    "result_to_transcript",
]

_JUDGE_EXPORTS = {
    "JudgeResult",
    "ScoringDimension",
    "assert_judge_score",
    "judge_agent_process",
    "judge_instruction_adherence",
    "judge_text",
    "result_to_transcript",
}


def __getattr__(name: str) -> object:
    """Lazy import judge symbols so litellm is only loaded on first use."""
    if name in _JUDGE_EXPORTS:
        from pytest_codingagents.validation import judge as _judge  # noqa: F811

        return getattr(_judge, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
