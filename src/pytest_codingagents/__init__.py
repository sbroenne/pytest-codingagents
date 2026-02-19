"""pytest-codingagents — Test real coding agents via their SDK."""

from __future__ import annotations

from pytest_aitest.fixtures.llm_assert import AssertionResult, LLMAssert

from pytest_codingagents.copilot.agent import CopilotAgent
from pytest_codingagents.copilot.agents import load_custom_agent, load_custom_agents
from pytest_codingagents.copilot.result import CopilotResult

__all__ = [
    "AssertionResult",
    "CopilotAgent",
    "CopilotResult",
    "LLMAssert",
    "load_custom_agent",
    "load_custom_agents",
]
