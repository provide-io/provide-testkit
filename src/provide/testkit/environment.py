"""
Environment management utilities for testing.

Provides context managers and utilities for managing test environments,
environment variables, and foundation setup/cleanup.
"""

import os
from pathlib import Path
from typing import Any

from provide.testkit.logger import reset_foundation_setup_for_testing


class TestEnvironment:
    """Context manager for test environment setup with proper cleanup."""

    def __init__(self, env_vars: dict[str, str] | None = None):
        """
        Initialize test environment manager.

        Args:
            env_vars: Dictionary of environment variables to set during the test
        """
        self.env_vars = env_vars or {}
        self.original_env: dict[str, str | None] = {}

    def __enter__(self) -> "TestEnvironment":
        """Enter the test environment context."""
        # Save original environment variables
        for key in self.env_vars:
            self.original_env[key] = os.environ.get(key)
            os.environ[key] = self.env_vars[key]

        # Reset foundation setup
        reset_foundation_setup_for_testing()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the test environment context and restore original state."""
        # Restore original environment variables
        for key, original_value in self.original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

        # Reset foundation setup again for cleanup
        reset_foundation_setup_for_testing()


def get_example_dir() -> Path:
    """Get the examples directory path consistently across examples."""
    # Note: This assumes foundation project structure
    # In testkit context, this should point to foundation's examples
    current_file = Path(__file__).resolve()
    # Go up from testkit/src/provide/testkit/environment.py to find foundation
    testkit_root = current_file.parent.parent.parent.parent
    foundation_root = testkit_root.parent / "provide-foundation"
    return foundation_root / "examples"


def add_src_to_path() -> Path:
    """Add src directory to Python path for examples. Returns project root path."""
    import sys

    example_dir = get_example_dir()
    project_root = example_dir.parent
    src_path = project_root / "src"

    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    return project_root


def reset_test_environment() -> None:
    """Reset the test environment to a clean state."""
    reset_foundation_setup_for_testing()
