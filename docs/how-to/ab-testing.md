# A/B Testing Agent Configs

The core use case of pytest-codingagents is **A/B testing**: run the same task with two different agent configurations and prove that one produces measurably better output than the other.

This stops cargo cult configuration — copying instructions and skills from blog posts without knowing if they work.

## The Pattern

Every A/B test follows the same structure:

```python
from pytest_codingagents import CopilotAgent


async def test_config_a_vs_config_b(copilot_run, tmp_path):
    config_a = CopilotAgent(
        name="baseline",
        instructions="...",          # Config A
        working_directory=str(tmp_path / "a"),
    )
    config_b = CopilotAgent(
        name="treatment",
        instructions="...",          # Config B — the change you're testing
        working_directory=str(tmp_path / "b"),
    )
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()

    task = "Create calculator.py with add(a, b) and subtract(a, b)."
    result_a = await copilot_run(config_a, task)
    result_b = await copilot_run(config_b, task)

    assert result_a.success and result_b.success

    # Assert the configs produced DIFFERENT, OBSERVABLE outputs
    content_a = (tmp_path / "a" / "calculator.py").read_text()
    content_b = (tmp_path / "b" / "calculator.py").read_text()
    assert '"""' not in content_a   # baseline: no docstrings
    assert '"""' in content_b       # treatment: docstrings present
```

**The key rule**: assert something that is present in Config B *because of the change* and absent (or different) in Config A.

---

## Testing Instructions

Does adding a documentation mandate actually change the code written?

```python
async def test_framework_instruction_steers_choice(copilot_run, tmp_path):
    baseline = CopilotAgent(
        name="generic",
        instructions="You are a Python developer.",
        working_directory=str(tmp_path / "a"),
    )
    with_fastapi = CopilotAgent(
        name="fastapi",
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
    assert "fastapi" in code_b.lower(), "FastAPI instruction was ignored"
```

---

## Testing Skills

Does adding a skill file actually change what the agent produces compared to the same task without it?

```python
async def test_exports_skill_adds_all_declaration(copilot_run, tmp_path):
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    (skill_dir / "module-exports.md").write_text(
        "# Module Export Standards\n\n"
        "Every Python module MUST declare its public API using __all__.\n"
        '__all__ = ["FunctionName"]\n\n'
        "Modules without __all__ are considered incomplete.\n"
    )

    task = "Create math_utils.py with add(a, b) and subtract(a, b)."

    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    baseline = CopilotAgent(
        name="baseline",
        instructions="Write a Python module.",
        working_directory=str(baseline_dir),
    )

    treatment_dir = tmp_path / "treatment"
    treatment_dir.mkdir()
    treatment = CopilotAgent(
        name="treatment",
        instructions="Write a Python module. Apply all module export standards from your skills.",
        working_directory=str(treatment_dir),
        skill_directories=[str(skill_dir)],
    )

    result_a = await copilot_run(baseline, task)
    result_b = await copilot_run(treatment, task)

    assert result_a.success and result_b.success

    content_a = (baseline_dir / "math_utils.py").read_text()
    content_b = (treatment_dir / "math_utils.py").read_text()

    assert "__all__" not in content_a, "Baseline should not have __all__ (LLM default)"
    assert "__all__" in content_b, "Skill should have added __all__ declaration"
```

---

## Testing Models

Which model follows instructions more reliably?

```python
import pytest
from pytest_codingagents import CopilotAgent

MODELS = ["claude-opus-4.5", "gpt-5.2"]


@pytest.mark.parametrize("model", MODELS)
async def test_model_follows_defensive_instructions(copilot_run, tmp_path, model):
    agent = CopilotAgent(
        name=f"model-{model}",
        model=model,
        instructions=(
            "Always write defensive Python. "
            "All I/O operations MUST use try/except. Never let exceptions propagate uncaught."
        ),
        working_directory=str(tmp_path),
    )
    result = await copilot_run(
        agent, "Create file_reader.py with read_json(path) that returns parsed JSON."
    )
    assert result.success
    content = (tmp_path / "file_reader.py").read_text()
    assert "try" in content and "except" in content, (
        f"Model {model} ignored defensive coding instructions"
    )
```

The AI analysis report will produce a leaderboard showing which model followed instructions most reliably.

---

## Choosing Good Assertions

The hardest part of A/B testing is finding an observable signal that reliably differs between configs.

| What you're testing | Good signal | Fragile signal |
|---|---|---|
| Docstring instructions | `'"""' in content` / `'"""' not in content` | Token count |
| Framework choice | `"fastapi" in code.lower()` | File count |
| Skills (module exports) | `"__all__" in content` | Code length |
| Skills (`__version__`) | `"__version__" in content` | Pass/fail alone |
| Error handling | `"try" in content and "except" in content` | `result.success` |
| Tool restrictions | `not result.tool_was_called("run_in_terminal")` | Turn count |

**Avoid** asserting only `result.success` — both configs will usually succeed. The point is to prove they produce *different* output.

---

## Reading the AI Report

After running A/B tests, generate the HTML report:

```bash
uv run pytest tests/ -m copilot --aitest-html=report.html --aitest-summary-model=azure/gpt-5.2-chat
```

The report will:

- **Rank configs** by pass rate in a leaderboard
- **Highlight differences** in tool usage, turn count, and token consumption
- **Diagnose failures** — if Config B fails and Config A passes, the AI explains why
- **Recommend improvements** — actionable changes to instructions, skills, or model choice
