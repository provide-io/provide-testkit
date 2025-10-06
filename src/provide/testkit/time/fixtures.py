"""Time Testing Fixtures and Utilities.

Fixtures for mocking time, freezing time, and testing time-dependent code
across the provide-io ecosystem.

This module re-exports all time testing fixtures for backward compatibility.
The actual implementations have been split into separate modules for better
organization:

- classes.py: Core classes (TimeMachine, Timer, etc.)
- freezing.py: Time freezing fixtures
- measurement.py: Timer fixtures
- mocking.py: Mock fixtures
- controlled.py: Controlled time utilities
- rate_limiting.py: Rate limiter mocks
"""

from __future__ import annotations

# Re-export all classes
from provide.testkit.time.classes import (
    BenchmarkTimer,
    FrozenTime,
    MockRateLimiter,
    TimeMachine,
    Timer,
    get_active_time_machines,
)

# Re-export all utilities
from provide.testkit.time.controlled import (
    advance_time,
    make_controlled_time,
)

# Re-export all fixtures
from provide.testkit.time.freezing import (
    freeze_time,
    time_machine,
)
from provide.testkit.time.measurement import (
    benchmark_timer,
    timer,
)
from provide.testkit.time.mocking import (
    mock_datetime,
    mock_sleep,
    mock_sleep_with_callback,
    time_travel,
)
from provide.testkit.time.rate_limiting import (
    rate_limiter_mock,
)

__all__ = [
    # Classes
    "BenchmarkTimer",
    "FrozenTime",
    "MockRateLimiter",
    "TimeMachine",
    "Timer",
    # Utilities
    "advance_time",
    # Fixtures
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
