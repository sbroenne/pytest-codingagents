# Optimizing Instructions with AI

`optimize_instruction()` closes the test→optimize→test loop.

When a test fails — the agent ignored an instruction or produced unexpected output — call `optimize_instruction()` to get a concrete, LLM-generated suggestion for improving the instruction. Drop the suggestion into `pytest.fail()` so the test failure message includes a ready-to-use fix.

## The Loop

```
write test → run → fail → optimize → update instruction → run → pass
```

This is **test-driven prompt engineering**: your tests define the standard; the optimizer helps you reach it.

## Basic Usage

```python
import pytest
from pytest_codingagents import CopilotAgent, optimize_instruction


async def test_docstring_instruction(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Write Python code.",
        working_directory=str(tmp_path),
    )

    result = await copilot_run(agent, "Create math.py with add(a, b) and subtract(a, b).")

    if '"""' not in result.file("math.py"):
        suggestion = await optimize_instruction(
            agent.instructions or "",
            result,
            "Agent should add Google-style docstrings to every function.",
        )
        pytest.fail(f"No docstrings found.\n\n{suggestion}")
```

The failure message will look like:

```
FAILED test_math.py::test_docstring_instruction

No docstrings found.

💡 Suggested instruction:

  Write Python code. Add Google-style docstrings to every function.
  The docstring should describe what the function does, its parameters (Args:),
  and its return value (Returns:).

  Changes: Added explicit docstring format mandate with Args/Returns sections.
  Reasoning: The original instruction did not mention documentation. The agent
  produced code without docstrings because there was no requirement to add them.
```

## With A/B Testing

Pair `optimize_instruction()` with `ab_run` to test the fix before committing:

```python
import pytest
from pytest_codingagents import CopilotAgent, optimize_instruction


async def test_docstring_instruction_iterates(ab_run, tmp_path):
    baseline = CopilotAgent(instructions="Write Python code.")
    treatment = CopilotAgent(
        instructions="Write Python code. Add Google-style docstrings to every function."
    )

    b, t = await ab_run(baseline, treatment, "Create math.py with add(a, b).")

    assert b.success and t.success

    if '"""' not in t.file("math.py"):
        suggestion = await optimize_instruction(
            treatment.instructions or "",
            t,
            "Treatment agent should add docstrings — treatment instruction did not work.",
        )
        pytest.fail(f"Treatment still no docstrings.\n\n{suggestion}")

    # Confirm baseline does NOT have docstrings (differential assertion)
    assert '"""' not in b.file("math.py"), "Baseline unexpectedly has docstrings"
```

## API Reference

::: pytest_aitest.execution.optimizer.optimize_instruction

---

::: pytest_aitest.execution.optimizer.InstructionSuggestion

## Choosing a Model

`optimize_instruction()` defaults to `openai:gpt-4o-mini` — cheap, fast, and precise enough for instruction analysis.

Override with the `model` keyword argument:

```python
suggestion = await optimize_instruction(
    agent.instructions or "",
    result,
    "Agent should use type hints.",
    model="anthropic:claude-3-haiku-20240307",
)
```

Any [LiteLLM-compatible](https://docs.litellm.ai/docs/providers) model string works.

## The Criterion

Write the `criterion` as a plain-English statement of what the agent *should* have done:

| Situation | Good criterion |
|-----------|----------------|
| Missing docstrings | `"Agent should add Google-style docstrings to every function."` |
| Wrong framework | `"Agent should use FastAPI, not Flask."` |
| Missing type hints | `"All function signatures must include type annotations."` |
| No error handling | `"All I/O operations must be wrapped in try/except."` |

The more specific the criterion, the more actionable the suggestion.
