"""Validation utilities for coding agent output.

Submodules:
    context — Workspace source-file collection for judge evaluation.
    judge   — LLM-as-judge evaluation with two-layer scoring architecture.
"""

from __future__ import annotations

from pytest_codingagents.validation.context import collect_source_files

__all__: list[str] = [
    "collect_source_files",
]

# Lazy re-exports — only available when the judge extra is installed.
try:
    from pytest_codingagents.validation.judge import (
        JudgeResult,
        ScoringDimension,
        assert_judge_score,
        judge_agent_process,
        judge_instruction_adherence,
        judge_text,
        result_to_transcript,
    )

    __all__ += [
        "JudgeResult",
        "ScoringDimension",
        "assert_judge_score",
        "judge_agent_process",
        "judge_instruction_adherence",
        "judge_text",
        "result_to_transcript",
    ]
except ImportError:
    pass
