"""Result types for Copilot agent execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolCall:
    """A tool call made by Copilot."""

    name: str
    arguments: dict[str, Any] | str
    result: str | None = None
    error: str | None = None
    duration_ms: float | None = None
    tool_call_id: str | None = None

    def __repr__(self) -> str:
        status = "error" if self.error else "ok"
        timing = f", {self.duration_ms:.1f}ms" if self.duration_ms else ""
        return f"ToolCall({self.name}, {status}{timing})"


@dataclass(slots=True)
class SubagentInvocation:
    """A subagent invocation observed during execution."""

    name: str
    status: str  # "selected", "started", "completed", "failed"
    duration_ms: float | None = None

    def __repr__(self) -> str:
        return f"SubagentInvocation({self.name}, {self.status})"


@dataclass(slots=True)
class UsageInfo:
    """Token usage and cost from a single model turn."""

    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: float = 0.0


@dataclass(slots=True)
class Turn:
    """A single conversational turn."""

    role: str  # "user", "assistant", "tool"
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Get the text content of this turn."""
        return self.content

    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Turn({self.role}: {preview!r})"


@dataclass(slots=True)
class CopilotResult:
    """Result of running a prompt against GitHub Copilot.

    Captures the full event stream from the SDK, including tool calls,
    reasoning traces, subagent routing, permissions, and token usage.

    Example:
        result = await copilot_run(agent, "Create hello.py")
        assert result.success
        assert result.tool_was_called("create_file")
        assert "hello" in result.final_response.lower()
    """

    turns: list[Turn] = field(default_factory=list)
    success: bool = True
    error: str | None = None
    duration_ms: float = 0.0

    # Token usage (aggregated across all model turns)
    usage: list[UsageInfo] = field(default_factory=list)

    # Reasoning traces (from assistant.reasoning events)
    reasoning_traces: list[str] = field(default_factory=list)

    # Subagent invocations
    subagent_invocations: list[SubagentInvocation] = field(default_factory=list)

    # Permission requests (True if any were requested)
    permission_requested: bool = False
    permissions: list[dict[str, Any]] = field(default_factory=list)

    # Model actually used (from session.start or assistant.usage)
    model_used: str | None = None

    # Raw SDK events for advanced inspection
    raw_events: list[Any] = field(default_factory=list)

    @property
    def final_response(self) -> str | None:
        """Get the last assistant response."""
        for turn in reversed(self.turns):
            if turn.role == "assistant":
                return turn.content
        return None

    @property
    def all_responses(self) -> list[str]:
        """Get all assistant responses."""
        return [t.content for t in self.turns if t.role == "assistant"]

    @property
    def all_tool_calls(self) -> list[ToolCall]:
        """Get all tool calls across all turns."""
        calls = []
        for turn in self.turns:
            calls.extend(turn.tool_calls)
        return calls

    @property
    def tool_names_called(self) -> set[str]:
        """Get set of all tool names that were called."""
        return {call.name for call in self.all_tool_calls}

    def tool_was_called(self, name: str) -> bool:
        """Check if a specific tool was called."""
        return name in self.tool_names_called

    def tool_call_count(self, name: str) -> int:
        """Count how many times a specific tool was called."""
        return len(self.tool_calls_for(name))

    def tool_calls_for(self, name: str) -> list[ToolCall]:
        """Get all calls to a specific tool."""
        return [c for c in self.all_tool_calls if c.name == name]

    @property
    def total_input_tokens(self) -> int:
        """Total input tokens across all model turns."""
        return sum(u.input_tokens for u in self.usage)

    @property
    def total_output_tokens(self) -> int:
        """Total output tokens across all model turns."""
        return sum(u.output_tokens for u in self.usage)

    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output) across all model turns."""
        return self.total_input_tokens + self.total_output_tokens

    @property
    def total_cost_usd(self) -> float:
        """Total cost in USD across all model turns."""
        return sum(u.cost_usd for u in self.usage)

    @property
    def token_usage(self) -> dict[str, int]:
        """Token usage dict compatible with pytest-aitest's AgentResult."""
        return {
            "prompt_tokens": self.total_input_tokens,
            "completion_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
        }

    @property
    def cost_usd(self) -> float:
        """Cost in USD, compatible with pytest-aitest's AgentResult."""
        return self.total_cost_usd

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else f"FAILED: {self.error}"
        tools = ", ".join(sorted(self.tool_names_called)) or "none"
        cost_str = f"${self.total_cost_usd:.6f}" if self.total_cost_usd > 0 else "N/A"
        final = self.final_response or ""
        return (
            f"CopilotResult({status})\n"
            f"  Turns: {len(self.turns)}\n"
            f"  Tools called: {tools}\n"
            f"  Duration: {self.duration_ms:.0f}ms\n"
            f"  Tokens: {self.total_tokens} | Cost: {cost_str}\n"
            f"  Model: {self.model_used or 'default'}\n"
            f"  Final: {final[:100]!r}..."
        )

    def __bool__(self) -> bool:
        return self.success
