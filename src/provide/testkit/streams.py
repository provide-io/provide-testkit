#
# streams.py
#
"""
Stream Testing Utilities for Foundation.

Provides utilities for redirecting and managing streams during testing,
allowing tests to capture and control Foundation's output streams.
"""

from typing import TextIO

# Import the actual stream management variables
from provide.foundation.streams.core import get_log_stream


def set_log_stream_for_testing(stream: TextIO | None) -> None:
    """
    Set the log stream for testing purposes.

    This allows tests to redirect Foundation's log output to a custom stream
    (like StringIO) for capturing and verifying log messages.

    Args:
        stream: Stream to redirect to, or None to reset to stderr
    """
    # Import the actual implementation from streams.core
    from provide.foundation.streams.core import (
        set_log_stream_for_testing as _set_stream,
    )

    _set_stream(stream)


def get_current_log_stream() -> TextIO:
    """
    Get the currently active log stream.

    Returns:
        The current log stream being used by Foundation
    """
    return get_log_stream()


def reset_log_stream() -> None:
    """Reset log stream back to stderr."""
    set_log_stream_for_testing(None)


def enable_file_logging_for_testing(log_file_path: str) -> None:
    """Enable file logging specifically for testing scenarios.

    This function bypasses the normal testmode detection that prevents
    file logging during tests. It should only be used in tests that
    specifically need to test file logging functionality.

    Args:
        log_file_path: Path to the log file to write to

    Note:
        This is a specialized utility for testing file logging behavior.
        Most tests should use captured_stderr_for_foundation fixture instead.
    """
    from unittest.mock import patch

    # Import the modules we need to patch
    from provide.foundation.streams import file as streams_file_module
    from provide.foundation.streams import core as streams_core_module

    # Patch both modules to temporarily disable testmode detection
    # This allows both set_log_stream_for_testing and configure_file_logging to work
    patcher1 = patch.object(streams_file_module, 'is_in_click_testing', return_value=False)
    patcher2 = patch.object(streams_core_module, 'is_in_click_testing', return_value=False)

    patcher1.start()
    patcher2.start()

    try:
        # Clear test stream first
        set_log_stream_for_testing(None)
        # Configure file logging
        from provide.foundation.streams.file import configure_file_logging
        configure_file_logging(log_file_path)
    finally:
        # Clean up patches
        patcher2.stop()
        patcher1.stop()


__all__ = [
    "enable_file_logging_for_testing",
    "get_current_log_stream",
    "reset_log_stream",
    "set_log_stream_for_testing",
]
