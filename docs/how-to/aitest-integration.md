# pytest-aitest Integration

HTML reports with AI-powered analysis are included automatically — [pytest-aitest](https://github.com/sbroenne/pytest-aitest) is a core dependency.

> **See example reports:** [Basic Report](../demo/basic-report.html) · [Model Comparison](../demo/model-comparison-report.html) · [Instruction Testing](../demo/instruction-testing-report.html)

## How It Works

When tests run, `CopilotResult` automatically bridges to `AgentResult`, enabling:

- **HTML reports** with test results, tool call details, and Mermaid sequence diagrams
- **AI analysis** with failure root causes and improvement suggestions tailored for coding agents
- **Agent leaderboards** when comparing models or instructions
- **Dynamic pricing** — model costs pulled live from litellm for accurate cost analysis

## Usage

Use pytest-aitest's standard CLI options:

```bash
uv run pytest tests/ --aitest-html=report.html --aitest-summary-model=azure/gpt-5-mini
```

Or configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = """
    --aitest-html=aitest-reports/report.html
    --aitest-summary-model=azure/gpt-5.2-chat
"""
```

No code changes needed — the integration is automatic via the plugin system.

## Analysis Prompt Hook

The plugin implements the `pytest_aitest_analysis_prompt` hook to inject Copilot-specific context into AI analysis:

- **Coding-agent framing** — the AI analyzer understands it's evaluating models, instructions, and tools (not MCP servers)
- **Dynamic pricing table** — model pricing data is pulled live from litellm's `model_cost` database, so cost analysis stays current without manual updates

This happens automatically — no configuration needed.
