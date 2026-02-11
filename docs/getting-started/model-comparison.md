# Model Comparison

Compare how different models perform the same task.

## Example

```python
import pytest
from pytest_codingagents import CopilotAgent

MODELS = ["claude-sonnet-4", "gpt-4.1"]


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

    # Compare token usage across models
    print(f"{model}: {result.total_tokens} tokens, ${result.total_cost_usd:.4f}")
```

## What To Look For

- **Success rate** — Which model completes the task reliably?
- **Token usage** — Which model is most efficient?
- **Tool calls** — Which model uses tools appropriately?
- **Reasoning traces** — How does each model think through the problem?
