"""Time testing classes for fixtures.

Core classes used by time testing fixtures. Extracted from fixtures.py
for better organization and discoverability.
"""

from __future__ import annotations

import datetime
import time
from typing import Any
from unittest.mock import patch

# Module-level registry for tracking active TimeMachine instances
# Used by test fixtures to avoid expensive gc.get_objects() scans
_active_time_machines: set[Any] = set()  # Will contain TimeMachine instances


def get_active_time_machines() -> set[Any]:
    """Get set of currently active TimeMachine instances.

    Returns:
        Set of TimeMachine instances that are currently active.

    Note:
        Thread-safe within a process. pytest-xdist workers are separate processes,
        so no cross-process synchronization needed.
    """
    return _active_time_machines.copy()  # Return copy to prevent external modification


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

        # Register in global registry for efficient cleanup
        _active_time_machines.add(self)

    def freeze(self, at: float | None = None) -> TimeMachine:
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
        for p in self.patches:
            try:
                p.stop()
            except Exception:
                # Ignore errors - module might be unloaded/reloaded
                pass
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

        # Unregister from global registry
        _active_time_machines.discard(self)  # discard() won't raise if not in set


class FrozenTime:
    """Context manager for freezing time at a specific point."""

    def __init__(self, frozen_time: datetime.datetime | None = None) -> None:
        """Initialize frozen time context.

        Args:
            frozen_time: Time to freeze at (defaults to now)
        """
        self.frozen_time = frozen_time or datetime.datetime.now()
        self.original_time = time.time
        self.original_datetime = datetime.datetime
        self.patches = []

    def __enter__(self):
        """Enter frozen time context."""
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
        """Exit frozen time context."""
        for p in self.patches:
            p.stop()

    def tick(self, seconds: float = 1.0) -> None:
        """Advance the frozen time by the specified seconds."""
        self.frozen_time += datetime.timedelta(seconds=seconds)
        # Update mocks
        for p in self.patches:
            if hasattr(p, "return_value"):
                p.return_value = self.frozen_time.timestamp()


class Timer:
    """Timer for measuring execution time."""

    def __init__(self) -> None:
        """Initialize timer."""
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


class MockRateLimiter:
    """Mock for testing rate-limited code."""

    def __init__(self) -> None:
        """Initialize mock rate limiter."""
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


class BenchmarkTimer:
    """Timer specifically for benchmarking code."""

    def __init__(self) -> None:
        """Initialize benchmark timer."""
        self.measurements = []

    def measure(self, func, *args, **kwargs) -> tuple[Any, float]:
        """Measure execution time of a function.

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


__all__ = [
    "BenchmarkTimer",
    "FrozenTime",
    "MockRateLimiter",
    "TimeMachine",
    "Timer",
    "get_active_time_machines",
]
