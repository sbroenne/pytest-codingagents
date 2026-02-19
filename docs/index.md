# pytest-codingagents

**Test-driven prompt engineering for GitHub Copilot.**

Everyone copies instruction files from blog posts, adds "you are a senior engineer" to agent configs, and includes skills found on Reddit. But does any of it work? Are your instructions making your agent better — or just longer?

**You don't know, because you're not testing it.**

pytest-codingagents gives you a complete **test→optimize→test loop** for GitHub Copilot configurations:

1. **Write a test** — define what the agent *should* do
2. **Run it** — see it fail (or pass)
3. **Optimize** — call `optimize_instruction()` to get a concrete suggestion
4. **A/B confirm** — use `ab_run` to prove the change actually helps
5. **Ship it** — you now have evidence, not vibes

Currently supports **GitHub Copilot** via [copilot-sdk](https://www.npmjs.com/package/github-copilot-sdk). More agents (Claude Code, etc.) coming soon.

```python
from pytest_codingagents import CopilotAgent, optimize_instruction
import pytest


async def test_docstring_instruction_works(ab_run):
    """Prove the docstring instruction actually changes output, and get a fix if it doesn't."""
    baseline = CopilotAgent(instructions="Write Python code.")
    treatment = CopilotAgent(
        instructions="Write Python code. Add Google-style docstrings to every function."
    )

    b, t = await ab_run(baseline, treatment, "Create math.py with add(a, b) and subtract(a, b).")

    assert b.success and t.success

    if '"""' not in t.file("math.py"):
        suggestion = await optimize_instruction(
            treatment.instructions or "",
            t,
            "Agent should add docstrings to every function.",
        )
        pytest.fail(f"Docstring instruction was ignored.\n\n{suggestion}")

    assert '"""' not in b.file("math.py"), "Baseline should not have docstrings"
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
| **Instruction optimization** | Turn a failing test into a ready-to-use instruction fix | [Optimize Instructions](how-to/optimize.md) |
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
- [How-To Guides](how-to/index.md) — A/B testing, instruction optimization, skills, MCP, and more
- [Demo Reports](demo/index.md) — See real HTML reports with AI analysis
- [API Reference](reference/api.md) — Full API documentation
