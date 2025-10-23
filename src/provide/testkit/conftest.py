"""Pytest configuration and fixtures for provide-testkit."""

from __future__ import annotations

import pytest  # noqa: F401

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
