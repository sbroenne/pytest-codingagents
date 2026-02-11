"""CopilotAgent configuration for testing GitHub Copilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(slots=True, frozen=True)
class CopilotAgent:
    """Configuration for a GitHub Copilot agent test.

    Maps to the Copilot SDK's SessionConfig. Each field corresponds
    directly to an SDK capability — no wrapper indirection.

    Example:
        # Minimal
        CopilotAgent()

        # With instructions and model
        CopilotAgent(
            name="security-reviewer",
            model="claude-sonnet-4.5",
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

    # System prompt / instructions
    instructions: str | None = None
    system_message_mode: Literal["append", "replace"] = "append"

    # Context
    working_directory: str | None = None

    # Tool control
    allowed_tools: list[str] | None = None  # Allowlist (None = all)
    excluded_tools: list[str] | None = None  # Blocklist

    # Limits
    max_turns: int = 25
    timeout_s: float = 120.0

    # Permissions — auto-approve by default for deterministic testing
    auto_confirm: bool = True

    # MCP servers to attach to the session
    mcp_servers: dict[str, Any] = field(default_factory=dict)

    # Custom sub-agents
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
        """
        config: dict[str, Any] = {}

        if self.model is not None:
            config["model"] = self.model

        if self.reasoning_effort is not None:
            config["reasoningEffort"] = self.reasoning_effort

        if self.instructions:
            config["instructions"] = self.instructions

        if self.system_message_mode != "append":
            config["systemMessageMode"] = self.system_message_mode

        if self.working_directory is not None:
            config["workingDirectory"] = self.working_directory

        if self.allowed_tools is not None:
            config["availableTools"] = self.allowed_tools

        if self.excluded_tools is not None:
            config["excludedTools"] = self.excluded_tools

        config["maxTurns"] = self.max_turns

        if self.mcp_servers:
            config["mcpServers"] = self.mcp_servers

        if self.custom_agents:
            config["customAgents"] = self.custom_agents

        if self.skill_directories:
            config["skillDirectories"] = self.skill_directories

        if self.disabled_skills:
            config["disabledSkills"] = self.disabled_skills

        # Apply extra_config passthrough
        config.update(self.extra_config)

        return config
