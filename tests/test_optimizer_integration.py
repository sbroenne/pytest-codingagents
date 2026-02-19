"""Integration tests for optimize_instruction().

These tests require:
- GitHub Copilot credentials (for copilot_run to produce a real result)
- AZURE_OPENAI_ENDPOINT env var set (for the optimizer LLM via Azure Entra ID)

Skipped automatically when AZURE_OPENAI_ENDPOINT is absent.
"""

from __future__ import annotations

import os

import pytest

from pytest_codingagents.copilot.agent import CopilotAgent
from pytest_codingagents.copilot.optimizer import (
    InstructionSuggestion,
    azure_entra_model,
    optimize_instruction,
)


def _model():
    """Build Azure Entra ID model for optimizer tests."""
    return azure_entra_model()  # defaults to gpt-5.2-chat


@pytest.mark.copilot
class TestOptimizeInstructionIntegration:
    """Integration tests for optimize_instruction() with real Azure LLM calls."""

    @pytest.fixture(autouse=True)
    def require_azure_endpoint(self):
        """Skip entire class when AZURE_OPENAI_ENDPOINT is not set."""
        if not os.environ.get("AZURE_OPENAI_ENDPOINT"):
            pytest.skip("AZURE_OPENAI_ENDPOINT not set — skipping optimizer integration tests")

    async def test_returns_valid_suggestion(self, copilot_run, tmp_path):
        """optimize_instruction returns an InstructionSuggestion with non-empty fields."""
        agent = CopilotAgent(
            name="minimal-coder",
            instructions="Write Python code.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Create calc.py with add(a, b) and subtract(a, b).",
        )
        assert result.success

        suggestion = await optimize_instruction(
            agent.instructions or "",
            result,
            "Every function must have a Google-style docstring.",
            model=_model(),
        )

        assert isinstance(suggestion, InstructionSuggestion)
        assert suggestion.instruction.strip(), "Suggestion instruction must not be empty"
        assert suggestion.reasoning.strip(), "Suggestion reasoning must not be empty"
        assert suggestion.changes.strip(), "Suggestion changes must not be empty"
        assert len(suggestion.instruction) > 20, "Instruction too short to be useful"

    async def test_suggestion_str_is_human_readable(self, copilot_run, tmp_path):
        """str(InstructionSuggestion) is readable and contains all fields."""
        agent = CopilotAgent(
            name="coder",
            instructions="Write Python code.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(agent, "Create utils.py with a helper function.")
        assert result.success

        suggestion = await optimize_instruction(
            agent.instructions or "",
            result,
            "Add type hints to all function parameters and return values.",
            model=_model(),
        )

        text = str(suggestion)
        assert suggestion.instruction in text
        assert suggestion.reasoning in text
        assert suggestion.changes in text

    async def test_suggestion_is_relevant_to_criterion(self, copilot_run, tmp_path):
        """Optimizer returns a suggestion that addresses the given criterion."""
        agent = CopilotAgent(
            name="coder",
            instructions="Write Python code.",
            working_directory=str(tmp_path),
        )
        result = await copilot_run(
            agent,
            "Create math.py with add(a, b) and multiply(a, b).",
        )
        assert result.success

        criterion = "All functions must include Google-style docstrings."
        suggestion = await optimize_instruction(
            agent.instructions or "",
            result,
            criterion,
            model=_model(),
        )

        # The suggestion instruction should mention docstrings somehow
        combined = (suggestion.instruction + " " + suggestion.reasoning).lower()
        assert any(word in combined for word in ["docstring", "doc", "documentation", "google"]), (
            f"Suggestion doesn't address 'docstring' criterion.\n"
            f"Instruction: {suggestion.instruction}\n"
            f"Reasoning: {suggestion.reasoning}"
        )
