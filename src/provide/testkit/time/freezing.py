"""Time freezing fixtures for testing.

Fixtures for freezing time and controlling time flow in tests.
"""

from __future__ import annotations

import datetime

import pytest

from provide.testkit.time.classes import FrozenTime, TimeMachine


@pytest.fixture
def freeze_time():
    """Fixture to freeze time at a specific point.

    Returns:
        Function that freezes time and returns a context manager.

    Example:
        >>> def test_with_frozen_time(freeze_time):
        ...     with freeze_time(datetime.datetime(2024, 1, 1)) as frozen:
        ...         # Time is frozen at 2024-01-01
        ...         frozen.tick(seconds=60)  # Advance by 60 seconds
    """

    def _freeze(at: datetime.datetime | None = None) -> FrozenTime:
        """Freeze time at a specific point.

        Args:
            at: Optional datetime to freeze at (defaults to now)

        Returns:
            FrozenTime context manager
        """
        return FrozenTime(at)

    return _freeze


@pytest.fixture
def time_machine(request: pytest.FixtureRequest) -> TimeMachine:
    """Advanced time manipulation fixture.

    Yields:
        TimeMachine instance for time manipulation.

    IMPORTANT: Uses request.addfinalizer() to ensure patches are stopped
    BEFORE pytest-asyncio creates event loops for the next test. Also forcibly
    closes ALL event loops to prevent cached frozen time.monotonic references.

    Example:
        >>> def test_with_time_machine(time_machine):
        ...     time_machine.freeze(at=time.time())
        ...     # Perform tests with frozen time
        ...     time_machine.jump(seconds=60)  # Jump forward
        ...     time_machine.unfreeze()
    """
    machine = TimeMachine()

    # Register cleanup with highest priority (runs before standard teardown)
    # This ensures time patches are stopped before pytest-asyncio creates
    # event loops for the next test
    def cleanup_patches() -> None:
        machine.cleanup()

        # NUCLEAR OPTION: Close ALL event loops to force fresh creation
        # This is necessary because event loops cache time.monotonic references
        # at creation time, and those cached values persist even after patches stop
        try:
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if not loop.is_running() and not loop.is_closed():
                    loop.close()
            except RuntimeError:
                pass

            # Also close the running loop if there is one
            try:
                asyncio.get_running_loop()
                # Can't close running loop, but we can stop it
            except RuntimeError:
                pass

        except Exception:
            pass

    request.addfinalizer(cleanup_patches)

    yield machine

    # Also call cleanup here as backup (defensive)
    machine.cleanup()


__all__ = [
    "freeze_time",
    "time_machine",
]
