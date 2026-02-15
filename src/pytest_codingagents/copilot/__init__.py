"""GitHub Copilot provider for pytest-codingagents."""

from __future__ import annotations

from pytest_codingagents.copilot.agent import CopilotAgent
from pytest_codingagents.copilot.agents import load_custom_agent, load_custom_agents
from pytest_codingagents.copilot.fixtures import copilot_run
from pytest_codingagents.copilot.result import CopilotResult
from pytest_codingagents.copilot.runner import run_copilot

__all__ = [
    "CopilotAgent",
    "CopilotResult",
    "copilot_run",
    "load_custom_agent",
    "load_custom_agents",
    "run_copilot",
]
