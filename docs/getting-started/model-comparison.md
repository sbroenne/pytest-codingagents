# Model Comparison

Compare how different models perform the same task — which is more reliable, more efficient, or better at following instructions.

## Example

```python
import pytest
from pytest_codingagents import CopilotAgent

MODELS = ["claude-opus-4.5", "gpt-5.2"]


@pytest.mark.parametrize("model", MODELS)
async def test_fibonacci(copilot_run, tmp_path, model):
    agent = CopilotAgent(
        name=f"model-{model}",
        model=model,
        instructions="Write clean Python code.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create fibonacci.py with a fibonacci function")

    assert result.success
    assert (tmp_path / "fibonacci.py").exists()
```

The AI analysis report will produce a leaderboard ranking models by pass rate, token efficiency, and turn count.

## What To Compare

- **Consistency** — Run the same test multiple times. Which model varies least across runs?
- **Turn count** — `len(result.turns)` — fewer turns often means better instruction-following.
- **Token usage** — `result.total_tokens` — efficiency matters at scale.
- **Tool call patterns** — Does one model over-call tools or skip necessary ones?
