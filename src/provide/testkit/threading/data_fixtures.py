#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Thread-safe data structure test fixtures.

Fixtures for thread-safe lists, counters, and other data structures for testing."""

from __future__ import annotations

from collections.abc import Iterable
import threading
from typing import Any

import pytest


class ThreadSafeList:
    """Simple thread-safe list wrapper."""

    def __init__(self) -> None:
        self._list: list[Any] = []
        self._lock = threading.Lock()

    def append(self, item: Any) -> None:
        """Thread-safe append."""
        with self._lock:
            self._list.append(item)

    def extend(self, items: Iterable[Any]) -> None:
        """Thread-safe extend."""
        with self._lock:
            self._list.extend(items)

    def get_all(self) -> list[Any]:
        """Get copy of all items."""
        with self._lock:
            return self._list.copy()

    def clear(self) -> None:
        """Clear the list."""
        with self._lock:
            self._list.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._list)

    def __getitem__(self, index: int) -> Any:
        with self._lock:
            return self._list[index]


class ThreadSafeCounter:
    """Thread-safe integer counter."""

    def __init__(self, initial: int = 0) -> None:
        self._value = initial
        self._lock = threading.Lock()

    def increment(self, amount: int = 1) -> int:
        """Thread-safe increment."""
        with self._lock:
            self._value += amount
            return self._value

    def decrement(self, amount: int = 1) -> int:
        """Thread-safe decrement."""
        with self._lock:
            self._value -= amount
            return self._value

    @property
    def value(self) -> int:
        """Get current value."""
        with self._lock:
            return self._value

    def reset(self, value: int = 0) -> None:
        """Reset counter."""
        with self._lock:
            self._value = value


@pytest.fixture
def thread_safe_list() -> ThreadSafeList:
    """
    Create a thread-safe list for collecting results.

    Returns:
        Thread-safe list implementation.
    """
    return ThreadSafeList()


@pytest.fixture
def thread_safe_counter() -> ThreadSafeCounter:
    """
    Create a thread-safe counter.

    Returns:
        Thread-safe counter implementation.
    """
    return ThreadSafeCounter()


__all__ = [
    "thread_safe_counter",
    "thread_safe_list",
]

# 🧪✅🔚
