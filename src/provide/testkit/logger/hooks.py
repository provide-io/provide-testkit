#
# hooks.py
#
"""
Pytest Hooks for Logger Management.

Provides pytest hooks for suppressing noisy loggers during test runs.
This helps reduce test output noise from third-party libraries.
"""

import logging
import os

import pytest

# Default list of commonly noisy loggers to suppress during tests
DEFAULT_NOISY_LOGGERS = [
    "markdown_it",
    "asyncio",
    "urllib3.connectionpool",
    "requests.packages.urllib3.connectionpool",
    "botocore",
    "boto3.resources",
    "websockets.protocol",
    "websockets.server",
    "websockets.client",
    "httpx",
    "httpcore",
]


def get_noisy_loggers() -> list[str]:
    """
    Get the list of loggers to suppress during tests.

    Can be customized via the TESTKIT_NOISY_LOGGERS environment variable,
    which should be a comma-separated list of logger names.

    Returns:
        List of logger names to suppress.
    """
    env_loggers = os.getenv("TESTKIT_NOISY_LOGGERS")
    if env_loggers:
        return [name.strip() for name in env_loggers.split(",") if name.strip()]
    return DEFAULT_NOISY_LOGGERS


def get_log_level_for_noisy_loggers() -> int:
    """
    Get the log level to set for noisy loggers.

    Can be customized via the TESTKIT_NOISY_LOG_LEVEL environment variable.
    Defaults to WARNING level.

    Returns:
        Logging level (int) to set for noisy loggers.
    """
    level_name = os.getenv("TESTKIT_NOISY_LOG_LEVEL", "WARNING")
    return getattr(logging, level_name.upper(), logging.WARNING)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup():
    """
    Hook that runs before each test setup.

    This forcefully sets the log level for noisy libraries to WARNING (or custom level),
    overriding any configuration that may have happened at import time
    (e.g., by Textual or the application itself).
    """
    noisy_loggers = get_noisy_loggers()
    log_level = get_log_level_for_noisy_loggers()

    for logger_name in noisy_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)


def suppress_loggers(logger_names: list[str], level: int = logging.WARNING) -> None:
    """
    Utility function to suppress specific loggers to a given level.

    Can be used directly in tests or conftest.py files for custom suppression.

    Args:
        logger_names: List of logger names to suppress
        level: Log level to set (defaults to WARNING)
    """
    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)


__all__ = [
    "DEFAULT_NOISY_LOGGERS",
    "get_log_level_for_noisy_loggers",
    "get_noisy_loggers",
    "pytest_runtest_setup",
    "suppress_loggers",
]
