# pytest-codingagents

**Combatting cargo cult programming in Agent Instructions, Skills, and Custom Agents for GitHub Copilot and other coding agents since 2026.**

Everyone's copying instruction files from blog posts, pasting "you are a senior engineer" into agent configs, and adding skills they found on Reddit. But does any of it actually work? Are your instructions making your coding agent better — or just longer? Is that skill helping, or is the agent ignoring it entirely?

**You don't know, because you're not testing it.**

pytest-codingagents is a pytest plugin that runs your actual coding agent configuration against real tasks — then uses AI analysis to tell you **why** things failed and **what to fix**.

Currently supports **GitHub Copilot** via [copilot-sdk](https://www.npmjs.com/package/github-copilot-sdk). More agents (Claude Code, etc.) coming soon.

```python
from pytest_codingagents import CopilotAgent

async def test_create_file(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Create files as requested.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create hello.py with print('hello')")
    assert result.success
    assert result.tool_was_called("create_file")
```

## Install

```bash
uv add pytest-codingagents
```

Authenticate via `GITHUB_TOKEN` env var (CI) or `gh auth status` (local).

## What You Can Test

| Capability | What it proves | Guide |
|---|---|---|
| **Instructions** | Your custom instructions actually produce the desired behavior — not just vibes | [Getting Started](https://sbroenne.github.io/pytest-codingagents/getting-started/) |
| **Skills** | That domain knowledge file is helping, not being ignored | [Skill Testing](https://sbroenne.github.io/pytest-codingagents/how-to/skills/) |
| **Models** | Which model works best for your use case and budget | [Model Comparison](https://sbroenne.github.io/pytest-codingagents/getting-started/model-comparison/) |
| **Custom Agents** | Your custom agent configurations actually work as intended | [Getting Started](https://sbroenne.github.io/pytest-codingagents/getting-started/) |
| **MCP Servers** | The agent discovers and uses your custom tools | [MCP Server Testing](https://sbroenne.github.io/pytest-codingagents/how-to/mcp-servers/) |
| **CLI Tools** | The agent operates command-line interfaces correctly | [CLI Tool Testing](https://sbroenne.github.io/pytest-codingagents/how-to/cli-tools/) |

## AI Analysis

> **See it in action:** [Basic Report](https://sbroenne.github.io/pytest-codingagents/demo/basic-report.html) · [Model Comparison](https://sbroenne.github.io/pytest-codingagents/demo/model-comparison-report.html) · [Instruction Testing](https://sbroenne.github.io/pytest-codingagents/demo/instruction-testing-report.html)

Every test run produces an HTML report with AI-powered insights:

- **Diagnoses failures** — root cause analysis with suggested fixes
- **Compares models** — leaderboards ranked by pass rate and cost
- **Evaluates instructions** — which instructions produce better results
- **Recommends improvements** — actionable changes to tools, instructions, and skills

```bash
uv run pytest tests/ --aitest-html=report.html --aitest-summary-model=azure/gpt-5.2-chat
```

## Documentation

Full docs at **[sbroenne.github.io/pytest-codingagents](https://sbroenne.github.io/pytest-codingagents/)** — API reference, how-to guides, and demo reports.

## License

MIT
