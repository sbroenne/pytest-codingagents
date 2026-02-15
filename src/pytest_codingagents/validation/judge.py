"""LLM-as-judge evaluation for coding agent output.

Two-layer evaluation architecture:

* **Process evaluation** — Feeds the judge the full agent transcript
  (turns, tool calls, reasoning traces) plus the instruction text to
  evaluate whether the agent demonstrated awareness of and compliance
  with instruction rules.

* **Result evaluation** — Feeds the judge the generated artifacts plus
  the instruction text to evaluate whether output follows instruction
  rules.

Uses a separate, more capable LLM to evaluate agent-generated text and
code on structured scoring dimensions.  Cross-model judging mitigates
self-evaluation bias (judge model != agent model).

Requires the ``judge`` optional extra::

    pip install pytest-codingagents[judge]

Usage::

    from pytest_codingagents.validation.judge import (
        judge_instruction_adherence,
        judge_agent_process,
        result_to_transcript,
        ScoringDimension,
    )

    transcript = result_to_transcript(copilot_result)
    scores = await judge_agent_process(transcript, instruction_text)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

try:
    import litellm
except ImportError as exc:
    raise ImportError(
        "litellm not installed. Install with: pip install pytest-codingagents[judge]"
    ) from exc

if TYPE_CHECKING:
    from pytest_codingagents.copilot.result import CopilotResult


# ---------------------------------------------------------------------------
# Azure AD token support
# ---------------------------------------------------------------------------

_azure_ad_token_cache: str | None = None


def _get_azure_ad_token() -> str | None:
    """Obtain an Azure AD token for Cognitive Services via DefaultAzureCredential.

    Returns the token string, or None if azure-identity is not installed or
    credential acquisition fails.  Caches the token for the process lifetime
    (sufficient for test runs).
    """
    global _azure_ad_token_cache  # noqa: PLW0603
    if _azure_ad_token_cache is not None:
        return _azure_ad_token_cache

    try:
        from azure.identity import DefaultAzureCredential  # type: ignore[import-untyped]

        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        _azure_ad_token_cache = token.token
        return _azure_ad_token_cache
    except Exception:  # noqa: BLE001
        return None


def _azure_kwargs(model: str) -> dict[str, Any]:
    """Build extra kwargs for litellm when using an Azure model without an API key.

    If the model starts with ``azure/`` and no ``AZURE_API_KEY`` is set,
    automatically obtains an Azure AD token via DefaultAzureCredential.
    """
    if not model.startswith("azure/"):
        return {}

    if os.environ.get("AZURE_API_KEY"):
        return {}

    token = _get_azure_ad_token()
    if token:
        return {"azure_ad_token": token}

    return {}


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class ScoringDimension:
    """A single dimension in a scoring rubric.

    Attributes:
        name: Short identifier (e.g. ``"adherence"``).
        description: What this dimension measures.
        max_score: Maximum score for this dimension (default 5).
    """

    name: str
    description: str
    max_score: int = 5


@dataclass
class JudgeResult:
    """Structured result from an LLM judge evaluation.

    Attributes:
        scores: Per-dimension scores keyed by dimension name.
        total: Sum of all dimension scores.
        max_total: Maximum possible total score.
        reasoning: Free-text explanation from the judge.
        raw_response: The raw JSON parsed from the judge's response.
    """

    scores: dict[str, int]
    total: int
    max_total: int
    reasoning: str
    raw_response: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Transcript builder
# ---------------------------------------------------------------------------


def result_to_transcript(result: CopilotResult) -> str:
    """Serialize a CopilotResult into a human-readable transcript for the judge.

    The transcript includes conversational turns, tool calls with arguments
    and results, and reasoning traces.  Large tool results are truncated to
    keep the judge prompt within token limits.

    Args:
        result: The CopilotResult from a completed agent run.

    Returns:
        A multi-line string representing the full agent session.
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

    # Include reasoning traces if available
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


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def _build_judge_prompt(
    content: str,
    rubric: list[ScoringDimension],
    content_label: str = "content",
    context: str | None = None,
) -> str:
    """Build the evaluation prompt for the judge LLM.

    Args:
        content: The text or code to evaluate.
        rubric: List of dimensions to score on.
        content_label: How to refer to the content (e.g. ``"documentation"``, ``"code"``).
        context: Optional context about what was requested.
    """
    dimension_lines = "\n".join(
        f"{i}. **{d.name}** (1-{d.max_score}): {d.description}" for i, d in enumerate(rubric, 1)
    )
    score_keys = ", ".join(f'"{d.name}": N' for d in rubric)

    context_block = ""
    if context:
        context_block = f"\nContext about the task:\n{context}\n"

    return (
        f"Rate the following {content_label} on each dimension.\n"
        f"{context_block}\n"
        f"Rubric:\n{dimension_lines}\n\n"
        f"{content_label.capitalize()} to evaluate:\n"
        f"---\n{content}\n---\n\n"
        f"Respond ONLY with valid JSON: {{{score_keys}, "
        f'"total": N, "reasoning": "..."}}'
    )


def _build_instruction_adherence_prompt(
    content: str,
    instruction: str,
    content_label: str = "output",
) -> str:
    """Build a prompt for evaluating output adherence to an instruction file.

    The judge receives the instruction text and the generated output, then
    scores how well the output follows each rule in the instruction.
    """
    return (
        "You are evaluating whether an AI coding agent's output follows a set of "
        "instruction rules.  Read the instruction carefully, then examine the "
        "output and score adherence on each dimension.\n\n"
        "## Instruction\n"
        f"---\n{instruction}\n---\n\n"
        f"## {content_label.capitalize()} to Evaluate\n"
        f"---\n{content}\n---\n\n"
        "## Scoring Dimensions\n"
        "1. **rule_coverage** (1-5): How many of the instruction's rules are "
        "reflected in the output? 5 = all rules observed, 1 = almost none.\n"
        "2. **rule_accuracy** (1-5): For the rules the output does follow, "
        "how correctly are they applied? 5 = perfectly, 1 = incorrectly.\n"
        "3. **contamination_resistance** (1-5): Does the output avoid "
        "patterns that violate the instruction, even if the surrounding "
        "codebase uses those patterns? 5 = fully clean, 1 = copies bad patterns.\n"
        "4. **completeness** (1-5): Is the output a complete, functional "
        "artifact (not a stub or placeholder)? 5 = fully complete, 1 = empty/stub.\n\n"
        'Respond ONLY with valid JSON: {"rule_coverage": N, "rule_accuracy": N, '
        '"contamination_resistance": N, "completeness": N, '
        '"total": N, "reasoning": "..."}'
    )


def _build_process_evaluation_prompt(
    transcript: str,
    instruction: str,
) -> str:
    """Build a prompt for evaluating agent process against an instruction.

    The judge reads the full agent transcript (tool calls, reasoning, responses)
    and determines whether the agent's behavior reflects instruction awareness.
    """
    return (
        "You are evaluating an AI coding agent's *process* — not just its output, "
        "but how it worked.  Read the instruction, then examine the full session "
        "transcript and score the agent's behavior.\n\n"
        "## Instruction the Agent Received\n"
        f"---\n{instruction}\n---\n\n"
        "## Agent Session Transcript\n"
        f"---\n{transcript}\n---\n\n"
        "## Scoring Dimensions\n"
        "1. **instruction_awareness** (1-5): Does the agent show evidence of "
        "reading, referencing, or applying the instruction? 5 = clearly "
        "guided by it, 1 = completely ignores it.\n"
        "2. **tool_strategy** (1-5): Does the agent use tools purposefully — "
        "reading existing files before editing, understanding context before "
        "acting? 5 = systematic, 1 = random/chaotic.\n"
        "3. **rule_application** (1-5): When the agent makes decisions "
        "(naming, formatting, structure), do those decisions align with the "
        "instruction's rules? 5 = consistent alignment, 1 = no alignment.\n"
        "4. **error_recovery** (1-5): If the agent encounters errors or "
        "unexpected states, does it recover sensibly? 5 = graceful recovery "
        "or no errors, 1 = gives up or loops.\n\n"
        'Respond ONLY with valid JSON: {"instruction_awareness": N, '
        '"tool_strategy": N, "rule_application": N, "error_recovery": N, '
        '"total": N, "reasoning": "..."}'
    )


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)


def _extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from an LLM response.

    Handles raw JSON, JSON wrapped in markdown code fences (with or without
    a closing fence), and JSON embedded in surrounding prose.
    """
    stripped = text.strip()
    if stripped.startswith("{"):
        # May have trailing text after the JSON — find matching brace.
        return _parse_first_object(stripped)

    # Fenced code block with closing ```.
    match = _JSON_BLOCK_RE.search(text)
    if match:
        return _parse_first_object(match.group(1).strip())

    # Opening fence without a closing fence (model sometimes omits it).
    open_match = re.search(r"```(?:json)?\s*\n?(\{.*)", text, re.DOTALL)
    if open_match:
        return _parse_first_object(open_match.group(1).strip())

    # Fallback: locate the first '{' and last '}' in the text.
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last > first:
        try:
            return json.loads(text[first : last + 1])
        except json.JSONDecodeError:
            pass

    msg = f"Could not extract JSON from judge response:\n{text[:500]}"
    raise ValueError(msg)


def _parse_first_object(text: str) -> dict[str, Any]:
    """Parse the first JSON object from *text*, ignoring trailing content.

    Handles valid JSON, JSON with trailing prose, and truncated JSON
    (e.g., model response cut off mid-string by token limits).
    """
    text = text.strip()
    # Fast path: entire text is valid JSON.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Use raw_decode to parse the first JSON value, ignoring trailing text.
    idx = text.find("{")
    if idx == -1:
        raise ValueError("No JSON object found")

    decoder = json.JSONDecoder()
    try:
        obj, _ = decoder.raw_decode(text, idx)
        if isinstance(obj, dict):
            return obj
        raise ValueError(f"Expected JSON object, got {type(obj).__name__}")
    except json.JSONDecodeError:
        pass

    # First '{' to last '}' substring.
    last = text.rfind("}")
    if last > idx:
        try:
            return json.loads(text[idx : last + 1])
        except json.JSONDecodeError:
            pass

    # Truncated JSON repair: extract numeric key-value pairs with regex.
    # Handles responses cut off mid-string (e.g., inside "reasoning").
    return _repair_truncated_json(text[idx:])


_NUMERIC_KV_RE = re.compile(r'"(\w+)"\s*:\s*(\d+)')


def _repair_truncated_json(text: str) -> dict[str, Any]:
    """Extract key-value pairs from truncated JSON via regex.

    When the model's response is cut off mid-string (e.g., inside the
    "reasoning" field), standard parsers fail.  Fall back to pulling out
    all ``"key": <number>`` pairs and any complete ``"key": "value"``
    strings.
    """
    result: dict[str, Any] = {}
    for m in _NUMERIC_KV_RE.finditer(text):
        result[m.group(1)] = int(m.group(2))

    # Try to capture complete string values (non-greedy, stops at unescaped ").
    for m in re.finditer(r'"(\w+)"\s*:\s*"((?:[^"\\]|\\.)*)"', text):
        key, val = m.group(1), m.group(2)
        if key not in result:
            result[key] = val

    if not result:
        raise ValueError(f"Could not parse JSON object from: {text[:200]}")

    return result


# ---------------------------------------------------------------------------
# Default judge model — more capable than the agent model for reliable eval.
# ---------------------------------------------------------------------------

DEFAULT_JUDGE_MODEL = "azure/gpt-5.2-chat"


# ---------------------------------------------------------------------------
# Core judge functions
# ---------------------------------------------------------------------------


async def judge_text(
    text: str,
    rubric: list[ScoringDimension],
    *,
    model: str = DEFAULT_JUDGE_MODEL,
    content_label: str = "document",
    context: str | None = None,
) -> JudgeResult:
    """Evaluate text against a rubric using an LLM judge.

    Args:
        text: The text to evaluate.
        rubric: List of ScoringDimension to score against.
        model: The litellm model identifier for the judge.
        content_label: How to label the content in the prompt.
        context: Optional context about what was requested.

    Returns:
        JudgeResult with per-dimension scores and reasoning.

    Raises:
        ValueError: If the judge response cannot be parsed as JSON.
        ImportError: If litellm is not installed.
    """
    prompt = _build_judge_prompt(text, rubric, content_label, context)

    azure_kwargs = _azure_kwargs(model)
    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        **azure_kwargs,
    )

    raw_text: str = response.choices[0].message.content  # type: ignore[union-attr]
    raw = _extract_json(raw_text or "")

    scores = {d.name: int(raw.get(d.name, 0)) for d in rubric}
    total = sum(scores.values())
    max_total = sum(d.max_score for d in rubric)

    return JudgeResult(
        scores=scores,
        total=total,
        max_total=max_total,
        reasoning=str(raw.get("reasoning", "")),
        raw_response=raw,
    )


async def judge_instruction_adherence(
    content: str,
    instruction: str,
    *,
    model: str = DEFAULT_JUDGE_MODEL,
    content_label: str = "output",
) -> JudgeResult:
    """Evaluate whether generated content follows an instruction file's rules.

    Layer 2 (result evaluation): the judge receives the instruction text and
    the agent's output, then scores rule coverage, accuracy, contamination
    resistance, and completeness.

    Args:
        content: The generated artifact (code, markdown, commit message, etc.).
        instruction: The full instruction file text.
        model: The litellm model identifier for the judge.
        content_label: How to label the content in the prompt.

    Returns:
        JudgeResult with four fixed dimensions:
        ``rule_coverage``, ``rule_accuracy``, ``contamination_resistance``,
        ``completeness``.
    """
    prompt = _build_instruction_adherence_prompt(content, instruction, content_label)

    azure_kwargs = _azure_kwargs(model)
    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        **azure_kwargs,
    )

    raw_text: str = response.choices[0].message.content  # type: ignore[union-attr]
    raw = _extract_json(raw_text or "")

    dimensions = ["rule_coverage", "rule_accuracy", "contamination_resistance", "completeness"]
    scores = {d: int(raw.get(d, 0)) for d in dimensions}
    total = sum(scores.values())
    max_total = 5 * len(dimensions)

    return JudgeResult(
        scores=scores,
        total=total,
        max_total=max_total,
        reasoning=str(raw.get("reasoning", "")),
        raw_response=raw,
    )


async def judge_agent_process(
    transcript: str,
    instruction: str,
    *,
    model: str = DEFAULT_JUDGE_MODEL,
) -> JudgeResult:
    """Evaluate agent behavior from a session transcript against an instruction.

    Layer 1 (process evaluation): the judge reads the full agent transcript
    (tool calls, reasoning traces, responses) and determines whether the
    agent's workflow reflects instruction awareness.

    Args:
        transcript: Serialized agent session (from ``result_to_transcript``).
        instruction: The full instruction file text.
        model: The litellm model identifier for the judge.

    Returns:
        JudgeResult with four fixed dimensions:
        ``instruction_awareness``, ``tool_strategy``, ``rule_application``,
        ``error_recovery``.
    """
    prompt = _build_process_evaluation_prompt(transcript, instruction)

    azure_kwargs = _azure_kwargs(model)
    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        **azure_kwargs,
    )

    raw_text: str = response.choices[0].message.content  # type: ignore[union-attr]
    raw = _extract_json(raw_text or "")

    dimensions = ["instruction_awareness", "tool_strategy", "rule_application", "error_recovery"]
    scores = {d: int(raw.get(d, 0)) for d in dimensions}
    total = sum(scores.values())
    max_total = 5 * len(dimensions)

    return JudgeResult(
        scores=scores,
        total=total,
        max_total=max_total,
        reasoning=str(raw.get("reasoning", "")),
        raw_response=raw,
    )


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


def assert_judge_score(
    result: JudgeResult,
    *,
    min_total: int | None = None,
    min_dimension: dict[str, int] | None = None,
) -> None:
    """Assert judge scores meet minimum thresholds.

    Args:
        result: JudgeResult from a judge function.
        min_total: Minimum total score required.
        min_dimension: Per-dimension minimum scores.

    Raises:
        AssertionError: If any threshold is not met.
    """
    if min_total is not None:
        assert result.total >= min_total, (
            f"Total score {result.total}/{result.max_total} below minimum {min_total}. "
            f"Scores: {result.scores}. Reasoning: {result.reasoning}"
        )

    if min_dimension:
        for dim, minimum in min_dimension.items():
            actual = result.scores.get(dim, 0)
            assert actual >= minimum, (
                f"Dimension '{dim}' scored {actual}, minimum is {minimum}. "
                f"Reasoning: {result.reasoning}"
            )
