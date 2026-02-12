# pytest-codingagents

Automated testing for GitHub Copilot configurations. Test your instructions, MCP servers, skills, and models — then get AI analysis that tells you **why** things failed and **what to fix**.

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
| **Instructions** | Custom instructions produce the desired behavior | [Getting Started](getting-started/index.md) |
| **Models** | Which model works best for your use case and budget | [Model Comparison](getting-started/model-comparison.md) |
| **MCP Servers** | The agent discovers and uses your custom tools | [MCP Server Testing](how-to/mcp-servers.md) |
| **Skills** | Domain knowledge improves agent performance | [Skill Testing](how-to/skills.md) |
| **CLI Tools** | The agent operates command-line interfaces correctly | [CLI Tool Testing](how-to/cli-tools.md) |
| **Tool Control** | Allowlists and blocklists restrict tool usage | [Tool Control](how-to/tool-control.md) |

## AI Analysis

> **See it in action:** [Basic Report](demo/basic-report.html) · [Model Comparison](demo/model-comparison-report.html) · [Instruction Testing](demo/instruction-testing-report.html)

Every test run produces an HTML report with AI-powered insights:

- **Diagnoses failures** — root cause analysis with suggested fixes
- **Compares models** — leaderboards ranked by pass rate and cost
- **Evaluates instructions** — which instructions produce better results
- **Recommends improvements** — actionable changes to tools, prompts, and skills

```bash
uv run pytest tests/ --aitest-html=report.html --aitest-summary-model=azure/gpt-5.2-chat
```

## Next Steps

- [Getting Started](getting-started/index.md) — Install and write your first test
- [How-To Guides](how-to/index.md) — MCP servers, skills, CLI tools, and more
- [Demo Reports](demo/index.md) — See real HTML reports with AI analysis
- [API Reference](reference/api.md) — Full API documentation
