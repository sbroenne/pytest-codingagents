"""Workspace context utilities for agent evaluation.

Reads source files from a workspace directory and formats them as context
for LLM-as-judge evaluation, so the judge derives ground truth from the
actual codebase rather than a hand-written answer key.

Also provides ``result_to_transcript`` for serializing
``CopilotResult`` into human-readable text for process evaluation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_codingagents.copilot.result import CopilotResult

_SOURCE_EXTENSIONS = {".py", ".toml", ".cfg", ".ini", ".yaml", ".yml", ".md"}


def collect_source_files(
    workspace: Path,
    *,
    extensions: set[str] | None = None,
    skip_dotdirs: bool = True,
) -> str:
    """Read source files from a workspace and format them for judge context.

    Walks the workspace tree, reads files matching the given extensions,
    and returns a formatted string with each file's relative path and
    content in fenced code blocks.

    Args:
        workspace: Root directory to scan.
        extensions: File extensions to include (default: Python, TOML, YAML,
            INI, CFG, Markdown).
        skip_dotdirs: Skip directories whose names start with ``.``
            (e.g. ``.git``, ``.venv``).

    Returns:
        Formatted string suitable for passing as ``context`` to
        :func:`judge_text` or :func:`judge_instruction_adherence`.
    """
    exts = extensions or _SOURCE_EXTENSIONS
    parts: list[str] = []
    for path in sorted(workspace.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in exts:
            continue
        rel = path.relative_to(workspace)
        if skip_dotdirs and any(p.startswith(".") for p in rel.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        parts.append(f"### {rel.as_posix()}\n```\n{content}\n```")
    return (
        "Here is the actual source code the agent analyzed. "
        "Use it to determine which conventions, patterns, and "
        "libraries the codebase uses.\n\n" + "\n\n".join(parts)
    )


def result_to_transcript(result: CopilotResult) -> str:
    """Serialize a CopilotResult into a human-readable transcript.

    Useful for passing to an LLM judge that evaluates agent *process*
    (tool strategy, reasoning, instruction awareness) rather than just
    the final output.

    Args:
        result: The completed agent run result.

    Returns:
        Multi-line transcript string with turns, tool calls, and
        reasoning traces.
    """
    max_tool_result_len = 2000
    lines: list[str] = []

    lines.append(f"## Agent Session (model={result.model_used or 'default'})")
    lines.append(
        f"Duration: {result.duration_ms:.0f}ms | "
        f"Turns: {len(result.turns)} | "
        f"Success: {result.success}"
    )
    if result.error:
        lines.append(f"Error: {result.error}")
    lines.append("")

    if result.reasoning_traces:
        lines.append("### Reasoning Traces")
        for i, trace in enumerate(result.reasoning_traces, 1):
            lines.append(f"  [{i}] {trace}")
        lines.append("")

    lines.append("### Conversation")
    for turn_idx, turn in enumerate(result.turns, 1):
        lines.append(f"--- Turn {turn_idx} [{turn.role}] ---")
        if turn.content:
            lines.append(turn.content)

        for tc in turn.tool_calls:
            args_str = (
                json.dumps(tc.arguments, indent=2)
                if isinstance(tc.arguments, dict)
                else str(tc.arguments)
            )
            if len(args_str) > max_tool_result_len:
                args_str = args_str[:max_tool_result_len] + "\n... (truncated)"

            lines.append(f"  >> Tool: {tc.name}")
            lines.append(f"     Args: {args_str}")

            if tc.result is not None:
                result_str = tc.result
                if len(result_str) > max_tool_result_len:
                    result_str = result_str[:max_tool_result_len] + "\n... (truncated)"
                lines.append(f"     Result: {result_str}")

            if tc.error:
                lines.append(f"     Error: {tc.error}")

        lines.append("")

    return "\n".join(lines)
