"""
Temporary Environment Utilities.

Provides context managers for safely modifying environment variables
in tests with automatic cleanup and restoration.
"""

from __future__ import annotations

import os
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from typing import Any


@contextmanager
def temp_env(**env_vars: str | None) -> Generator[None, None, None]:
    """Context manager for temporarily setting environment variables.

    Args:
        **env_vars: Environment variables to set. Use None to delete a variable.

    Example:
        with temp_env(DEBUG="true", LOG_LEVEL="INFO"):
            # Environment variables are set
            assert os.environ["DEBUG"] == "true"
        # Environment variables are restored

        # To delete an environment variable:
        with temp_env(UNWANTED_VAR=None):
            # UNWANTED_VAR is removed from environment
            pass
    """
    # Store original values
    original_values: dict[str, str | None] = {}
    for key in env_vars:
        original_values[key] = os.environ.get(key)

    try:
        # Set new values
        for key, value in env_vars.items():
            if value is None:
                # Remove the environment variable
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        # Restore original values
        for key, original_value in original_values.items():
            if original_value is None:
                # Variable didn't exist originally, remove it
                os.environ.pop(key, None)
            else:
                # Restore original value
                os.environ[key] = original_value


@contextmanager
def temp_env_from_dict(env_dict: Mapping[str, str | None]) -> Generator[None, None, None]:
    """Context manager for temporarily setting environment variables from a dict.

    Args:
        env_dict: Dictionary of environment variables to set. Use None values to delete.

    Example:
        env_changes = {"DEBUG": "true", "LOG_LEVEL": "INFO", "REMOVE_ME": None}
        with temp_env_from_dict(env_changes):
            # Environment variables are set/removed
            pass
    """
    with temp_env(**env_dict):
        yield


@contextmanager
def isolated_env(
    keep_vars: list[str] | None = None,
    **new_vars: str,
) -> Generator[None, None, None]:
    """Context manager for running tests in an isolated environment.

    This clears all environment variables except those specified in keep_vars,
    then sets any new variables provided.

    Args:
        keep_vars: List of environment variable names to preserve.
        **new_vars: New environment variables to set.

    Example:
        with isolated_env(keep_vars=["PATH", "HOME"], TEST_MODE="true"):
            # Only PATH, HOME, and TEST_MODE are in the environment
            pass
    """
    if keep_vars is None:
        keep_vars = ["PATH", "HOME", "USER"]  # Preserve essential vars

    # Store all original values
    original_env = dict(os.environ)

    try:
        # Clear environment except for kept variables
        os.environ.clear()
        for var in keep_vars:
            if var in original_env:
                os.environ[var] = original_env[var]

        # Set new variables
        for key, value in new_vars.items():
            os.environ[key] = value

        yield
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


class EnvContext:
    """Context manager class for environment variable management.

    Provides more control over environment variable manipulation
    with the ability to add/remove variables incrementally.
    """

    def __init__(self) -> None:
        """Initialize environment context."""
        self._original_values: dict[str, str | None] = {}
        self._active = False

    def set(self, key: str, value: str) -> None:
        """Set an environment variable.

        Args:
            key: Environment variable name.
            value: Environment variable value.
        """
        if not self._active:
            raise RuntimeError("EnvContext must be used as a context manager")

        if key not in self._original_values:
            self._original_values[key] = os.environ.get(key)

        os.environ[key] = value

    def delete(self, key: str) -> None:
        """Delete an environment variable.

        Args:
            key: Environment variable name to delete.
        """
        if not self._active:
            raise RuntimeError("EnvContext must be used as a context manager")

        if key not in self._original_values:
            self._original_values[key] = os.environ.get(key)

        os.environ.pop(key, None)

    def __enter__(self) -> EnvContext:
        """Enter the context manager."""
        self._active = True
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager and restore environment."""
        self._active = False

        # Restore original values
        for key, original_value in self._original_values.items():
            if original_value is None:
                # Variable didn't exist originally, remove it
                os.environ.pop(key, None)
            else:
                # Restore original value
                os.environ[key] = original_value

        self._original_values.clear()


__all__ = [
    "temp_env",
    "temp_env_from_dict",
    "isolated_env",
    "EnvContext",
]