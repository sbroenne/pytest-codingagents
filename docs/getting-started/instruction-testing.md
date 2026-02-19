# Instruction Testing

A/B test different instruction configs against the same task and assert the outputs actually differ.

## Direct Comparison

Run two configs against the same task and assert observable differences:

```python
from pytest_codingagents import CopilotAgent


async def test_documentation_instructions_produce_docstrings(copilot_run, tmp_path):
    """Do documentation instructions actually change the output?"""
    concise = CopilotAgent(
        name="concise",
        instructions="Write minimal Python. NO docstrings. NO comments. Pure logic only.",
        working_directory=str(tmp_path / "concise"),
    )
    verbose = CopilotAgent(
        name="verbose",
        instructions='Write fully documented Python. EVERY function MUST have a docstring: """What it does."""',
        working_directory=str(tmp_path / "verbose"),
    )
    (tmp_path / "concise").mkdir()
    (tmp_path / "verbose").mkdir()

    task = "Create calculator.py with add(a, b), subtract(a, b), multiply(a, b)."
    result_a = await copilot_run(concise, task)
    result_b = await copilot_run(verbose, task)

    assert result_a.success and result_b.success

    content_concise = (tmp_path / "concise" / "calculator.py").read_text()
    content_verbose = (tmp_path / "verbose" / "calculator.py").read_text()

    # Assert the instruction actually changed the output
    assert '"""' not in content_concise, "Concise instructions should suppress docstrings"
    assert '"""' in content_verbose, "Verbose instructions should produce docstrings"
```

## Parametrized Style Comparison

Run many instruction variants in a single test suite and let the AI report rank them:

```python
import pytest
from pytest_codingagents import CopilotAgent

INSTRUCTIONS = {
    "concise": "Write minimal, clean code. No comments unless complex.",
    "verbose": "Write well-documented code with docstrings and inline comments.",
    "tdd": "Always write tests first, then implement the solution.",
}


@pytest.mark.parametrize("style,instructions", INSTRUCTIONS.items())
async def test_coding_style(copilot_run, tmp_path, style, instructions):
    agent = CopilotAgent(
        name=f"style-{style}",
        instructions=instructions,
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create a calculator module with add, subtract, multiply, divide")
    assert result.success
    assert (tmp_path / "calculator.py").exists()
```

The AI analysis report will rank instruction styles by pass rate and highlight behavioral differences.

## What To Assert

- **Presence of specific constructs** — `assert '"""' in content` to verify docstrings
- **Absence of forbidden constructs** — `assert "print(" not in content`
- **Library choice** — `assert "fastapi" in code.lower()`
- **Tool usage** — `assert result.tool_was_called("run_in_terminal")`
