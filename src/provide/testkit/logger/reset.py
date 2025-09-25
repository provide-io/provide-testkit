#
# reset.py
#
"""
Foundation Reset Utilities for Testing.

Thin wrapper around Foundation's orchestrated reset functionality.
Provides backward-compatible API while delegating to Foundation's
internal reset orchestration.
"""

# Re-export mock utilities from mocks module
from provide.testkit.logger.mocks import mock_logger, mock_logger_factory

# Note: Removed module-level imports to avoid circular imports
# All Foundation imports will be done within functions when needed


def reset_foundation_state() -> None:
    """Reset Foundation's complete internal state using Foundation's orchestration.

    This is a thin wrapper around Foundation's internal reset orchestration.
    Use reset_foundation_setup_for_testing() for the full test reset.
    """
    from provide.foundation.testmode.orchestration import reset_foundation_state as foundation_reset

    foundation_reset()


def reset_foundation_setup_for_testing() -> None:
    """Complete Foundation reset for testing with all test-specific concerns.

    This function ensures clean test isolation by resetting all
    Foundation state between test runs using Foundation's own
    orchestrated reset functionality.
    """
    from provide.foundation.testmode.orchestration import reset_foundation_for_testing

    reset_foundation_for_testing()


__all__ = [
    "mock_logger",
    "mock_logger_factory",
    "reset_foundation_setup_for_testing",
    "reset_foundation_state",
]
