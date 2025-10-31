#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Thread synchronization test fixtures.

Fixtures for thread barriers, events, conditions, and other synchronization primitives."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
import threading

import pytest


@pytest.fixture
def thread_barrier() -> Callable[[int, float | None], threading.Barrier]:
    """
    Create a barrier for thread synchronization.

    Returns:
        Function to create barriers for N threads.
    """
    barriers: list[threading.Barrier] = []

    def _create_barrier(n_threads: int, timeout: float | None = None) -> threading.Barrier:
        """
        Create a barrier for synchronizing threads.

        Args:
            n_threads: Number of threads to synchronize
            timeout: Optional timeout for barrier

        Returns:
            Barrier instance
        """
        barrier = threading.Barrier(n_threads, timeout=timeout)
        barriers.append(barrier)
        return barrier

    yield _create_barrier

    # Cleanup: abort all barriers
    for barrier in barriers:
        with suppress(threading.BrokenBarrierError):
            barrier.abort()


@pytest.fixture
def thread_event() -> Callable[[], threading.Event]:
    """
    Create thread events for signaling.

    Returns:
        Function to create thread events.
    """
    events: list[threading.Event] = []

    def _create_event() -> threading.Event:
        """Create a thread event."""
        event = threading.Event()
        events.append(event)
        return event

    yield _create_event

    # Cleanup: set all events to release waiting threads
    for event in events:
        event.set()


@pytest.fixture
def thread_condition() -> Callable[[threading.Lock | None], threading.Condition]:
    """
    Create condition variables for thread coordination.

    Returns:
        Function to create condition variables.
    """

    def _create_condition(lock: threading.Lock | None = None) -> threading.Condition:
        """
        Create a condition variable.

        Args:
            lock: Optional lock to use (creates new if None)

        Returns:
            Condition variable
        """
        return threading.Condition(lock)

    return _create_condition


__all__ = [
    "thread_barrier",
    "thread_condition",
    "thread_event",
]

# 🧪✅🔚
