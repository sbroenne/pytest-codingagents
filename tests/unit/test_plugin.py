"""Unit tests for the pytest-codingagents plugin hookimpl."""

from __future__ import annotations

from pytest_codingagents.plugin import pytest_aitest_analysis_prompt


class TestAnalysisPromptHook:
    """Tests for the pytest_aitest_analysis_prompt hookimpl."""

    def test_returns_prompt_content(self) -> None:
        """Hook returns non-None string with prompt content."""
        result = pytest_aitest_analysis_prompt(config=None)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 500

    def test_prompt_has_coding_agent_framing(self) -> None:
        """Prompt uses coding-agent framing, not the default aitest framing."""
        result = pytest_aitest_analysis_prompt(config=None)
        assert result is not None
        assert "coding agent" in result.lower()

    def test_prompt_has_required_sections(self) -> None:
        """Prompt contains all expected analysis sections."""
        result = pytest_aitest_analysis_prompt(config=None)
        assert result is not None
        for section in [
            "Executive Summary",
            "Failure Analysis",
            "Model Comparison",
            "Instruction Effectiveness",
            "Tool Usage",
        ]:
            assert section in result, f"Missing section: {section}"

    def test_hookimpl_is_optional(self) -> None:
        """The hookimpl uses optionalhook=True for cross-plugin compatibility."""
        # The function should have the hookimpl marker with optionalhook=True
        marker = getattr(pytest_aitest_analysis_prompt, "pytest_impl", None)
        assert marker is not None
        assert marker.get("optionalhook") is True
