"""CopilotRunner — Execute prompts against GitHub Copilot directly via SDK.

This is the core execution engine. It:
1. Creates a CopilotClient and starts the CLI server
2. Creates a session with the agent's config
3. Sends the prompt and captures ALL events
4. Maps events to a CopilotResult via EventMapper
5. Cleans up the client

No LiteLLM. No outer agent. One LLM. Direct SDK access.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any, cast

from copilot import CopilotClient

from pytest_codingagents.copilot.events import EventMapper

if TYPE_CHECKING:
    from copilot import CopilotSession, SessionEvent
    from copilot.types import CopilotClientOptions

    from pytest_codingagents.copilot.agent import CopilotAgent
    from pytest_codingagents.copilot.result import CopilotResult

logger = logging.getLogger(__name__)


async def run_copilot(agent: CopilotAgent, prompt: str) -> CopilotResult:
    """Execute a prompt against GitHub Copilot and return structured results.

    This is the primary entry point for test execution. It manages the full
    lifecycle: client start → session creation → prompt execution → event
    capture → client cleanup.

    Authentication is resolved in this order:
    1. ``GITHUB_TOKEN`` environment variable (ideal for CI)
    2. Logged-in user via ``gh`` CLI / OAuth (local development)

    Args:
        agent: CopilotAgent configuration.
        prompt: The prompt to send to Copilot.

    Returns:
        CopilotResult with all captured events, tool calls, usage, etc.

    Raises:
        TimeoutError: If the prompt takes longer than agent.timeout_s.
        RuntimeError: If the Copilot CLI fails to start.
    """
    client_options: dict[str, Any] = {
        "cwd": agent.working_directory or ".",
        "auto_start": True,
        "log_level": "warning",
    }

    # Pass GITHUB_TOKEN from environment for CI authentication
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        client_options["github_token"] = github_token
        logger.info("Using GITHUB_TOKEN from environment for authentication")

    client = CopilotClient(options=cast("CopilotClientOptions", client_options))

    mapper = EventMapper()

    try:
        await client.start()
        logger.info("Copilot CLI started")

        # Build session config from agent
        session_config = agent.build_session_config()

        # Install permission handler if auto_confirm is enabled
        if agent.auto_confirm:
            session_config["on_permission_request"] = _auto_approve_handler

        session: CopilotSession = await client.create_session(session_config)  # type: ignore[arg-type]
        logger.info("Session created: %s", session.session_id)

        # Register event listener — captures ALL events
        session.on(mapper.handle)

        # Send prompt and wait for completion
        result_event: SessionEvent | None = await asyncio.wait_for(
            session.send_and_wait({"prompt": prompt}),
            timeout=agent.timeout_s,
        )

        # If send_and_wait returned a final event, process it too
        if result_event is not None:
            mapper.handle(result_event)

        logger.info("Prompt execution complete")

    except TimeoutError:
        logger.error("Prompt execution timed out after %ss", agent.timeout_s)
        # Build partial result from events captured so far
        result = mapper.build()
        result.success = False
        result.error = f"Timeout after {agent.timeout_s}s"
        return result

    except Exception as exc:
        logger.error("Copilot execution failed: %s", exc)
        result = mapper.build()
        result.success = False
        result.error = str(exc)
        return result

    finally:
        try:
            await client.stop()
        except Exception:
            logger.warning("Failed to stop Copilot CLI cleanly, force stopping")
            await client.force_stop()

    return mapper.build()


def _auto_approve_handler(request: dict, context: dict[str, str]) -> dict:
    """Auto-approve all permission requests for deterministic testing.

    Args:
        request: PermissionRequest TypedDict with kind, toolCallId, etc.
        context: Additional context from the SDK.

    Returns:
        PermissionRequestResult with kind="approved".
    """
    return {"kind": "approved"}
