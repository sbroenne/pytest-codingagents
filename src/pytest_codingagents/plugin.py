"""pytest-codingagents plugin registration.

Registered as a pytest plugin via the ``pytest11`` entry point in
pyproject.toml. Provides the ``copilot_run`` fixture and ``copilot`` marker.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Re-export the fixture so pytest discovers it via the plugin entry point.
from pytest_codingagents.copilot.fixtures import copilot_run

__all__ = ["copilot_run"]

_ANALYSIS_PROMPT_PATH = Path(__file__).parent / "prompts" / "coding_agent_analysis.md"


def pytest_configure(config: object) -> None:
    """Register markers for coding agent tests."""
    from _pytest.config import Config

    assert isinstance(config, Config)
    config.addinivalue_line(
        "markers",
        "copilot: mark test as requiring GitHub Copilot SDK credentials",
    )


@pytest.hookimpl(optionalhook=True)
def pytest_aitest_analysis_prompt(config: object) -> str | None:
    """Provide coding-agent-specific analysis prompt for AI insights.

    This hook is called by pytest-aitest when generating AI-powered
    report insights. We return a prompt tailored for evaluating coding
    agents (models, instructions, skills, tools) rather than the default
    prompt which frames the agent as a test harness.

    The ``{{PRICING_TABLE}}`` placeholder is replaced with a live
    pricing table built from litellm's ``model_cost`` data.
    """
    if _ANALYSIS_PROMPT_PATH.exists():
        prompt = _ANALYSIS_PROMPT_PATH.read_text(encoding="utf-8")
        if "{{PRICING_TABLE}}" in prompt:
            prompt = prompt.replace("{{PRICING_TABLE}}", _build_pricing_table())
        return prompt
    return None


def _build_pricing_table() -> str:
    """Build a markdown pricing table from litellm's model_cost map.

    Returns a table of common coding-agent models with their per-token
    pricing, pulled live from litellm so it stays current.
    """
    try:
        from litellm import model_cost
    except ImportError:
        return "*Pricing data unavailable (litellm not installed).*"

    # Models we care about — bare names (no provider prefix).
    # Listed from cheapest to most expensive.
    models_of_interest = [
        "gpt-4.1-nano",
        "gpt-5-nano",
        "gpt-4.1-mini",
        "gpt-5-mini",
        "gpt-4.1",
        "gpt-5",
        "gpt-5.1",
        "gpt-5.2",
        "claude-sonnet-4",
        "claude-sonnet-4-5",
        "claude-opus-4-5",
        "claude-opus-4-6",
        "gpt-5-pro",
        "gpt-5.2-pro",
    ]

    rows: list[str] = []
    for name in models_of_interest:
        info = model_cost.get(name) or model_cost.get(f"azure/{name}", {})
        ic = info.get("input_cost_per_token", 0) or 0
        oc = info.get("output_cost_per_token", 0) or 0
        if ic == 0 and oc == 0:
            continue
        rows.append(f"| {name} | ${ic * 1_000_000:.2f} | ${oc * 1_000_000:.2f} |")

    if not rows:
        return "*No model pricing data available from litellm.*"

    header = (
        "**Model pricing reference** ($/M tokens, from litellm):\n\n"
        "| Model | Input $/M | Output $/M |\n"
        "|-------|-----------|------------|\n"
    )
    return header + "\n".join(rows)
