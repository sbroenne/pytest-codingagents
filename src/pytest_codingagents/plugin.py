"""pytest-codingagents plugin registration.

Registered as a pytest plugin via the ``pytest11`` entry point in
pyproject.toml. Provides the ``copilot_run`` fixture and ``copilot`` marker.
"""

from __future__ import annotations

# Re-export the fixture so pytest discovers it via the plugin entry point.
from pytest_codingagents.copilot.fixtures import copilot_run

__all__ = ["copilot_run"]


def pytest_configure(config: object) -> None:
    """Register markers for coding agent tests."""
    from _pytest.config import Config

    assert isinstance(config, Config)
    config.addinivalue_line(
        "markers",
        "copilot: mark test as requiring GitHub Copilot SDK credentials",
    )
