"""Time testing utilities for the provide-io ecosystem.

Fixtures and utilities for mocking time, freezing time, and testing
time-dependent code across any project that depends on provide.foundation.
"""

from provide.testkit.time.fixtures import (
    BenchmarkTimer,
    FrozenTime,
    MockRateLimiter,
    TimeMachine,
    Timer,
    advance_time,
    benchmark_timer,
    freeze_time,
    get_active_time_machines,
    make_controlled_time,
    mock_datetime,
    mock_sleep,
    mock_sleep_with_callback,
    rate_limiter_mock,
    time_machine,
    time_travel,
    timer,
)

__all__ = [
    # Classes
    "BenchmarkTimer",
    "FrozenTime",
    "MockRateLimiter",
    "TimeMachine",
    "Timer",
    # Utilities and fixtures
    "advance_time",
    "benchmark_timer",
    "freeze_time",
    "get_active_time_machines",
    "make_controlled_time",
    "mock_datetime",
    "mock_sleep",
    "mock_sleep_with_callback",
    "rate_limiter_mock",
    "time_machine",
    "time_travel",
    "timer",
]
