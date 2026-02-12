"""CopilotAgent configuration for testing GitHub Copilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(slots=True, frozen=True)
class CopilotAgent:
    """Configuration for a GitHub Copilot agent test.

    Maps to the Copilot SDK's ``SessionConfig``. User-facing field names
    are kept intuitive (e.g. ``instructions``), while
    ``build_session_config()`` maps them to the SDK's actual
    ``system_message`` TypedDict.

    The SDK's ``SessionConfig`` has no ``maxTurns`` field — turn limits
    are enforced externally by the runner via ``timeout_s``.

    Example:
        # Minimal
        CopilotAgent()

        # With instructions and model
        CopilotAgent(
            name="security-reviewer",
            model="claude-sonnet-4",
            instructions="Review code for security vulnerabilities.",
        )

        # With custom tools and references
        CopilotAgent(
            name="file-creator",
            instructions="Create files as requested.",
            working_directory="/tmp/workspace",
            allowed_tools=["create_file", "read_file"],
        )
    """

    # Identity
    name: str = "copilot"

    # Model selection (None = Copilot's default)
    model: str | None = None
    reasoning_effort: Literal["low", "medium", "high", "xhigh"] | None = None

    # System message content — maps to SDK's system_message.content
    # In the Copilot SDK, this is NOT a "system prompt" — it's instructions
    # appended to (or replacing) the CLI's built-in system message.
    instructions: str | None = None
    system_message_mode: Literal["append", "replace"] = "append"

    # Context
    working_directory: str | None = None

    # Tool control
    allowed_tools: list[str] | None = None  # Allowlist (None = all)
    excluded_tools: list[str] | None = None  # Blocklist

    # Limits — enforced by the runner, NOT part of SDK SessionConfig
    max_turns: int = 25
    timeout_s: float = 300.0

    # Permissions — auto-approve by default for deterministic testing
    auto_confirm: bool = True

    # MCP servers to attach to the session
    mcp_servers: dict[str, Any] = field(default_factory=dict)

    # Custom agents (SDK CustomAgentConfig: name, prompt, description,
    # display_name, tools, mcp_servers, infer)
    custom_agents: list[dict[str, Any]] = field(default_factory=list)

    # Skill directories
    skill_directories: list[str] = field(default_factory=list)
    disabled_skills: list[str] = field(default_factory=list)

    # SDK passthrough for unmapped fields
    extra_config: dict[str, Any] = field(default_factory=dict)

    def build_session_config(self) -> dict[str, Any]:
        """Build a SessionConfig dict for the Copilot SDK.

        Returns a dict compatible with ``CopilotClient.create_session()``.
        Only includes non-None/non-default fields to avoid overriding
        SDK defaults.

        SDK field mapping (Python snake_case TypedDict keys):
            instructions → system_message: {mode, content}
            allowed_tools → available_tools
            excluded_tools → excluded_tools
            reasoning_effort → reasoning_effort
            working_directory → working_directory
            mcp_servers → mcp_servers
            custom_agents → custom_agents
            skill_directories → skill_directories
            disabled_skills → disabled_skills

        Note: ``max_turns`` is NOT part of ``SessionConfig`` — the runner
        enforces turn limits externally.
        """
        config: dict[str, Any] = {}

        if self.model is not None:
            config["model"] = self.model

        if self.reasoning_effort is not None:
            config["reasoning_effort"] = self.reasoning_effort

        # Map instructions + system_message_mode → SDK's system_message
        if self.instructions:
            config["system_message"] = {
                "mode": self.system_message_mode,
                "content": self.instructions,
            }

        if self.working_directory is not None:
            config["working_directory"] = self.working_directory

        if self.allowed_tools is not None:
            config["available_tools"] = self.allowed_tools

        if self.excluded_tools is not None:
            config["excluded_tools"] = self.excluded_tools

        if self.mcp_servers:
            config["mcp_servers"] = self.mcp_servers

        if self.custom_agents:
            config["custom_agents"] = self.custom_agents

        if self.skill_directories:
            config["skill_directories"] = self.skill_directories

        if self.disabled_skills:
            config["disabled_skills"] = self.disabled_skills

        # Apply extra_config passthrough
        config.update(self.extra_config)

        return config
