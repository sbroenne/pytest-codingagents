# Configuration

## CopilotAgent Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | `"copilot"` | Agent identifier for reports |
| `model` | `str \| None` | `None` | Model to use (e.g., `claude-sonnet-4`) |
| `instructions` | `str \| None` | `None` | Instructions for the agent |
| `system_message_mode` | `Literal["append", "replace"]` | `"append"` | `"append"` adds to Copilot's built-in system message; `"replace"` overrides it |
| `working_directory` | `str \| None` | `None` | Working directory for file operations |
| `max_turns` | `int` | `25` | Maximum conversation turns (informational — enforced via `timeout_s`, not in SDK) |
| `timeout_s` | `float` | `300.0` | Timeout in seconds |
| `auto_confirm` | `bool` | `True` | Auto-approve tool permissions |
| `reasoning_effort` | `Literal["low", "medium", "high", "xhigh"] \| None` | `None` | Reasoning effort level |
| `allowed_tools` | `list[str] \| None` | `None` | Allowlist of tools |
| `excluded_tools` | `list[str] \| None` | `None` | Blocklist of tools |
| `mcp_servers` | `dict` | `{}` | MCP server configurations |
| `custom_agents` | `list[dict]` | `[]` | Custom agent configurations |
| `skill_directories` | `list[str]` | `[]` | Paths to skill directories |
| `disabled_skills` | `list[str]` | `[]` | Skills to disable |
| `extra_config` | `dict` | `{}` | SDK passthrough for unmapped fields |

## Authentication

Authentication is resolved in order:

1. `GITHUB_TOKEN` environment variable (ideal for CI)
2. Logged-in user via `gh` CLI / OAuth (local development)

## pytest Configuration

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
    "copilot: marks tests as requiring GitHub Copilot SDK credentials",
]
```
