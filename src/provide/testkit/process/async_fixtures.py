#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Async-specific test fixtures for process testing.

Provides fixtures for testing async operations, event loops, and
async context management across the provide-io ecosystem."""

from __future__ import annotations

import asyncio
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    Awaitable,
    Callable,
    Coroutine,
    Generator,
    Sequence,
)
from types import TracebackType
from typing import Any, Generic, TypeVar

import pytest
try:
    import pytest_asyncio
except ImportError:  # pragma: no cover - pytest-asyncio is a test dependency
    pytest_asyncio = None

from provide.testkit.mocking import AsyncMock

T = TypeVar("T")
StageFunc = Callable[[Any], Awaitable[Any] | Any]


class _AsyncIterator(Generic[T]):
    """Simple async iterator over a sequence of values."""

    def __init__(self, values: Sequence[T]) -> None:
        self._values = list(values)
        self._index = 0

    def __aiter__(self) -> _AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        if self._index >= len(self._values):
            raise StopAsyncIteration
        value = self._values[self._index]
        self._index += 1
        return value


class AsyncTaskGroup:
    """Track asyncio tasks and guarantee cleanup."""

    def __init__(self) -> None:
        self.tasks: list[asyncio.Task[Any]] = []

    def create_task(self, coro: Coroutine[Any, Any, T]) -> asyncio.Task[T]:
        """Create and track a task."""
        task = asyncio.create_task(coro)
        self.tasks.append(task)
        return task

    async def wait_all(self, timeout: float | None = None) -> list[Any]:
        """Wait for all tracked tasks to finish."""
        if not self.tasks:
            return []

        done, pending = await asyncio.wait(
            self.tasks,
            timeout=timeout,
            return_when=asyncio.ALL_COMPLETED,
        )

        for task in pending:
            task.cancel()

        results: list[Any] = []
        for task in done:
            try:
                results.append(task.result())
            except Exception as exc:
                results.append(exc)

        return results

    async def cancel_all(self) -> None:
        """Cancel all running tasks."""
        for task in self.tasks:
            if not task.done():
                task.cancel()

        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

    async def __aenter__(self) -> AsyncTaskGroup:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.cancel_all()


class AsyncPipeline:
    """Pipeline helper for chaining async processing stages."""

    def __init__(self) -> None:
        self.stages: list[StageFunc] = []
        self.results: list[Any] = []

    def add_stage(self, func: StageFunc) -> AsyncPipeline:
        """Register a pipeline stage."""
        self.stages.append(func)
        return self

    async def process(self, data: Any) -> Any:
        """Process a single item through all stages."""
        result = data
        for stage in self.stages:
            if asyncio.iscoroutinefunction(stage):
                result = await stage(result)  # type: ignore[arg-type]
            else:
                result = stage(result)
            self.results.append(result)
        return result

    async def process_batch(self, items: Sequence[Any]) -> list[Any]:
        """Process a batch of items."""
        tasks = [self.process(item) for item in items]
        return list(await asyncio.gather(*tasks))

    def clear(self) -> None:
        """Reset stages and stored results."""
        self.stages.clear()
        self.results.clear()


class AsyncRateLimiter:
    """Co-operative async rate limiter."""

    def __init__(self, rate: int = 10, per: float = 1.0) -> None:
        self.rate = rate
        self.per = per
        self.allowance = float(rate)
        self.last_check = asyncio.get_event_loop().time()

    async def acquire(self) -> None:
        """Acquire permission to continue, respecting rate limits."""
        current = asyncio.get_event_loop().time()
        time_passed = current - self.last_check
        self.last_check = current

        self.allowance += time_passed * (self.rate / self.per)
        if self.allowance > self.rate:
            self.allowance = float(self.rate)

        if self.allowance < 1.0:
            sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
            await asyncio.sleep(sleep_time)
            self.allowance = 0.0
        else:
            self.allowance -= 1.0

    async def __aenter__(self) -> AsyncRateLimiter:
        await self.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


_async_fixture = pytest_asyncio.fixture if pytest_asyncio else pytest.fixture


@_async_fixture
async def clean_event_loop() -> AsyncGenerator[None, None]:
    """
    Ensure clean event loop for async tests.

    Cancels all pending tasks after the test to prevent event loop issues.

    Yields:
        None - fixture for test setup/teardown.
    """
    yield

    # Clean up any pending tasks
    loop = asyncio.get_running_loop()
    current_task = asyncio.current_task()
    pending = asyncio.all_tasks()

    # Break potential task child cycles before cancellation to avoid recursion errors.
    for task in pending:
        children = getattr(task, "_children", None)
        if children is not None and hasattr(children, "clear"):
            children.clear()

    def _is_safe_to_cancel(task: asyncio.Task[object]) -> bool:
        children = getattr(task, "_children", None)
        if children:
            return False
        return task is not current_task and not task.done()

    # Exclude the current task and any task with children to avoid recursive cancellation.
    tasks_to_cancel = [t for t in pending if _is_safe_to_cancel(t)]

    for task in tasks_to_cancel:
        task.cancel()

    # Wait for all tasks to complete cancellation
    if tasks_to_cancel:
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)


@pytest.fixture
def async_timeout() -> Callable[[Awaitable[T], float], Awaitable[T]]:
    """
    Provide configurable timeout wrapper for async operations.

    Returns:
        A function that wraps async operations with a timeout.
    """

    def _timeout_wrapper(coro: Awaitable[T], seconds: float = 5.0) -> Awaitable[T]:
        """
        Wrap a coroutine with a timeout.

        Args:
            coro: Coroutine to wrap
            seconds: Timeout in seconds

        Returns:
            Result of the coroutine or raises asyncio.TimeoutError
        """
        return asyncio.wait_for(coro, timeout=seconds)

    return _timeout_wrapper


@pytest.fixture
def event_loop_policy() -> Generator[asyncio.AbstractEventLoopPolicy, None, None]:
    """
    Set event loop policy for tests to avoid conflicts.

    Returns:
        New event loop policy for isolated testing.
    """
    policy = asyncio.get_event_loop_policy()
    new_policy = asyncio.DefaultEventLoopPolicy()
    asyncio.set_event_loop_policy(new_policy)

    yield new_policy

    # Restore original policy
    asyncio.set_event_loop_policy(policy)


@pytest.fixture
async def async_context_manager() -> Callable[[Any | None, Any | None], AsyncMock]:
    """
    Factory for creating mock async context managers.

    Returns:
        Function that creates configured async context manager mocks.
    """

    def _create_async_cm(enter_value: Any | None = None, exit_value: Any | None = None) -> AsyncMock:
        """
        Create a mock async context manager.

        Args:
            enter_value: Value to return from __aenter__
            exit_value: Value to return from __aexit__

        Returns:
            AsyncMock configured as context manager
        """
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=enter_value)
        mock_cm.__aexit__ = AsyncMock(return_value=exit_value)
        return mock_cm

    return _create_async_cm


@pytest.fixture
async def async_iterator() -> Callable[[Sequence[T]], AsyncIterable[T]]:
    """
    Factory for creating mock async iterators.

    Returns:
        Function that creates async iterator mocks with specified values.
    """

    def _create_async_iter(values: Sequence[T]) -> AsyncIterable[T]:
        """
        Create a mock async iterator.

        Args:
            values: List of values to yield

        Returns:
            Async iterator that yields the specified values
        """
        return _AsyncIterator(values)

    return _create_async_iter


@pytest.fixture
def async_queue() -> asyncio.Queue[Any]:
    """
    Create an async queue for testing producer/consumer patterns.

    Returns:
        asyncio.Queue instance for testing.
    """
    return asyncio.Queue()


@pytest.fixture
async def async_lock() -> asyncio.Lock:
    """
    Create an async lock for testing synchronization.

    Returns:
        asyncio.Lock instance for testing.
    """
    return asyncio.Lock()


# mock_async_sleep removed - use mock_asyncio_sleep from provide.testkit.mocking.time instead


@pytest.fixture
def async_gather_helper() -> Callable[..., Awaitable[list[Any]]]:
    """
    Helper for testing asyncio.gather operations.

    Returns:
        Function to gather async results with error handling.
    """

    async def _gather(*coroutines: Awaitable[Any], return_exceptions: bool = False) -> list[Any]:
        """
        Gather results from multiple coroutines.

        Args:
            *coroutines: Coroutines to gather
            return_exceptions: Whether to return exceptions as results

        Returns:
            List of results from coroutines
        """
        return await asyncio.gather(*coroutines, return_exceptions=return_exceptions)

    return _gather


@pytest.fixture
def async_task_group() -> AsyncTaskGroup:
    """
    Manage a group of async tasks with cleanup.

    Returns:
        AsyncTaskGroup instance for managing tasks.
    """

    return AsyncTaskGroup()


@pytest.fixture
def async_condition_waiter() -> Callable[[Callable[[], bool], float, float], Awaitable[bool]]:
    """
    Helper for waiting on async conditions in tests.

    Returns:
        Function to wait for conditions with timeout.
    """

    async def _wait_for(condition: Callable[[], bool], timeout: float = 5.0, interval: float = 0.1) -> bool:
        """
        Wait for a condition to become true.

        Args:
            condition: Function that returns True when condition is met
            timeout: Maximum wait time
            interval: Check interval

        Returns:
            True if condition met, False if timeout
        """
        start = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start < timeout:
            if condition():
                return True
            await asyncio.sleep(interval)

        return False

    return _wait_for


@pytest.fixture
def async_pipeline() -> AsyncPipeline:
    """
    Create an async pipeline for testing data flow.

    Returns:
        AsyncPipeline instance for chaining async operations.
    """

    return AsyncPipeline()


@pytest.fixture
def async_rate_limiter() -> AsyncRateLimiter:
    """
    Create an async rate limiter for testing.

    Returns:
        AsyncRateLimiter instance for controlling request rates.
    """

    return AsyncRateLimiter()


__all__ = [
    "async_condition_waiter",
    "async_context_manager",
    "async_gather_helper",
    "async_iterator",
    "async_lock",
    "async_pipeline",
    "async_queue",
    "async_rate_limiter",
    "async_task_group",
    "async_timeout",
    "clean_event_loop",
    "event_loop_policy",
]

# 🧪✅🔚
