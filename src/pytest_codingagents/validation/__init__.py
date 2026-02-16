"""Validation utilities for coding agent output.

Submodules:
    context — Workspace source-file collection and transcript building.
"""

from __future__ import annotations

from pytest_codingagents.validation.context import (
    collect_source_files,
    result_to_transcript,
)

__all__: list[str] = [
    "collect_source_files",
    "result_to_transcript",
]
