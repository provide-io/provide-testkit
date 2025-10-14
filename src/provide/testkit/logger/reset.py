#
# reset.py
#
"""
Foundation Reset Utilities for Testing.

Thin wrapper around Foundation's orchestrated reset functionality.
Provides backward-compatible API while delegating to Foundation's
internal reset orchestration.

Testing Patterns with Dependency Injection
------------------------------------------

With Foundation's dependency injection architecture, there are two main
testing patterns:

1. **Global State Testing (traditional):**
   Uses the global Hub via get_hub() and requires reset functions between tests.
   Suitable for integration tests and legacy code.

2. **Isolated Container Testing (DI-based):**
   Creates isolated Container instances per test, eliminating the need for
   global state resets. Each test gets a fresh Container and Hub automatically.

   Example:
       >>> from provide.foundation.hub import Hub, Container
       >>> def test_my_feature():
       ...     container = Container()
       ...     hub = Hub(container=container)
       ...     # Test has clean, isolated state

The reset functions in this module support the traditional global state pattern.
Tests using isolated containers can skip these reset calls entirely.
"""

# Re-export mock utilities from mocks module
from provide.testkit.logger.mocks import mock_logger, mock_logger_factory

# Note: Removed module-level imports to avoid circular imports
# All Foundation imports will be done within functions when needed


def reset_foundation_state() -> None:
    """Reset Foundation's complete internal state using Foundation's orchestration.

    This is a thin wrapper around Foundation's internal reset orchestration.
    Use reset_foundation_setup_for_testing() for the full test reset.

    Note on Dependency Injection:
        Tests using isolated Container instances for dependency injection may not
        need to reset global state. See reset_foundation_setup_for_testing()
        documentation for details on testing with isolated containers.
    """
    from provide.foundation.testmode.orchestration import reset_foundation_state as foundation_reset

    foundation_reset()


def reset_foundation_setup_for_testing() -> None:
    """Complete Foundation reset for testing with all test-specific concerns.

    This function ensures clean test isolation by resetting all
    Foundation state between test runs using Foundation's own
    orchestrated reset functionality.

    Note on Dependency Injection:
        With Foundation's new dependency injection architecture, tests that use
        isolated Container instances may not need to call this global reset
        function. If your test creates its own Hub with an isolated Container,
        the test inherently has clean state without resetting global state.

        Example of isolated testing with DI:
            >>> from provide.foundation.hub import Hub, Container
            >>> def test_with_isolated_container():
            ...     # No reset needed - each test gets fresh container
            ...     container = Container()
            ...     hub = Hub(container=container)
            ...     # Use hub for dependency injection
            ...     # Test has isolated state automatically

        Continue using this function for:
            - Tests that rely on global Hub state via get_hub()
            - Integration tests that need to reset shared state
            - Legacy tests not yet using explicit dependency injection
    """
    from provide.foundation.testmode.orchestration import reset_foundation_for_testing

    reset_foundation_for_testing()


__all__ = [
    "mock_logger",
    "mock_logger_factory",
    "reset_foundation_setup_for_testing",
    "reset_foundation_state",
]
