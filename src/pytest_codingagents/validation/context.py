"""Workspace context utilities for judge evaluation.

Reads source files from a workspace directory and formats them as context
for LLM-as-judge evaluation, so the judge derives ground truth from the
actual codebase rather than a hand-written answer key.
"""

from __future__ import annotations

from pathlib import Path

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
