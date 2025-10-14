"""Pytest configuration and fixtures for provide-testkit."""

from __future__ import annotations

import pytest

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
