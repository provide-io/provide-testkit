"""Controlled time utilities for testing.

Injectable time sources and sleep functions that don't rely on global mocking.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from unittest.mock import Mock


def make_controlled_time() -> tuple[
    Callable[[], float],
    Callable[[float], None],
    Callable[[float], None],
    Callable[[float], Awaitable[None]],
]:
    """Create controlled time source and sleep functions for testing.

    This provides injectable time/sleep functions that don't rely on global mocking,
    making tests faster and more reliable. Use these instead of time_machine.freeze()
    for retry/circuit breaker tests.

    Returns:
        Tuple of (get_time, advance_time, fake_sleep, fake_async_sleep)

    Example:
        >>> get_time, advance_time, fake_sleep, fake_async_sleep = make_controlled_time()
        >>> executor = RetryExecutor(
        ...     policy,
        ...     time_source=get_time,
        ...     sleep_func=fake_sleep,
        ...     async_sleep_func=fake_async_sleep,
        ... )
        >>> # In tests:
        >>> advance_time(5.0)  # Simulate 5 seconds passing
        >>> assert get_time() == 5.0
    """
    current_time = [0.0]

    def get_time() -> float:
        """Get current test time."""
        return current_time[0]

    def advance_time(seconds: float) -> None:
        """Advance test time by seconds."""
        current_time[0] += seconds

    def fake_sleep(seconds: float) -> None:
        """Fake sleep that advances time instead of blocking."""
        advance_time(seconds)

    async def fake_async_sleep(seconds: float) -> None:
        """Fake async sleep that advances time instead of blocking."""
        advance_time(seconds)

    return get_time, advance_time, fake_sleep, fake_async_sleep


def advance_time(mock_time: Mock, seconds: float) -> None:
    """Advance a mocked time by specified seconds.

    Args:
        mock_time: The mock time object
        seconds: Number of seconds to advance

    Example:
        >>> from unittest.mock import Mock, patch
        >>> with patch("time.time") as mock_time:
        ...     mock_time.return_value = 100.0
        ...     advance_time(mock_time, 50.0)
        ...     assert mock_time.return_value == 150.0
    """
    if hasattr(mock_time, "return_value"):
        mock_time.return_value += seconds


__all__ = [
    "advance_time",
    "make_controlled_time",
]
