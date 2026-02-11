"""Shared fixtures and constants for tests."""

from __future__ import annotations

# Default model — None means Copilot picks its default
DEFAULT_MODEL: str | None = None

# Models for parametrized tests
MODELS: list[str] = ["gpt-5.2", "claude-opus-4.5"]

# Timeouts
DEFAULT_TIMEOUT_S: float = 300.0

# Turn limits
DEFAULT_MAX_TURNS: int = 25
