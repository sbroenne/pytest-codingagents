# Assertions

Two complementary assertion styles work together in pytest-codingagents:

- **File helpers** — read files the agent created/modified directly from `CopilotResult`
- **Semantic assertions** — evaluate content with a plain-English criterion via an LLM judge

## File helpers

The agent runs in `working_directory`. File helpers let you read the results
without threading `tmp_path` through every test.

```python
# Read a file the agent created
content = result.file("main.py")

# Check existence
assert result.file_exists("main.py")

# Find files by pattern (glob, recursive)
py_files = result.files_matching("**/*.py")
assert py_files, "No Python files were created"

test_files = result.files_matching("test_*.py")
assert test_files, "No test file was created"
```

All paths are relative to `agent.working_directory`. The methods raise
`FileNotFoundError` if a file doesn't exist (useful for asserting creation).

## Semantic assertions with `llm_assert`

`llm_assert` is a pytest fixture from pytest-aitest, auto-available in every
test. It evaluates text against a plain-English criterion using a cheap judge
model (`gpt-5-mini` by default).

```python
async def test_calculator(copilot_run, llm_assert, tmp_path):
    agent = CopilotAgent(
        instructions="Write fully documented Python with Google-style docstrings.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create calculator.py with add and subtract.")

    assert result.success
    content = result.file("calculator.py")
    assert llm_assert(content, "has Google-style docstrings with Args: and Returns: sections")
```

`llm_assert(text, criterion)` returns an `AssertionResult` that:
- Is truthy/falsy (works with `assert`)
- Has a rich `repr` showing pass/fail, the criterion, and the judge's reasoning

```
LLMAssert(FAIL: 'has Google-style docstrings with Args: and Returns: sections')
  Content: 'def add(a, b):\n    return a + b\n...'
  Reasoning: The function has no docstring at all.
```

## Combining both in A/B tests

```python
@pytest.mark.copilot
async def test_docstring_instruction_adds_docs(copilot_run, llm_assert, tmp_path):
    """A/B: docstring instruction vs. no instruction."""
    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    treatment_dir = tmp_path / "treatment"
    treatment_dir.mkdir()

    baseline = CopilotAgent(working_directory=str(baseline_dir))
    treatment = CopilotAgent(
        working_directory=str(treatment_dir),
        instructions="Every function MUST have a Google-style docstring.",
    )

    task = "Create calculator.py with add(a, b) and subtract(a, b)."
    baseline_result = await copilot_run(baseline, task)
    treatment_result = await copilot_run(treatment, task)

    assert baseline_result.success
    assert treatment_result.success

    # Baseline: no instruction → likely no docstrings
    baseline_content = baseline_result.file("calculator.py")
    # Treatment: instruction → must have docstrings
    treatment_content = treatment_result.file("calculator.py")
    assert llm_assert(
        treatment_content,
        "has Google-style docstrings with Args: and Returns: sections",
    ), "Treatment did not produce docstrings despite instruction"
```

## `LLMAssert` standalone (no fixture)

For use outside of test functions (e.g. helper modules), import `LLMAssert` directly:

```python
from pytest_codingagents import LLMAssert

judge = LLMAssert(model="openai/gpt-5-mini")
result = judge(content, "has type hints on all parameters")
if not result:
    print(f"Failed: {result.reasoning}")
```

## Configuring the judge model

The judge model is controlled via pytest CLI options (passed through from pytest-aitest):

```bash
pytest --llm-model openai/gpt-4.1-mini   # explicit judge model
pytest --aitest-summary-model gpt-4.1    # shared model for analysis + assertions
```

## See also

- [A/B Testing Guide](ab-testing.md)
- [Load from Copilot Config](copilot-config.md)
- [pytest-aitest llm_assert docs](https://sbroenne.github.io/pytest-aitest/reference/fixtures/#llm_assert)
