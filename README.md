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

Currently supports **GitHub Copilot** via [copilot-sdk](https://www.npmjs.com/package/github-copilot-sdk) with **IDE personas** for VS Code, Claude Code, and Copilot CLI environments.

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
| **A/B comparison** | Config B actually produces different (and better) output than Config A | [Getting Started](https://sbroenne.github.io/pytest-codingagents/getting-started/) |
| **Instruction optimization** | Turn a failing test into a ready-to-use instruction fix | [Optimize Instructions](https://sbroenne.github.io/pytest-codingagents/how-to/optimize/) |
| **Instructions** | Your custom instructions change agent behavior — not just vibes | [Getting Started](https://sbroenne.github.io/pytest-codingagents/getting-started/) |
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
