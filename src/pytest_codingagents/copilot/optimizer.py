"""Instruction optimizer for test-driven prompt engineering.

Provides :func:`optimize_instruction`, which uses an LLM to analyze the gap
between a current agent instruction and the observed behavior, and suggests a
concrete improvement.

Use :func:`azure_entra_model` to build a pre-configured pydantic-ai model
from Azure Entra ID (no API key required):

    model = azure_entra_model()  # defaults to gpt-5.2-chat
    suggestion = await optimize_instruction(
        agent.instructions or "",
        result,
        "Agent should add docstrings.",
        model=model,
    )
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic_ai import Agent as PydanticAgent
from pydantic_ai.models import Model

if TYPE_CHECKING:
    from pytest_codingagents.copilot.result import CopilotResult

__all__ = ["InstructionSuggestion", "azure_entra_model", "optimize_instruction"]

# Most capable model available on Azure OpenAI
_AZURE_DEFAULT_MODEL = "gpt-5.2-chat"


def azure_entra_model(
    deployment: str = _AZURE_DEFAULT_MODEL,
    *,
    endpoint: str | None = None,
    api_version: str = "2024-12-01-preview",
) -> Model:
    """Build a pydantic-ai Model using Azure Entra ID authentication.

    No API key required — uses ``DefaultAzureCredential`` (works with
    ``az login`` locally and managed identity in CI).

    Args:
        deployment: Azure OpenAI deployment name. Defaults to
            ``"gpt-5.2-chat"`` — the most capable model available.
        endpoint: Azure OpenAI endpoint URL. Defaults to the
            ``AZURE_OPENAI_ENDPOINT`` environment variable.
        api_version: Azure OpenAI API version string.

    Returns:
        A pydantic-ai ``Model`` ready to pass to ``optimize_instruction()``.

    Example::

        model = azure_entra_model()
        suggestion = await optimize_instruction(
            agent.instructions or "",
            result,
            "Agent should add docstrings.",
            model=model,
        )
    """
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import AsyncAzureOpenAI
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    azure_endpoint = endpoint or os.environ["AZURE_OPENAI_ENDPOINT"]
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    client = AsyncAzureOpenAI(
        azure_endpoint=azure_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=api_version,
    )
    return OpenAIChatModel(deployment, provider=OpenAIProvider(openai_client=client))


@dataclass
class InstructionSuggestion:
    """A suggested improvement to a Copilot agent instruction.

    Returned by :func:`optimize_instruction`. Designed to drop into
    ``pytest.fail()`` so the failure message includes an actionable fix.

    Attributes:
        instruction: The improved instruction text to use instead.
        reasoning: Explanation of why this change would close the gap.
        changes: Short description of what was changed (one sentence).

    Example::

        suggestion = await optimize_instruction(
            agent.instructions,
            result,
            "Agent should add docstrings to all functions.",
            model=azure_entra_model(),
        )
        pytest.fail(f"No docstrings found.\\n\\n{suggestion}")
    """

    instruction: str
    reasoning: str
    changes: str

    def __str__(self) -> str:
        return (
            f"💡 Suggested instruction:\n\n"
            f"  {self.instruction}\n\n"
            f"  Changes: {self.changes}\n"
            f"  Reasoning: {self.reasoning}"
        )


class _OptimizationOutput(BaseModel):
    """Structured output schema for the optimizer LLM call."""

    instruction: str
    reasoning: str
    changes: str


async def optimize_instruction(
    current_instruction: str,
    result: CopilotResult,
    criterion: str,
    *,
    model: str | Model = "openai:gpt-4o-mini",
) -> InstructionSuggestion:
    """Analyze a result and suggest an improved instruction.

    Uses pydantic-ai structured output to analyze the gap between a
    current instruction and the agent's observed behavior, returning a
    concrete, actionable improvement.

    Designed to drop into ``pytest.fail()`` so the failure message
    contains a ready-to-use fix.

    For Azure OpenAI with Entra ID auth (recommended), use
    :func:`azure_entra_model` to build the model:

    Example::

        from pytest_codingagents import optimize_instruction, azure_entra_model

        result = await copilot_run(agent, task)
        if '\"\"\"' not in result.file("main.py"):
            suggestion = await optimize_instruction(
                agent.instructions or "",
                result,
                "Agent should add docstrings to all functions.",
                model=azure_entra_model(),  # gpt-5.2-chat via Entra ID
            )
            pytest.fail(f"No docstrings found.\\n\\n{suggestion}")

    Args:
        current_instruction: The agent's current instruction text.
        result: The ``CopilotResult`` from the (failed) run.
        criterion: What the agent *should* have done — the test expectation
            in plain English (e.g. ``"Always write docstrings"``).
        model: LiteLLM-style model string (e.g. ``"openai:gpt-4o-mini"``)
            **or** a pre-configured pydantic-ai ``Model`` object built with
            :func:`azure_entra_model` or any other provider.

    Returns:
        An :class:`InstructionSuggestion` with the improved instruction.
    """
    final_output = result.final_response or "(no response)"
    tool_calls = ", ".join(sorted(result.tool_names_called)) or "none"

    prompt = f"""You are helping improve a GitHub Copilot agent instruction.

## Current instruction
{current_instruction or "(no instruction)"}

## Task the agent performed
{criterion}

## What actually happened
The agent produced:
{final_output[:1500]}

Tools called: {tool_calls}
Run succeeded: {result.success}

## Expected criterion
The agent SHOULD have satisfied this criterion:
{criterion}

Analyze the gap between the instruction and the observed behaviour.
Suggest a specific, concise, directive improvement to the instruction
that would make the agent satisfy the criterion.
Keep the instruction under 200 words. Do not add unrelated rules."""

    optimizer_agent = PydanticAgent(model, output_type=_OptimizationOutput)
    run_result = await optimizer_agent.run(prompt)
    output = run_result.output

    return InstructionSuggestion(
        instruction=output.instruction,
        reasoning=output.reasoning,
        changes=output.changes,
    )
