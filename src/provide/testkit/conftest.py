"""Pytest configuration and fixtures for provide-testkit."""

from __future__ import annotations

import pytest

# Note: setproctitle is disabled by pytest_plugin.py (registered via entry points)
# This happens very early in pytest initialization to prevent pytest-xdist performance issues
# Import fixtures from hub module
from provide.testkit.hub.fixtures import (
    default_container_directory,
    isolated_container,
    isolated_hub,
)

# Re-export fixtures so pytest can find them
__all__ = [
    "default_container_directory",
    "isolated_container",
    "isolated_hub",
]

# Make pytest discover fixtures
pytest_plugins = []


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """
    Reset terminal state after test session to prevent output corruption.

    This hook ensures ANSI escape codes and terminal state are properly reset
    after pytest completes, preventing garbled output in the terminal.

    Common causes of terminal corruption:
    - pytest-benchmark unicode box-drawing characters
    - Hypothesis verbose output with special characters
    - ANSI color codes not properly terminated
    - pytest-xdist worker output interference

    The reset codes used:
    - \\033[0m  : Reset all text formatting attributes
    - \\033[?25h : Show cursor (in case it was hidden)
    """
    import sys

    # Reset terminal: clear all formatting and restore cursor
    reset_sequence = "\033[0m\033[?25h"
    sys.stdout.write(reset_sequence)
    sys.stdout.flush()
    sys.stderr.write(reset_sequence)
    sys.stderr.flush()
