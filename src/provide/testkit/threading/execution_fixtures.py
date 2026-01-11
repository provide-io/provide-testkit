#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Thread execution and testing helper fixtures.

Advanced fixtures for concurrent execution, synchronization testing, deadlock detection,
and exception handling in threaded code."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from typing import Any

import pytest


class ConcurrentExecutor:
    """Run callables concurrently while capturing results and exceptions."""

    def __init__(self) -> None:
        self.results: list[Any] = []
        self.exceptions: list[Exception] = []

    def run_concurrent(
        self,
        func: Callable[..., Any],
        args_list: Sequence[Sequence[Any] | Any],
        max_workers: int = 4,
    ) -> list[Any]:
        """Run ``func`` concurrently with provided argument sets."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for args in args_list:
                if isinstance(args, Sequence) and not isinstance(args, (str, bytes)):
                    future = executor.submit(func, *args)
                else:
                    future = executor.submit(func, args)
                futures.append(future)

            results: list[Any] = []
            for future in futures:
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                    self.results.append(result)
                except Exception as exc:
                    self.exceptions.append(exc)
                    results.append(None)

            return results

    def run_parallel(self, funcs: Sequence[Callable[[], Any]], timeout: float = 10) -> list[Any]:
        """Run multiple zero-argument callables in parallel."""
        with ThreadPoolExecutor(max_workers=len(funcs)) as executor:
            futures = [executor.submit(func) for func in funcs]
            results: list[Any] = []

            for future in futures:
                try:
                    result = future.result(timeout=timeout)
                    results.append(result)
                except Exception as exc:
                    self.exceptions.append(exc)
                    results.append(None)

            return results


class ThreadSynchronizer:
    """Coordinate threads using named checkpoints."""

    def __init__(self) -> None:
        self.checkpoints: dict[str, list[tuple[int, float]]] = {}

    def checkpoint(self, name: str, thread_id: int | None = None) -> None:
        thread_id = thread_id or threading.get_ident()
        if name not in self.checkpoints:
            self.checkpoints[name] = []
        self.checkpoints[name].append((thread_id, time.time()))

    def wait_for_checkpoint(self, name: str, count: int, timeout: float = 5.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if name in self.checkpoints and len(self.checkpoints[name]) >= count:
                return True
            time.sleep(0.01)
        return False

    def get_order(self, checkpoint: str) -> list[int]:
        if checkpoint not in self.checkpoints:
            return []
        return [tid for tid, _ in sorted(self.checkpoints[checkpoint], key=lambda x: x[1])]

    def clear(self) -> None:
        self.checkpoints.clear()


class DeadlockDetector:
    """Track lock ownership to flag potential deadlocks."""

    def __init__(self) -> None:
        self.locks_held: dict[int, set[str]] = {}
        self.lock = threading.Lock()

    def acquire(self, lock_name: str, thread_id: int | None = None) -> None:
        thread_id = thread_id or threading.get_ident()
        with self.lock:
            self.locks_held.setdefault(thread_id, set()).add(lock_name)

    def release(self, lock_name: str, thread_id: int | None = None) -> None:
        thread_id = thread_id or threading.get_ident()
        with self.lock:
            if thread_id in self.locks_held:
                self.locks_held[thread_id].discard(lock_name)

    def check_circular_wait(self) -> bool:
        with self.lock:
            multi_lock_threads = [tid for tid, locks in self.locks_held.items() if len(locks) > 1]
            return len(multi_lock_threads) > 1

    def get_held_locks(self) -> dict[int, set[str]]:
        with self.lock:
            return {tid: locks.copy() for tid, locks in self.locks_held.items()}


class ThreadExceptionHandler:
    """Capture exceptions raised from worker threads."""

    def __init__(self) -> None:
        self.exceptions: list[dict[str, Any]] = []
        self.lock = threading.Lock()

    def handle(self, func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                with self.lock:
                    self.exceptions.append(
                        {
                            "thread": threading.current_thread().name,
                            "exception": exc,
                            "time": time.time(),
                        }
                    )
                raise

        return wrapper

    def get_exceptions(self) -> list[dict[str, Any]]:
        with self.lock:
            return self.exceptions.copy()

    def assert_no_exceptions(self) -> None:
        with self.lock:
            if self.exceptions:
                raise AssertionError(f"Exceptions captured: {self.exceptions}")


@pytest.fixture
def concurrent_executor() -> ConcurrentExecutor:
    """Helper for executing functions concurrently in tests."""

    return ConcurrentExecutor()


@pytest.fixture
def thread_synchronizer() -> ThreadSynchronizer:
    """Helper for synchronizing test threads."""

    return ThreadSynchronizer()


@pytest.fixture
def deadlock_detector() -> DeadlockDetector:
    """Helper for detecting potential deadlocks in tests."""

    return DeadlockDetector()


@pytest.fixture
def thread_exception_handler() -> ThreadExceptionHandler:
    """Capture exceptions from threads for testing."""

    return ThreadExceptionHandler()


__all__ = [
    "concurrent_executor",
    "deadlock_detector",
    "thread_exception_handler",
    "thread_synchronizer",
]

# 🧪✅🔚
