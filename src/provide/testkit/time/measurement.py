"""Time measurement fixtures for testing.

Fixtures for measuring execution time and benchmarking.
"""

from __future__ import annotations

import pytest

from provide.testkit.time.classes import BenchmarkTimer, Timer


@pytest.fixture
def timer():
    """Timer fixture for measuring execution time.

    Returns:
        Timer instance for measuring durations.

    Example:
        >>> def test_with_timer(timer):
        ...     with timer:
        ...         # Code to time
        ...         pass
        ...     print(f"Elapsed: {timer.elapsed}s")
    """
    return Timer()


@pytest.fixture
def benchmark_timer():
    """Timer specifically for benchmarking code.

    Returns:
        Benchmark timer with statistics.

    Example:
        >>> def test_with_benchmark(benchmark_timer):
        ...     result, duration = benchmark_timer.measure(my_function, arg1, arg2)
        ...     benchmark_timer.assert_faster_than(0.1)  # Assert < 100ms
    """
    return BenchmarkTimer()


__all__ = [
    "benchmark_timer",
    "timer",
]
