#
# reset.py
#
"""
Logger Testing Utilities for Foundation.

Provides utilities for resetting logger state, managing configurations,
and ensuring test isolation for the Foundation logging system.
"""

from unittest.mock import Mock

import pytest

# Note: Removed module-level imports to avoid circular imports
# All Foundation imports will be done within functions when needed


@pytest.fixture
def mock_logger():
    """
    Comprehensive mock logger for testing.

    Provides compatibility with both stdlib logging and structlog interfaces,
    including method call tracking and common logger attributes.

    Returns:
        Mock logger with debug, info, warning, error methods and structlog compatibility.
    """
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.warn = Mock()  # Alias for warning
    logger.error = Mock()
    logger.exception = Mock()
    logger.critical = Mock()
    logger.fatal = Mock()  # Alias for critical

    # Add common logger attributes
    logger.name = "mock_logger"
    logger.level = 10  # DEBUG level
    logger.handlers = []
    logger.disabled = False

    # Add structlog compatibility methods
    logger.bind = Mock(return_value=logger)
    logger.unbind = Mock(return_value=logger)
    logger.new = Mock(return_value=logger)
    logger.msg = Mock()  # Alternative to info

    # Add trace method for Foundation's extended logging
    logger.trace = Mock()

    return logger


def mock_logger_factory():
    """
    Factory function to create mock loggers outside of pytest context.

    Useful for unit tests that need a mock logger but aren't using pytest fixtures.

    Returns:
        Mock logger with the same interface as the pytest fixture.
    """
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.warn = Mock()
    logger.error = Mock()
    logger.exception = Mock()
    logger.critical = Mock()
    logger.fatal = Mock()

    logger.name = "mock_logger"
    logger.level = 10
    logger.handlers = []
    logger.disabled = False

    logger.bind = Mock(return_value=logger)
    logger.unbind = Mock(return_value=logger)
    logger.new = Mock(return_value=logger)
    logger.msg = Mock()
    logger.trace = Mock()

    return logger


def _reset_opentelemetry_providers() -> None:
    """
    Reset OpenTelemetry providers to uninitialized state.

    This prevents "Overriding of current TracerProvider/MeterProvider" warnings
    and stream closure issues by properly resetting the global providers.
    """
    try:
        # Reset tracing provider more thoroughly
        import opentelemetry.trace as otel_trace

        # Reset the Once flag to allow re-initialization
        if hasattr(otel_trace, "_TRACER_PROVIDER_SET_ONCE"):
            once_obj = otel_trace._TRACER_PROVIDER_SET_ONCE
            if hasattr(once_obj, "_done"):
                once_obj._done = False
            if hasattr(once_obj, "_lock"):
                with once_obj._lock:
                    once_obj._done = False

        # Reset to NoOpTracerProvider
        from opentelemetry.trace import NoOpTracerProvider

        otel_trace.set_tracer_provider(NoOpTracerProvider())

    except ImportError:
        # OpenTelemetry tracing not available
        pass
    except Exception:
        # Ignore errors during reset - better to continue than fail
        pass

    try:
        # Reset metrics provider more thoroughly
        import opentelemetry.metrics as otel_metrics
        import opentelemetry.metrics._internal as otel_metrics_internal

        # Reset the Once flag to allow re-initialization
        if hasattr(otel_metrics_internal, "_METER_PROVIDER_SET_ONCE"):
            once_obj = otel_metrics_internal._METER_PROVIDER_SET_ONCE
            if hasattr(once_obj, "_done"):
                once_obj._done = False
            if hasattr(once_obj, "_lock"):
                with once_obj._lock:
                    once_obj._done = False

        # Reset to NoOpMeterProvider
        from opentelemetry.metrics import NoOpMeterProvider

        otel_metrics.set_meter_provider(NoOpMeterProvider())

    except ImportError:
        # OpenTelemetry metrics not available
        pass
    except Exception:
        # Ignore errors during reset - better to continue than fail
        pass


def reset_foundation_state() -> None:
    """
    Internal function to reset structlog and Foundation's state using Hub-based approach.

    This resets:
    - structlog configuration to defaults
    - Foundation Hub state (which manages all Foundation components)
    - Stream state back to defaults
    - Lazy setup state tracking (if available)
    - OpenTelemetry provider state (if available)
    """
    # Use the new internal reset APIs from Foundation's testmode module
    from provide.foundation.testmode.internal import (
        reset_coordinator_state,
        reset_eventsets_state,
        reset_hub_state,
        reset_logger_state,
        reset_streams_state,
        reset_structlog_state,
    )

    # Reset in the proper order to avoid triggering reinitialization
    reset_structlog_state()
    reset_streams_state()

    # Reset OpenTelemetry providers to avoid "Overriding" warnings and stream closure
    # Note: OpenTelemetry providers are designed to prevent override for safety.
    # In test environments, we suppress this reset to avoid hanging/blocking.
    # The warnings are harmless in test context.
    _reset_opentelemetry_providers()

    # Reset lazy setup state FIRST to prevent hub operations from triggering setup
    reset_logger_state()

    # Clear Hub (this handles all Foundation state including logger instances)
    reset_hub_state()

    # Reset coordinator and event set state
    reset_coordinator_state()
    reset_eventsets_state()

    # Final reset of logger state (after all operations that might trigger setup)
    reset_logger_state()


def reset_foundation_setup_for_testing() -> None:
    """
    Public test utility to reset Foundation's internal state using Hub-based approach.

    This function ensures clean test isolation by resetting all
    Foundation state between test runs. Now uses Hub.clear_hub() which
    properly resets all Foundation components.
    """
    # Full reset with Hub-based state management
    reset_foundation_state()

    # Re-register HTTP transport for tests that need it
    try:
        from provide.foundation.transport.http import _register_http_transport

        _register_http_transport()
    except ImportError:
        # Transport module not available
        pass

    # Final reset of lazy setup state (after transport registration)
    try:
        from provide.foundation.logger.core import _LAZY_SETUP_STATE

        _LAZY_SETUP_STATE.update({"done": False, "error": None, "in_progress": False})
    except ImportError:
        # Legacy state not available, skip
        pass


__all__ = [
    "mock_logger",
    "mock_logger_factory",
    "reset_foundation_setup_for_testing",
    "reset_foundation_state",
]
