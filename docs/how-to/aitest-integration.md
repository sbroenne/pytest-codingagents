# pytest-aitest Integration

Get HTML reports with AI-powered analysis by integrating with [pytest-aitest](https://github.com/sbroenne/pytest-aitest).

## Installation

```bash
uv add "pytest-codingagents[aitest]"
```

## How It Works

When `pytest-aitest` is installed, `CopilotResult` automatically bridges to `AgentResult`, enabling:

- **HTML reports** with test results, tool call details, and Mermaid sequence diagrams
- **AI analysis** with failure root causes and improvement suggestions tailored for coding agents
- **Agent leaderboards** when comparing models or instructions
- **Dynamic pricing** — model costs pulled live from litellm for accurate cost analysis

## Usage

Use pytest-aitest's standard CLI options:

```bash
uv run pytest tests/ --aitest-html=report.html --aitest-summary-model=azure/gpt-5-mini
```

No code changes needed — the integration is automatic via the plugin system.
