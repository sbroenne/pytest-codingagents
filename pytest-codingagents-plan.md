# pytest-codingagents — Project Plan

> A pytest plugin for testing **real coding agents** (GitHub Copilot, Cursor, etc.) directly via their SDK, capturing the full event stream.

## Why a Separate Project?

### The Problem with PR #37 (Wrapper Approach)

PR #37 wraps GitHub Copilot as a tool inside a synthetic agent:

```
User → LiteLLM (outer agent) → call_tool("copilot") → Copilot SDK (inner agent) → tools
```

This creates fundamental problems:

| Issue | Impact |
|-------|--------|
| **2 LLMs** | Outer LiteLLM agent adds latency, cost, and noise |
| **Throwaway system prompt** | The outer agent's prompt is meaningless — Copilot has its own |
| **Hidden SDK events** | 37 event types compressed into a single `call_tool()` return |
| **No permission hooks** | Can't test consent flows (file edits, terminal commands) |
| **No reasoning traces** | Copilot's thinking is invisible |
| **No attachment testing** | Can't send files, images, workspace context |
| **No subagent routing** | Can't observe how Copilot delegates to specialized agents |
| **Fake metrics** | Token counts reflect the outer agent, not Copilot |

### The Solution: Direct SDK Integration

```
User → Copilot SDK → tools → events captured directly
```

One LLM. Full event stream. Real metrics. Every SDK capability accessible.

### Doctrine Alignment

**pytest-aitest** has a clear doctrine: *"Agents are harnesses, not targets."* Real coding agents break this — they ARE the target. Rather than dilute pytest-aitest's clean abstraction, we create a sibling project that shares its reporting infrastructure.

## Capability Comparison

| Capability | PR #37 (Wrapper) | pytest-codingagents (Direct) |
|---|---|---|
| Tool call capture | ✅ (via outer agent) | ✅ (native events) |
| Token usage | ❌ (outer agent tokens) | ✅ (real Copilot tokens) |
| Reasoning traces | ❌ | ✅ (`Thinking` events) |
| Permission hooks | ❌ | ✅ (`ConfirmationRequest`) |
| Attachment support | ❌ | ✅ (`references` in config) |
| Subagent routing | ❌ | ✅ (`AgentQueued/Started/Completed`) |
| Error details | ❌ (generic) | ✅ (`ErrorOccurred` with context) |
| Progress tracking | ❌ | ✅ (`Progress` events) |
| Code citations | ❌ | ✅ (`CodeCitation` events) |
| Custom instructions | ❌ | ✅ (full `SessionConfig`) |
| System prompt testing | ❌ (outer prompt) | ✅ (`instructions` field) |
| Multi-turn sessions | ❌ | ✅ (session continuations) |
| Cost accuracy | ❌ | ✅ |
| LLM count | 2 (wasteful) | 1 (direct) |

## Project Structure

```
pytest-codingagents/
├── pyproject.toml
├── README.md
├── src/
│   └── pytest_codingagents/
│       ├── __init__.py              # Public API exports
│       ├── plugin.py                # pytest plugin (pytest11 entry point)
│       ├── copilot/                 # GitHub Copilot provider
│       │   ├── __init__.py
│       │   ├── agent.py             # CopilotAgent config dataclass
│       │   ├── runner.py            # CopilotRunner — direct SDK execution
│       │   ├── events.py            # SessionEvent → Turn/ToolCall mapper
│       │   └── fixtures.py          # copilot_run pytest fixture
│       └── _compat/                 # pytest-aitest integration
│           ├── __init__.py
│           └── result.py            # AgentResult adapter (if needed)
├── tests/
│   ├── conftest.py
│   ├── test_basic.py               # Basic Copilot tool usage
│   ├── test_instructions.py        # System prompt / instructions testing
│   ├── test_models.py              # Model comparison
│   ├── test_matrix.py              # Model × Instructions grid
│   ├── test_custom_agents.py       # Custom agent modes
│   └── test_events.py              # SDK-unique: permissions, reasoning, attachments
└── docs/
    └── index.md
```

## Step-by-Step Plan

### Step 1: Project Scaffolding

Create the project with `uv init`, configure `pyproject.toml`:

```toml
[project]
name = "pytest-codingagents"
description = "Test real coding agents via their SDK"
requires-python = ">=3.11"
dependencies = [
    "pytest>=8.0",
    "github-copilot-sdk>=0.1",
]

[project.optional-dependencies]
aitest = ["pytest-aitest>=0.6"]  # For HTML reporting

[project.entry-points.pytest11]
codingagents = "pytest_codingagents.plugin"
```

**Verification**: `uv sync` succeeds, `pytest --co` sees the plugin.

### Step 2: CopilotAgent Config Type

A flat dataclass that maps 1:1 to the Copilot SDK's `SessionConfig`:

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class CopilotAgent:
    """Configuration for a GitHub Copilot agent test."""

    # Identity
    agent_name: str = "copilot"
    model: str | None = None  # None = Copilot's default

    # Behavior
    instructions: str = ""  # System prompt / custom instructions
    agent_mode: str | None = None  # "agent", custom agent slug
    
    # Context
    references: list[str] = field(default_factory=list)  # File paths, URLs
    working_directory: str | None = None
    
    # Limits
    max_turns: int = 25
    timeout_ms: int = 120_000
    
    # Permissions
    auto_confirm: bool = True  # Auto-approve file edits, terminal commands
    
    # SDK passthrough
    extra_config: dict[str, Any] = field(default_factory=dict)
```

**Key design decisions**:
- `frozen=True` — config is immutable once created
- `auto_confirm` — most tests want deterministic execution without permission dialogs
- `extra_config` — escape hatch for SDK features we haven't mapped yet
- No `provider` wrapper — Copilot IS the provider

**Verification**: Can instantiate `CopilotAgent()` with defaults and with full config.

### Step 3: CopilotRunner Execution Engine

Direct SDK integration — no LiteLLM, no outer agent:

```python
from __future__ import annotations

from dataclasses import dataclass, field

from github_copilot_sdk import CopilotClient, SessionConfig, SessionEvent


@dataclass(slots=True)
class CopilotRunner:
    """Executes prompts against GitHub Copilot directly via SDK."""

    agent: CopilotAgent
    _events: list[SessionEvent] = field(default_factory=list, init=False)

    async def run(self, prompt: str) -> CopilotResult:
        """Send a prompt to Copilot and capture the full event stream."""
        client = CopilotClient()
        config = self._build_config()

        session = await client.start_session(config)

        # Register event listeners for ALL 37 event types
        session.on("*", self._capture_event)

        if self.agent.auto_confirm:
            session.on("ConfirmationRequest", self._auto_approve)

        response = await session.send_and_wait(prompt)

        return self._build_result(response, self._events)

    def _build_config(self) -> SessionConfig:
        """Map CopilotAgent fields to SDK SessionConfig."""
        config = SessionConfig(
            instructions=self.agent.instructions,
            model=self.agent.model,
            agent_mode=self.agent.agent_mode,
            references=self.agent.references,
        )
        # Apply extra_config passthrough
        for key, value in self.agent.extra_config.items():
            setattr(config, key, value)
        return config

    def _capture_event(self, event: SessionEvent) -> None:
        """Capture every SDK event for later analysis."""
        self._events.append(event)

    def _auto_approve(self, event: SessionEvent) -> str:
        """Auto-approve permission requests for deterministic testing."""
        return "approve"
```

**Key design decisions**:
- Wildcard listener (`session.on("*", ...)`) captures everything
- `auto_confirm` handles permission flows automatically
- Events are raw SDK objects — mapping happens in Step 4
- No retry logic at this layer (SDK handles its own retries)

**Verification**: Can run a simple prompt and get events back.

### Step 4: Event Mapper (SessionEvent → AgentResult)

Maps the 37 SDK event types to pytest-aitest's `AgentResult` structure:

```python
from __future__ import annotations

from pytest_aitest.core.result import AgentResult, Turn, ToolCall


# Event type → handler mapping
EVENT_HANDLERS = {
    # Tool lifecycle
    "ToolCallStarted": _handle_tool_start,
    "ToolCallCompleted": _handle_tool_complete,
    "ToolCallConfirmationRequest": _handle_tool_confirm,

    # Agent reasoning
    "Thinking": _handle_thinking,
    "Progress": _handle_progress,

    # Subagent delegation
    "AgentQueued": _handle_subagent_queued,
    "AgentStarted": _handle_subagent_started,
    "AgentCompleted": _handle_subagent_completed,

    # Content
    "TextContent": _handle_text,
    "CodeCitation": _handle_citation,
    "MarkdownContent": _handle_markdown,

    # Errors
    "ErrorOccurred": _handle_error,

    # Metrics (token usage, timing)
    "ModelResponse": _handle_model_response,
}


def map_events_to_result(
    events: list[SessionEvent],
    agent: CopilotAgent,
) -> AgentResult:
    """Convert raw SDK events into an AgentResult for reporting."""
    turns: list[Turn] = []
    tool_calls: list[ToolCall] = []
    total_tokens = 0
    reasoning_traces: list[str] = []
    # ... process events through handlers ...
    
    return AgentResult(
        turns=turns,
        success=not any(e.type == "ErrorOccurred" for e in events),
        token_usage=total_tokens,
        # Extended fields for Copilot-specific data
    )
```

**SDK Event Types (37 total) grouped by category**:

| Category | Events | Maps To |
|----------|--------|---------|
| **Tool Lifecycle** | `ToolCallStarted`, `ToolCallCompleted`, `ToolCallConfirmationRequest`, `ToolCallProgressUpdated` | `Turn.tool_calls[]` |
| **Agent Reasoning** | `Thinking`, `Progress` | `Turn.reasoning_traces[]` |
| **Subagent** | `AgentQueued`, `AgentStarted`, `AgentCompleted` | Nested `Turn` objects |
| **Content** | `TextContent`, `MarkdownContent`, `CodeCitation`, `Snippet` | `Turn.response`, citations |
| **Permissions** | `ConfirmationRequest`, `ConfirmationResponse` | `Turn.permissions[]` |
| **Model** | `ModelResponse`, `ModelTurnStarted`, `ModelTurnCompleted` | Token counts, timing |
| **Session** | `SessionStarted`, `SessionCompleted`, `SessionCancelled` | Result status |
| **References** | `ReferenceAdded`, `ReferenceRemoved` | Context tracking |
| **Errors** | `ErrorOccurred` | `result.success = False` |
| **Other** | `PlanCreated`, `PlanUpdated`, `CodeEdit`, `TerminalCommand`, etc. | Extended metadata |

**Verification**: Unit-test with mock event sequences → assert correct AgentResult shape.

### Step 5: copilot_run Fixture

The primary test interface. Stashes results for pytest-aitest reporting:

```python
from __future__ import annotations

import pytest


@pytest.fixture
def copilot_run(request):
    """Fixture that runs a prompt against a CopilotAgent and captures results."""

    async def _run(agent: CopilotAgent, prompt: str) -> AgentResult:
        runner = CopilotRunner(agent)
        result = await runner.run(prompt)

        # Stash for pytest-aitest's reporting plugin
        request.node._aitest_result = result
        request.node._aitest_agent = _to_aitest_agent(agent)

        return result

    return _run


def _to_aitest_agent(copilot_agent: CopilotAgent) -> Agent:
    """Convert CopilotAgent to pytest-aitest's Agent type for reporting."""
    from pytest_aitest import Agent, Provider

    return Agent(
        agent_name=copilot_agent.agent_name,
        provider=Provider(model=copilot_agent.model or "copilot-default"),
        system_prompt=copilot_agent.instructions,
        max_turns=copilot_agent.max_turns,
    )
```

**Integration mechanism**: pytest-aitest's plugin reads `request.node._aitest_result` and `request.node._aitest_agent` in `pytest_runtest_makereport`. By stashing compatible objects, we get full HTML reporting for free — leaderboard, AI insights, Mermaid diagrams, everything.

**Verification**: Run a test with `--aitest-html=report.html`, verify Copilot results appear in the report.

### Step 6: Plugin Registration

```python
# src/pytest_codingagents/plugin.py
from __future__ import annotations


def pytest_configure(config):
    """Register markers for coding agent tests."""
    config.addinivalue_line(
        "markers",
        "copilot: mark test as requiring GitHub Copilot SDK",
    )


# Fixture auto-registration via conftest.py convention
# or explicit fixture registration here
```

Entry point in `pyproject.toml`:
```toml
[project.entry-points.pytest11]
codingagents = "pytest_codingagents.plugin"
```

**Verification**: `pytest --markers` shows the `copilot` marker.

### Step 7: Write Tests

Migrate and adapt tests from PR #37, plus add SDK-unique tests:

#### Migrated tests (from PR #37)

```python
# test_basic.py
from pytest_codingagents.copilot import CopilotAgent


async def test_file_creation(copilot_run, tmp_path):
    """Copilot can create a file when asked."""
    agent = CopilotAgent(
        instructions="You are a helpful coding assistant.",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create a file called hello.py with print('hello')")
    assert result.success
    assert result.tool_was_called("create_file")
    assert (tmp_path / "hello.py").exists()
```

#### SDK-unique tests (NOT possible with PR #37)

```python
# test_events.py — Tests that exploit direct SDK access


async def test_reasoning_traces_captured(copilot_run, tmp_path):
    """Verify we capture Copilot's thinking/reasoning events."""
    agent = CopilotAgent(working_directory=str(tmp_path))
    result = await copilot_run(agent, "Analyze this code and suggest improvements")
    
    # Only possible with direct SDK — reasoning is invisible in wrapper
    assert len(result.reasoning_traces) > 0


async def test_permission_flow(copilot_run, tmp_path):
    """Verify permission request/response cycle is captured."""
    agent = CopilotAgent(
        auto_confirm=False,  # Don't auto-approve
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Delete all .tmp files")
    
    # Only possible with direct SDK — permissions are hidden in wrapper
    assert result.permission_requested
    assert result.permission_type == "file_delete"


async def test_subagent_routing(copilot_run, tmp_path):
    """Verify subagent delegation is captured."""
    agent = CopilotAgent(working_directory=str(tmp_path))
    result = await copilot_run(
        agent,
        "Create a React component with tests and documentation",
    )
    
    # Only possible with direct SDK — subagents are invisible in wrapper
    assert len(result.subagent_invocations) > 0


async def test_code_citations(copilot_run, tmp_path):
    """Verify code citations are captured."""
    agent = CopilotAgent(working_directory=str(tmp_path))
    result = await copilot_run(agent, "Implement a binary search function")
    
    # Only possible with direct SDK
    if result.citations:
        assert all(c.license for c in result.citations)


async def test_custom_model(copilot_run, tmp_path):
    """Test with a specific model selection."""
    agent = CopilotAgent(
        model="claude-sonnet-4",
        working_directory=str(tmp_path),
    )
    result = await copilot_run(agent, "Create hello.py")
    assert result.success
    assert result.model_used == "claude-sonnet-4"


async def test_attachment_context(copilot_run, tmp_path):
    """Test sending file references as context."""
    # Create a file to reference
    (tmp_path / "schema.sql").write_text("CREATE TABLE users (id INT, name TEXT);")
    
    agent = CopilotAgent(
        references=[str(tmp_path / "schema.sql")],
        working_directory=str(tmp_path),
    )
    result = await copilot_run(
        agent,
        "Generate a Python ORM model based on the referenced schema",
    )
    assert result.success
    assert "users" in result.final_response.lower()
```

**Verification**: `pytest --collect-only` finds all tests. Integration run passes.

### Step 8: Clean Up pytest-aitest

Revert all Copilot code from PR #37. Close the PR.

**Files to revert** (25 touch points across 7 files):

| File | What to Remove |
|------|---------------|
| `src/pytest_aitest/core/agent.py` | `CopilotCustomAgent` (L284-330), `GitHubCopilotServer` (L335-389), `Agent.copilot_servers` field (L430) |
| `src/pytest_aitest/execution/servers.py` | `GitHubCopilotServerProcess` (L358-513, 156 lines), ServerManager copilot dispatch (L531-703) |
| `src/pytest_aitest/fixtures/run.py` | `copilot_servers=agent.copilot_servers` passthrough (L127) |
| `src/pytest_aitest/__init__.py` | Copilot exports |
| `src/pytest_aitest/core/__init__.py` | Copilot exports |
| `src/pytest_aitest/prompts/ai_summary.md` | Copilot-specific sections (L12, L19, L34-36, L70, L72, L156-160) |
| `pyproject.toml` | `copilot` optional dependency, marker |

**Files to delete**:
- `tests/integration/copilot/` (6 test files + conftest)
- `tests/unit/test_copilot_config.py`
- `docs/how-to/test-copilot-agent.md`

**Approach**: Either revert the entire PR branch, or surgically remove each touch point. Given the scope (25 locations), a clean revert is safer.

**Verification**: `uv run pytest tests/unit/ -q` passes with no Copilot references. `grep -r "copilot" src/` returns nothing.

## Integration with pytest-aitest Reporting

The key insight: pytest-codingagents doesn't need its own reporting. It piggybacks on pytest-aitest's HTML reports by stashing compatible objects:

```
pytest-codingagents fixture                pytest-aitest plugin
─────────────────────────                  ────────────────────
copilot_run()                              pytest_runtest_makereport()
  ├─ runner.run(prompt)                      ├─ reads node._aitest_result
  ├─ stash node._aitest_result ──────────►   ├─ reads node._aitest_agent
  └─ stash node._aitest_agent  ──────────►   └─ builds TestReport → HTML
```

This gives us:
- Agent leaderboard (compare Copilot models, instructions)
- AI insights (failure analysis, prompt feedback)
- Mermaid sequence diagrams (tool call flows)
- Cost tracking (real token usage from SDK)
- Session tracking (multi-turn conversations)

**Requirement**: User installs both packages:
```bash
uv add pytest-codingagents pytest-aitest
```

Without pytest-aitest installed, tests still run — they just don't get HTML reports.

## Timeline & Priorities

| Priority | Step | Effort | Dependency |
|----------|------|--------|------------|
| P0 | Step 1: Scaffolding | 1 hour | None |
| P0 | Step 2: CopilotAgent | 1 hour | Step 1 |
| P0 | Step 3: CopilotRunner | 2-3 hours | Step 2 |
| P0 | Step 4: Event mapper | 2-3 hours | Step 3 |
| P0 | Step 5: Fixture | 1 hour | Step 4 |
| P1 | Step 6: Plugin | 30 min | Step 5 |
| P1 | Step 7: Tests | 2-3 hours | Step 5 |
| P2 | Step 8: Clean up pytest-aitest | 1 hour | Steps 1-7 proven |

**Total estimated effort**: ~12-14 hours

## Open Questions

1. **SDK stability**: `github-copilot-sdk>=0.1` — is the API stable enough, or should we pin more tightly?
2. **Authentication**: How does the SDK authenticate? PAT? GitHub App? Device flow? This affects CI/CD.
3. **AgentResult extensions**: Do we extend pytest-aitest's `AgentResult` with Copilot-specific fields, or create a `CopilotResult` subclass?
4. **Multi-agent support**: Should we plan for Cursor, Windsurf, etc. from day one, or add them later?
5. **Workspace isolation**: How do we sandbox Copilot's file operations in tests? `tmp_path`? Docker?

## Appendix: SDK Event Types (Full List)

All 37 `SessionEventType` values from `github-copilot-sdk`:

```
AgentCompleted          AgentQueued            AgentStarted
CodeCitation            CodeEdit               ConfirmationRequest
ConfirmationResponse    ErrorOccurred          MarkdownContent
ModelResponse           ModelTurnCompleted     ModelTurnStarted
PlanCreated             PlanUpdated            Progress
ReferenceAdded          ReferenceRemoved       SessionCancelled
SessionCompleted        SessionStarted         Snippet
TerminalCommand         TerminalOutput         TextContent
Thinking                ToolCallCompleted      ToolCallConfirmationRequest
ToolCallProgressUpdated ToolCallStarted        ...
```

*(Some event types may be added/removed as the SDK evolves)*
