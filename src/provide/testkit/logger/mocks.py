#
# mocks.py
#
"""
Logger Mock Utilities for Testing.

Provides mock logger fixtures and factories for testing Foundation-based
applications. These are logger-specific mocks that complement the Foundation
reset orchestration.
"""

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_logger() -> Mock:
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


def mock_logger_factory() -> Mock:
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


__all__ = [
    "mock_logger",
    "mock_logger_factory",
]
