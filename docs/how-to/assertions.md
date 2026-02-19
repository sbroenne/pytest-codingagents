# Assertions

Two complementary assertion styles work together in pytest-codingagents:

- **File helpers** — read files the agent created/modified directly from `CopilotResult`
- **Semantic assertions** — use the `llm_assert` fixture from [pytest-aitest](https://sbroenne.github.io/pytest-aitest)

## File helpers

The agent runs in `working_directory`. File helpers let you inspect results
without threading `tmp_path` through every test.

```python
# Read a file the agent created
content = result.file("main.py")

# Check existence
assert result.file_exists("main.py")

# Find files by glob pattern (recursive)
py_files = result.files_matching("**/*.py")
assert py_files, "No Python files were created"

test_files = result.files_matching("test_*.py")
assert test_files, "No test file was created"
```

All paths are relative to `agent.working_directory`. `file()` raises
`FileNotFoundError` if the file does not exist — which is itself a useful
assertion when you expect the agent to have created it.

## Semantic assertions with `llm_assert`

`llm_assert` is a pytest fixture provided by **pytest-aitest** — it's
automatically available in every test (no import needed). It evaluates text
against a plain-English criterion using a cheap judge LLM.

```python
async def test_calculator(copilot_run, llm_assert, tmp_path):
    agent = CopilotAgent(
        instructions="Write fully documented Python with Google-style docstrings.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create calculator.py with add and subtract.")
    assert result.success
    assert llm_assert(
        result.file("calculator.py"),
        "has Google-style docstrings with Args: and Returns: sections",
    )
```

See the [pytest-aitest docs](https://sbroenne.github.io/pytest-aitest) for
full `llm_assert` and `llm_score` documentation.

## Combining both in A/B tests

```python
@pytest.mark.copilot
async def test_docstring_instruction_adds_docs(copilot_run, llm_assert, tmp_path):
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

    assert treatment_result.success
    assert llm_assert(
        treatment_result.file("calculator.py"),
        "has Google-style docstrings with Args: and Returns: sections",
    ), "Treatment did not produce docstrings despite instruction"
```

## See also

- [A/B Testing Guide](ab-testing.md)
- [Load from Copilot Config](copilot-config.md)
