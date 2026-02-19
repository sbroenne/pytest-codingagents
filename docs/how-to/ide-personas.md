# IDE Personas

Agents written for VS Code, Claude Code, or the Copilot CLI each expect a
different native tool set. A `Persona` tells `pytest-codingagents` which
runtime environment to simulate so your tests run the agent the same way
the IDE would.

## The problem

An agent like `rpi-agent` is written for VS Code, where `runSubagent` is a
native tool. In the Copilot SDK headless mode `runSubagent` does not exist,
so the agent silently falls back to direct implementation — the RPI pipeline
never fires, and the test proves nothing.

A persona solves this by:

1. **Injecting polyfill tools** — e.g. a Python-side `runSubagent` that
   dispatches registered custom agents as nested SDK runs.
2. **Auto-loading custom instructions** — VS Code and Copilot CLI read
   `.github/copilot-instructions.md`; Claude Code reads `CLAUDE.md`. The
   persona does the same, prepending the file to the session's system
   message when `working_directory` is set.
3. **Setting IDE context** — adds a system-message fragment so the model
   knows which environment it is in.

## Built-in personas

| Persona | Auto-loaded file | Polyfilled tools | Use for |
|---|---|---|---|
| `VSCodePersona` *(default)* | `.github/copilot-instructions.md` | `runSubagent` | VS Code Copilot agents |
| `CopilotCLIPersona` | `.github/copilot-instructions.md` | none — `task` + `skill` are native | Copilot terminal agents |
| `ClaudeCodePersona` | `CLAUDE.md` | `task`-dispatch | Claude Code agents |
| `HeadlessPersona` | nothing | none | Raw SDK baseline |

## Usage

```python
from pytest_codingagents import CopilotAgent, VSCodePersona, CopilotCLIPersona, ClaudeCodePersona, HeadlessPersona

# VS Code agent — auto-loads .github/copilot-instructions.md, polyfills runSubagent
agent = CopilotAgent(
    persona=VSCodePersona(),
    working_directory=str(workspace),
    custom_agents=my_agents,
)

# Default — VSCodePersona is used automatically
agent = CopilotAgent(custom_agents=my_agents)

# Copilot CLI — same instructions file; task+skill already native, no polyfill needed
agent = CopilotAgent(persona=CopilotCLIPersona(), working_directory=str(workspace))

# Claude Code — loads CLAUDE.md, polyfills task-dispatch
agent = CopilotAgent(
    persona=ClaudeCodePersona(),
    working_directory=str(workspace),
    custom_agents=my_agents,
)

# Headless baseline — no IDE context, no file loaded, no polyfills
agent = CopilotAgent(persona=HeadlessPersona())
```

## Custom instructions loading

Custom instruction loading is **automatic and additive**:

- Fires only when `agent.working_directory` is set
- Fires only when the target file exists in that directory
- Prepends the file content to the session system message (before any
  `instructions` you set on the agent)
- If the file is absent, the persona works exactly as without it

This means the same test works against a workspace that has
`.github/copilot-instructions.md` and one that does not — the persona
adapts silently.

## `runSubagent` polyfill

`VSCodePersona` injects `runSubagent` as a Python-side tool when
`agent.custom_agents` is non-empty. The tool dispatches the named agent
as a nested `run_copilot` call, so the model's sub-agent invocations
produce real results — not stub responses.

The polyfill is a no-op when `custom_agents` is empty.

## Extending personas

Subclass `Persona` and override `apply()`:

```python
from pytest_codingagents import Persona, CopilotAgent

class MyPersona(Persona):
    def apply(self, agent, session_config, mapper):
        # Add your tool polyfills or system message additions here
        session_config.setdefault("system_message", {})["content"] = (
            "Custom context. " +
            session_config.get("system_message", {}).get("content", "")
        )

agent = CopilotAgent(persona=MyPersona())
```

## See also

- [Load from Copilot Config](copilot-config.md)
- [Tool Control](tool-control.md)
