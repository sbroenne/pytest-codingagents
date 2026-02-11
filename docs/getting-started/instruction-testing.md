# Instruction Testing

Test how different system prompts affect agent behavior.

## Example

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

## What To Look For

- **Do instructions change behavior?** Compare output files across styles.
- **Token efficiency** — Verbose prompts may cost more but produce better results.
- **Tool patterns** — Does TDD-style actually write tests first?
