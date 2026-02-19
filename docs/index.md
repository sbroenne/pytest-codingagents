# pytest-codingagents

**Combatting cargo cult programming in Agent Instructions, Skills, and Custom Agents for GitHub Copilot and other coding agents since 2026.**

Everyone's copying instruction files from blog posts, pasting "you are a senior engineer" into agent configs, and adding skills they found on Reddit. But does any of it actually work? Are your instructions making your coding agent better — or just longer? Is that skill helping, or is the agent ignoring it entirely?

**You don't know, because you're not testing it.**

pytest-codingagents gives you **A/B testing for coding agent configurations**. Run two configs against the same task, assert the difference, and let AI analysis tell you which one wins — and why.

Currently supports **GitHub Copilot** via [copilot-sdk](https://www.npmjs.com/package/github-copilot-sdk). More agents (Claude Code, etc.) coming soon.

```python
from pytest_codingagents import CopilotAgent

async def test_fastapi_instruction_steers_framework(copilot_run, tmp_path):
    """Does 'always use FastAPI' actually change what the agent produces?"""
    # Config A: generic instructions
    baseline = CopilotAgent(
        instructions="You are a Python developer.",
        working_directory=str(tmp_path / "a"),
    )
    # Config B: framework mandate
    with_fastapi = CopilotAgent(
        instructions="You are a Python developer. ALWAYS use FastAPI for web APIs.",
        working_directory=str(tmp_path / "b"),
    )
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()

    task = 'Create a web API with a GET /health endpoint returning {"status": "ok"}.'
    result_a = await copilot_run(baseline, task)
    result_b = await copilot_run(with_fastapi, task)

    assert result_a.success and result_b.success
    code_b = "\n".join(f.read_text() for f in (tmp_path / "b").rglob("*.py"))
    assert "fastapi" in code_b.lower(), "FastAPI instruction was ignored — the config has no effect"
```

## Install

```bash
uv add pytest-codingagents
```

Authenticate via `GITHUB_TOKEN` env var (CI) or `gh auth status` (local).

## What You Can Test

| Capability | What it proves | Guide |
|---|---|---|
| **A/B comparison** | Config B actually produces different (and better) output than Config A | [A/B Testing](how-to/ab-testing.md) |
| **Instructions** | Your custom instructions change agent behavior — not just vibes | [Getting Started](getting-started/index.md) |
| **Skills** | That domain knowledge file is helping, not being ignored | [Skill Testing](how-to/skills.md) |
| **Models** | Which model works best for your use case and budget | [Model Comparison](getting-started/model-comparison.md) |
| **Custom Agents** | Your custom agent configurations actually work as intended | [Getting Started](getting-started/index.md) |
| **MCP Servers** | The agent discovers and uses your custom tools | [MCP Server Testing](how-to/mcp-servers.md) |
| **CLI Tools** | The agent operates command-line interfaces correctly | [CLI Tool Testing](how-to/cli-tools.md) |
| **Tool Control** | Allowlists and blocklists restrict tool usage | [Tool Control](how-to/tool-control.md) |

## AI Analysis

> **See it in action:** [Basic Report](demo/basic-report.html) · [Model Comparison](demo/model-comparison-report.html) · [Instruction Testing](demo/instruction-testing-report.html)

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

- [Getting Started](getting-started/index.md) — Install and write your first test
- [How-To Guides](how-to/index.md) — Skills, MCP servers, CLI tools, and more
- [Demo Reports](demo/index.md) — See real HTML reports with AI analysis
- [API Reference](reference/api.md) — Full API documentation
