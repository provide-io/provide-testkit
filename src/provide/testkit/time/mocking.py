"""Time mocking fixtures for testing.

Fixtures for mocking time-related functions like sleep, datetime.now(), etc.
"""

from __future__ import annotations

from collections.abc import Callable
import datetime
import time
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_sleep():
    """Mock time.sleep to speed up tests.

    Returns:
        Mock object that replaces time.sleep.

    Example:
        >>> def test_with_mock_sleep(mock_sleep):
        ...     time.sleep(10)  # Returns instantly
        ...     assert mock_sleep.called
    """
    with patch("time.sleep") as mock:
        # Make sleep instant by default
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_sleep_with_callback():
    """Mock time.sleep with a callback for each sleep call.

    Returns:
        Function to set up sleep mock with callback.

    Example:
        >>> def test_with_callback(mock_sleep_with_callback):
        ...     total_sleep = []
        ...     sleep_mock = mock_sleep_with_callback(lambda s: total_sleep.append(s))
        ...     with patch("time.sleep", sleep_mock):
        ...         time.sleep(1.5)
        ...     assert total_sleep == [1.5]
    """

    def _mock_sleep(callback: Callable[[float], None] | None = None):
        """Create a mock sleep with optional callback.

        Args:
            callback: Function called with sleep duration

        Returns:
            Mock sleep object
        """

        def sleep_side_effect(seconds) -> None:
            if callback:
                callback(seconds)
            return None

        mock = Mock(side_effect=sleep_side_effect)
        return mock

    return _mock_sleep


@pytest.fixture
def mock_datetime():
    """Mock datetime module for testing.

    Returns:
        Mock datetime module with common methods mocked.

    Example:
        >>> def test_with_mock_datetime(mock_datetime):
        ...     now = datetime.datetime.now()
        ...     assert now == datetime.datetime(2024, 1, 1, 12, 0, 0)
    """
    with patch("datetime.datetime") as mock_dt:
        # Set up a fake "now"
        fake_now = datetime.datetime(2024, 1, 1, 12, 0, 0)
        mock_dt.now.return_value = fake_now
        mock_dt.utcnow.return_value = fake_now
        mock_dt.today.return_value = fake_now.date()

        # Allow normal datetime construction
        mock_dt.side_effect = lambda *args, **kwargs: datetime.datetime(*args, **kwargs)

        yield mock_dt


@pytest.fixture
def time_travel():
    """Fixture for traveling through time in tests.

    Returns:
        Function to travel to specific time points.

    Example:
        >>> def test_with_time_travel(time_travel):
        ...     time_travel(datetime.datetime(2025, 1, 1))
        ...     # time.time() now returns the timestamp for 2025-01-01
    """
    original_time = time.time
    current_offset = 0.0

    def mock_time():
        return original_time() + current_offset

    def _travel_to(target: datetime.datetime) -> None:
        """Travel to a specific point in time.

        Args:
            target: The datetime to travel to
        """
        nonlocal current_offset
        current_offset = target.timestamp() - original_time()

    with patch("time.time", mock_time):
        yield _travel_to


__all__ = [
    "mock_datetime",
    "mock_sleep",
    "mock_sleep_with_callback",
    "time_travel",
]
