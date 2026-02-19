"""pytest-codingagents — Test real coding agents via their SDK."""

from __future__ import annotations

from pytest_codingagents.copilot.agent import CopilotAgent
from pytest_codingagents.copilot.agents import load_custom_agent, load_custom_agents
from pytest_codingagents.copilot.result import CopilotResult

__all__ = [
    "CopilotAgent",
    "CopilotResult",
    "load_custom_agent",
    "load_custom_agents",
]
