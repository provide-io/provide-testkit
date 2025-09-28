"""
Time Mocking Utilities.

Provides utilities for mocking time-related functions in tests,
particularly sleep functions from both time and asyncio modules.
"""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from contextlib import contextmanager
import time
from typing import Any
from unittest.mock import Mock, patch


class SleepTracker:
    """Tracks sleep calls and their durations."""

    def __init__(self) -> None:
        """Initialize sleep tracker."""
        self.calls: list[float] = []
        self.total_sleep_time: float = 0.0

    def add_call(self, duration: float) -> None:
        """Add a sleep call."""
        self.calls.append(duration)
        self.total_sleep_time += duration

    def reset(self) -> None:
        """Reset tracking data."""
        self.calls.clear()
        self.total_sleep_time = 0.0

    @property
    def call_count(self) -> int:
        """Get number of sleep calls."""
        return len(self.calls)


@contextmanager
def mock_sleep(
    instant: bool = True,
    track_calls: bool = True,
    side_effect: Any = None,
) -> Generator[SleepTracker, None, None]:
    """Context manager to mock both time.sleep and asyncio.sleep.

    Args:
        instant: If True, sleep calls return immediately. If False, use side_effect.
        track_calls: If True, track all sleep calls and durations.
        side_effect: Custom side effect for sleep calls. Ignored if instant=True.

    Yields:
        SleepTracker instance for inspecting sleep calls.

    Example:
        with mock_sleep() as sleep_tracker:
            time.sleep(1.0)
            asyncio.sleep(2.0)
            assert sleep_tracker.call_count == 2
            assert sleep_tracker.total_sleep_time == 3.0
    """
    tracker = SleepTracker()

    def time_sleep_mock(duration: float) -> None:
        """Mock implementation of time.sleep."""
        if track_calls:
            tracker.add_call(duration)
        if not instant and side_effect:
            return side_effect(duration)

    async def asyncio_sleep_mock(duration: float) -> None:
        """Mock implementation of asyncio.sleep."""
        if track_calls:
            tracker.add_call(duration)
        if not instant and side_effect:
            result = side_effect(duration)
            if asyncio.iscoroutine(result):
                return await result
            return result

    with (
        patch("time.sleep", side_effect=time_sleep_mock) as time_mock,
        patch("asyncio.sleep", side_effect=asyncio_sleep_mock) as asyncio_mock,
    ):
        try:
            yield tracker
        finally:
            pass


@contextmanager
def mock_time_sleep(
    instant: bool = True,
    track_calls: bool = True,
    side_effect: Any = None,
) -> Generator[SleepTracker, None, None]:
    """Context manager to mock only time.sleep.

    Args:
        instant: If True, sleep calls return immediately. If False, use side_effect.
        track_calls: If True, track all sleep calls and durations.
        side_effect: Custom side effect for sleep calls. Ignored if instant=True.

    Yields:
        SleepTracker instance for inspecting sleep calls.
    """
    tracker = SleepTracker()

    def time_sleep_mock(duration: float) -> None:
        """Mock implementation of time.sleep."""
        if track_calls:
            tracker.add_call(duration)
        if not instant and side_effect:
            return side_effect(duration)

    with patch("time.sleep", side_effect=time_sleep_mock):
        yield tracker


@contextmanager
def mock_asyncio_sleep(
    instant: bool = True,
    track_calls: bool = True,
    side_effect: Any = None,
) -> Generator[SleepTracker, None, None]:
    """Context manager to mock only asyncio.sleep.

    Args:
        instant: If True, sleep calls return immediately. If False, use side_effect.
        track_calls: If True, track all sleep calls and durations.
        side_effect: Custom side effect for sleep calls. Ignored if instant=True.

    Yields:
        SleepTracker instance for inspecting sleep calls.
    """
    tracker = SleepTracker()

    async def asyncio_sleep_mock(duration: float) -> None:
        """Mock implementation of asyncio.sleep."""
        if track_calls:
            tracker.add_call(duration)
        if not instant and side_effect:
            result = side_effect(duration)
            if asyncio.iscoroutine(result):
                return await result
            return result

    with patch("asyncio.sleep", side_effect=asyncio_sleep_mock):
        yield tracker


def create_sleep_mock(instant: bool = True, track_calls: bool = True) -> Mock:
    """Create a mock for sleep functions with tracking.

    Args:
        instant: If True, sleep calls return immediately.
        track_calls: If True, track all sleep calls and durations.

    Returns:
        Mock object with sleep tracking capabilities.
    """
    mock = Mock()
    tracker = SleepTracker()

    def sleep_side_effect(duration: float) -> None:
        if track_calls:
            tracker.add_call(duration)

    mock.side_effect = sleep_side_effect
    mock.tracker = tracker
    return mock


__all__ = [
    "SleepTracker",
    "mock_sleep",
    "mock_time_sleep",
    "mock_asyncio_sleep",
    "create_sleep_mock",
]