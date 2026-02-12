# MCP Server Testing

Test that GitHub Copilot can discover and use your MCP server tools correctly.

## Basic Usage

Attach an MCP server to a `CopilotAgent` and verify the agent calls the right tools:

```python
from pytest_codingagents import CopilotAgent


async def test_database_query(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Use the database tools to answer questions.",
        working_directory=str(tmp_path),
        mcp_servers={
            "my-db-server": {
                "command": "python",
                "args": ["-m", "my_db_mcp_server"],
            }
        },
    )
    result = await copilot_run(agent, "List all users in the database")
    assert result.success
    assert result.tool_was_called("list_users")
```

## Multiple Servers

Attach multiple MCP servers to test interactions between tools:

```python
async def test_multi_server(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Use the available tools to complete tasks.",
        working_directory=str(tmp_path),
        mcp_servers={
            "database": {
                "command": "python",
                "args": ["-m", "db_server"],
            },
            "notifications": {
                "command": "node",
                "args": ["notification_server.js"],
            },
        },
    )
    result = await copilot_run(
        agent,
        "Find users who signed up today and send them a welcome notification",
    )
    assert result.success
    assert result.tool_was_called("query_users")
    assert result.tool_was_called("send_notification")
```

## A/B Server Comparison

Compare two versions of the same MCP server to validate improvements:

```python
import pytest
from pytest_codingagents import CopilotAgent

SERVER_VERSIONS = {
    "v1": {"command": "python", "args": ["-m", "my_server_v1"]},
    "v2": {"command": "python", "args": ["-m", "my_server_v2"]},
}


@pytest.mark.parametrize("version", SERVER_VERSIONS.keys())
async def test_server_version(copilot_run, tmp_path, version):
    agent = CopilotAgent(
        name=f"server-{version}",
        instructions="Use the available tools to answer questions.",
        working_directory=str(tmp_path),
        mcp_servers={"my-server": SERVER_VERSIONS[version]},
    )
    result = await copilot_run(agent, "What's the current inventory count?")
    assert result.success
    assert result.tool_was_called("get_inventory")
```

The AI analysis report will compare pass rates and tool usage across server versions, highlighting which performs better.

## Verifying Tool Arguments

Check not just that a tool was called, but how it was called:

```python
async def test_correct_arguments(copilot_run, tmp_path):
    agent = CopilotAgent(
        instructions="Use database tools to query data.",
        working_directory=str(tmp_path),
        mcp_servers={
            "db": {"command": "python", "args": ["-m", "db_server"]},
        },
    )
    result = await copilot_run(agent, "Find users named Alice")
    assert result.success

    # Check specific tool calls
    calls = result.tool_calls_for("query_users")
    assert len(calls) >= 1
    assert "Alice" in str(calls[0].arguments)
```

## Environment Variables

Pass environment variables to your MCP server process:

```python
agent = CopilotAgent(
    instructions="Use the API tools.",
    working_directory=str(tmp_path),
    mcp_servers={
        "api-server": {
            "command": "python",
            "args": ["-m", "api_server"],
            "env": {
                "API_KEY": "test-key",
                "DATABASE_URL": "sqlite:///test.db",
            },
        }
    },
)
```
