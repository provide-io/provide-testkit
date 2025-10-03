"""
Time Testing Fixtures and Utilities.

Fixtures for mocking time, freezing time, and testing time-dependent code
across the provide-io ecosystem.
"""

from __future__ import annotations

from collections.abc import Callable
import datetime
import time
from typing import Any
from unittest.mock import Mock, patch

import pytest


class TimeMachine:
    """Advanced time manipulation class for testing.

    Provides methods to:
    - Freeze time
    - Speed up/slow down time
    - Jump to specific times
    """

    def __init__(self) -> None:
        """Initialize the TimeMachine."""
        self.current_time = time.time()
        self.speed_multiplier = 1.0
        self.patches: list[Any] = []
        self.is_frozen = False

    def freeze(self, at: float | None = None) -> "TimeMachine":
        """Freeze time at a specific timestamp."""
        self.is_frozen = True
        self.current_time = at or time.time()

        # Patch global time.time
        global_patcher = patch("time.time", return_value=self.current_time)
        global_patcher.start()
        self.patches.append(global_patcher)

        # Patch time.monotonic as well for timing operations
        monotonic_patcher = patch("time.monotonic", return_value=self.current_time)
        monotonic_patcher.start()
        self.patches.append(monotonic_patcher)

        # Patch module-specific time imports for provide.foundation modules
        module_patches = [
            "provide.foundation.state._internal.transitions.time.time",
            "provide.foundation.state._internal.transitions.time.monotonic",
            "provide.foundation.resilience.retry.time.time",
            "provide.foundation.resilience.retry.time.monotonic",
            "provide.foundation.resilience.circuit.time.time",
            "provide.foundation.resilience.circuit.time.monotonic",
            "provide.foundation.utils.rate_limiting.time.time",
            "provide.foundation.utils.rate_limiting.time.monotonic",
            "provide.foundation.utils.timing.time.time",
            "provide.foundation.utils.timing.time.monotonic",
            "provide.foundation.transport.middleware.time.time",
            "provide.foundation.transport.middleware.time.monotonic",
            "provide.foundation.tracer.spans.time.time",
            "provide.foundation.tracer.spans.time.monotonic",
        ]

        for module_path in module_patches:
            try:
                patcher = patch(module_path, return_value=self.current_time)
                patcher.start()
                self.patches.append(patcher)
            except (ImportError, AttributeError):
                # Module might not be imported yet or doesn't exist
                pass

        return self

    def _stop_all_patches(self) -> None:
        """Stop and clear all active patches robustly."""
        import sys
        for p in self.patches:
            try:
                p.stop()
            except Exception as e:
                # Debug: show what's failing
                print(f"[TimeMachine] Failed to stop patch {p}: {e}", file=sys.stderr)
        print(f"[TimeMachine] Stopped {len(self.patches)} patches", file=sys.stderr)
        self.patches.clear()

    def unfreeze(self) -> None:
        """Unfreeze time."""
        self.is_frozen = False
        self._stop_all_patches()

    def jump(self, seconds: float) -> None:
        """Jump forward or backward in time."""
        self.current_time += seconds
        if self.is_frozen:
            # Stop all patches and restart them with the new time
            self.unfreeze()
            self.freeze(self.current_time)

    def speed_up(self, factor: float) -> None:
        """Speed up time by a factor."""
        self.speed_multiplier = factor

    def slow_down(self, factor: float) -> None:
        """Slow down time by a factor."""
        self.speed_multiplier = 1.0 / factor

    def cleanup(self) -> None:
        """Clean up all patches and reset state."""
        self.is_frozen = False
        self._stop_all_patches()


@pytest.fixture
def freeze_time():
    """
    Fixture to freeze time at a specific point.

    Returns:
        Function that freezes time and returns a context manager.
    """

    class FrozenTime:
        def __init__(self, frozen_time: datetime.datetime | None = None) -> None:
            self.frozen_time = frozen_time or datetime.datetime.now()
            self.original_time = time.time
            self.original_datetime = datetime.datetime
            self.patches = []

        def __enter__(self):
            # Patch time.time()
            time_patch = patch("time.time", return_value=self.frozen_time.timestamp())
            self.patches.append(time_patch)
            time_patch.start()

            # Patch datetime.datetime.now()
            datetime_patch = patch("datetime.datetime", wraps=datetime.datetime)
            mock_datetime = datetime_patch.start()
            mock_datetime.now.return_value = self.frozen_time
            mock_datetime.utcnow.return_value = self.frozen_time
            self.patches.append(datetime_patch)

            return self

        def __exit__(self, *args):
            for p in self.patches:
                p.stop()

        def tick(self, seconds: float = 1.0) -> None:
            """Advance the frozen time by the specified seconds."""
            self.frozen_time += datetime.timedelta(seconds=seconds)
            # Update mocks
            for p in self.patches:
                if hasattr(p, "return_value"):
                    p.return_value = self.frozen_time.timestamp()

    def _freeze(at: datetime.datetime | None = None) -> FrozenTime:
        """
        Freeze time at a specific point.

        Args:
            at: Optional datetime to freeze at (defaults to now)

        Returns:
            FrozenTime context manager
        """
        return FrozenTime(at)

    return _freeze


@pytest.fixture
def mock_sleep():
    """
    Mock time.sleep to speed up tests.

    Returns:
        Mock object that replaces time.sleep.
    """
    with patch("time.sleep") as mock:
        # Make sleep instant by default
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_sleep_with_callback():
    """
    Mock time.sleep with a callback for each sleep call.

    Returns:
        Function to set up sleep mock with callback.
    """

    def _mock_sleep(callback: Callable[[float], None] | None = None):
        """
        Create a mock sleep with optional callback.

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
def time_machine() -> TimeMachine:
    """
    Advanced time manipulation fixture.

    Yields:
        TimeMachine instance for time manipulation.
    """
    machine = TimeMachine()
    yield machine
    machine.cleanup()


@pytest.fixture
def timer():
    """
    Timer fixture for measuring execution time.

    Returns:
        Timer instance for measuring durations.
    """

    class Timer:
        def __init__(self) -> None:
            self.start_time = None
            self.end_time = None
            self.durations = []

        def start(self):
            """Start the timer."""
            self.start_time = time.perf_counter()
            return self

        def stop(self) -> float:
            """Stop the timer and return duration."""
            self.end_time = time.perf_counter()
            if self.start_time is None:
                raise RuntimeError("Timer not started")
            duration = self.end_time - self.start_time
            self.durations.append(duration)
            return duration

        def __enter__(self):
            """Context manager entry."""
            self.start()
            return self

        def __exit__(self, *args):
            """Context manager exit."""
            self.stop()

        @property
        def elapsed(self) -> float:
            """Get elapsed time since start."""
            if self.start_time is None:
                raise RuntimeError("Timer not started")
            if self.end_time is None:
                return time.perf_counter() - self.start_time
            return self.end_time - self.start_time

        @property
        def average(self) -> float:
            """Get average duration from all measurements."""
            if not self.durations:
                return 0.0
            return sum(self.durations) / len(self.durations)

        def reset(self) -> None:
            """Reset the timer."""
            self.start_time = None
            self.end_time = None
            self.durations.clear()

    return Timer()


@pytest.fixture
def mock_datetime():
    """
    Mock datetime module for testing.

    Returns:
        Mock datetime module with common methods mocked.
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
    """
    Fixture for traveling through time in tests.

    Returns:
        Function to travel to specific time points.
    """
    original_time = time.time
    current_offset = 0.0

    def mock_time():
        return original_time() + current_offset

    def _travel_to(target: datetime.datetime) -> None:
        """
        Travel to a specific point in time.

        Args:
            target: The datetime to travel to
        """
        nonlocal current_offset
        current_offset = target.timestamp() - original_time()

    with patch("time.time", mock_time):
        yield _travel_to


@pytest.fixture
def rate_limiter_mock():
    """
    Mock for testing rate-limited code.

    Returns:
        Mock rate limiter that can be controlled in tests.
    """

    class MockRateLimiter:
        def __init__(self) -> None:
            self.calls = []
            self.should_limit = False
            self.limit_after = None
            self.call_count = 0

        def check(self) -> bool:
            """Check if rate limit is exceeded."""
            self.call_count += 1
            self.calls.append(time.time())

            if self.limit_after and self.call_count > self.limit_after:
                return False  # Rate limited

            return not self.should_limit

        def reset(self) -> None:
            """Reset the rate limiter."""
            self.calls.clear()
            self.call_count = 0
            self.should_limit = False
            self.limit_after = None

        def set_limit(self, after_calls: int) -> None:
            """Set to limit after N calls."""
            self.limit_after = after_calls

    return MockRateLimiter()


@pytest.fixture
def benchmark_timer():
    """
    Timer specifically for benchmarking code.

    Returns:
        Benchmark timer with statistics.
    """

    class BenchmarkTimer:
        def __init__(self) -> None:
            self.measurements = []

        def measure(self, func: Callable, *args, **kwargs) -> tuple[Any, float]:
            """
            Measure execution time of a function.

            Args:
                func: Function to measure
                *args: Function arguments
                **kwargs: Function keyword arguments

            Returns:
                Tuple of (result, duration)
            """
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            self.measurements.append(duration)
            return result, duration

        @property
        def min_time(self) -> float:
            """Get minimum execution time."""
            return min(self.measurements) if self.measurements else 0.0

        @property
        def max_time(self) -> float:
            """Get maximum execution time."""
            return max(self.measurements) if self.measurements else 0.0

        @property
        def avg_time(self) -> float:
            """Get average execution time."""
            return sum(self.measurements) / len(self.measurements) if self.measurements else 0.0

        def assert_faster_than(self, seconds: float) -> None:
            """Assert all measurements were faster than threshold."""
            if not self.measurements:
                raise AssertionError("No measurements taken")
            if self.max_time > seconds:
                raise AssertionError(f"Maximum time {self.max_time:.3f}s exceeded threshold {seconds:.3f}s")

    return BenchmarkTimer()


# Utility functions that can be imported directly
def advance_time(mock_time: Mock, seconds: float) -> None:
    """
    Advance a mocked time by specified seconds.

    Args:
        mock_time: The mock time object
        seconds: Number of seconds to advance
    """
    if hasattr(mock_time, "return_value"):
        mock_time.return_value += seconds


__all__ = [
    "TimeMachine",
    "advance_time",
    "benchmark_timer",
    "freeze_time",
    "mock_datetime",
    "mock_sleep",
    "mock_sleep_with_callback",
    "rate_limiter_mock",
    "time_machine",
    "time_travel",
    "timer",
]
