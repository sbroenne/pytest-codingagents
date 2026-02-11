"""Unit tests for CopilotAgent."""

from __future__ import annotations

from pytest_codingagents.copilot.agent import CopilotAgent


class TestCopilotAgentDefaults:
    """Test default values."""

    def test_default_values(self):
        agent = CopilotAgent(name="test")
        assert agent.name == "test"
        assert agent.model is None
        assert agent.max_turns == 25
        assert agent.timeout_s == 300.0
        assert agent.auto_confirm is True
        assert agent.instructions is None
        assert agent.working_directory is None

    def test_custom_values(self):
        agent = CopilotAgent(
            name="custom",
            model="gpt-4.1",
            max_turns=10,
            timeout_s=60.0,
            auto_confirm=False,
            instructions="Be helpful",
            working_directory="/tmp/test",
        )
        assert agent.model == "gpt-4.1"
        assert agent.max_turns == 10
        assert agent.timeout_s == 60.0
        assert agent.auto_confirm is False

    def test_frozen(self):
        agent = CopilotAgent(name="frozen")
        try:
            agent.name = "mutated"  # type: ignore[misc]
            raise AssertionError("Should not allow mutation")
        except AttributeError:
            pass  # Expected — frozen dataclass


class TestBuildSessionConfig:
    """Test build_session_config() method."""

    def test_minimal_config(self):
        agent = CopilotAgent(name="minimal")
        config = agent.build_session_config()
        assert isinstance(config, dict)
        # Should not include None fields
        assert "model" not in config or config.get("model") is None

    def test_full_config(self):
        agent = CopilotAgent(
            name="full",
            model="claude-sonnet-4",
            reasoning_effort="high",
            instructions="Be helpful",
            max_turns=10,
            allowed_tools=["create_file"],
            excluded_tools=["run_in_terminal"],
            working_directory="/tmp/test",
        )
        config = agent.build_session_config()
        assert config["model"] == "claude-sonnet-4"
        assert config["reasoning_effort"] == "high"
        assert config["system_message"] == {"mode": "append", "content": "Be helpful"}
        assert "maxTurns" not in config  # max_turns is NOT part of SDK SessionConfig
        assert config["available_tools"] == ["create_file"]
        assert config["excluded_tools"] == ["run_in_terminal"]
        assert config["working_directory"] == "/tmp/test"

    def test_mcp_servers_included(self):
        agent = CopilotAgent(
            name="mcp",
            mcp_servers={
                "my-server": {"command": "python", "args": ["-m", "my_server"]},
            },
        )
        config = agent.build_session_config()
        assert "mcp_servers" in config
        assert len(config["mcp_servers"]) == 1

    def test_system_message_replace_mode(self):
        agent = CopilotAgent(
            name="replace",
            instructions="Custom system message",
            system_message_mode="replace",
        )
        config = agent.build_session_config()
        assert config["system_message"] == {
            "mode": "replace",
            "content": "Custom system message",
        }

    def test_no_system_message_without_instructions(self):
        agent = CopilotAgent(name="no-instructions")
        config = agent.build_session_config()
        assert "system_message" not in config

    def test_extra_config_merged(self):
        agent = CopilotAgent(
            name="extra",
            extra_config={"customField": "value"},
        )
        config = agent.build_session_config()
        assert config["customField"] == "value"
