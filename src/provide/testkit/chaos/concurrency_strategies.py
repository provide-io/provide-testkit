"""Concurrency and parallelism chaos strategies.

Provides Hypothesis strategies for generating concurrent execution patterns,
race conditions, deadlock scenarios, and threading/async edge cases.
"""

from __future__ import annotations

from typing import Any

from hypothesis import strategies as st
from hypothesis.strategies import DrawFn, composite


@composite
def thread_counts(
    draw: DrawFn,
    min_threads: int = 1,
    max_threads: int = 100,
    include_extremes: bool = True,
) -> int:
    """Generate thread count scenarios for concurrency testing.

    Args:
        draw: Hypothesis draw function
        min_threads: Minimum number of threads
        max_threads: Maximum number of threads
        include_extremes: Include edge cases (1 thread, max threads)

    Returns:
        Number of threads to spawn

    Example:
        ```python
        @given(num_threads=thread_counts())
        def test_concurrent_access(num_threads):
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                # Test concurrent operations
                pass
        ```
    """
    if include_extremes:
        return draw(
            st.one_of(
                st.just(1), st.just(max_threads), st.integers(min_value=min_threads, max_value=max_threads)
            )
        )
    return draw(st.integers(min_value=min_threads, max_value=max_threads))


@composite
def race_condition_triggers(
    draw: DrawFn,
    num_operations: int = 10,
    max_delay: float = 0.1,
) -> list[tuple[int, float]]:
    """Generate timing patterns designed to trigger race conditions.

    Returns operation timings that maximize the chance of exposing race conditions.

    Args:
        draw: Hypothesis draw function
        num_operations: Number of concurrent operations
        max_delay: Maximum delay between operations in seconds

    Returns:
        List of (operation_id, delay_before_execution) tuples

    Example:
        ```python
        @given(timings=race_condition_triggers())
        async def test_race_condition(timings):
            tasks = []
            for op_id, delay in timings:
                await asyncio.sleep(delay)
                tasks.append(asyncio.create_task(operation(op_id)))
            await asyncio.gather(*tasks)
        ```
    """
    return [
        (
            i,
            draw(st.floats(min_value=0.0, max_value=max_delay, allow_nan=False, allow_infinity=False)),
        )
        for i in range(num_operations)
    ]


@composite
def deadlock_scenarios(
    draw: DrawFn,
    num_resources: int = 5,
) -> dict[str, Any]:
    """Generate resource lock patterns that may cause deadlocks.

    Creates scenarios where circular dependencies between locks might occur.

    Args:
        draw: Hypothesis draw function
        num_resources: Number of lockable resources

    Returns:
        Dictionary containing deadlock scenario configuration

    Example:
        ```python
        @given(scenario=deadlock_scenarios())
        def test_deadlock_prevention(scenario):
            # Attempt to acquire locks in the pattern
            # System should prevent deadlock
            pass
        ```
    """
    num_threads = draw(st.integers(min_value=2, max_value=10))

    # Each thread gets a sequence of resources to lock
    lock_sequences = []
    for _ in range(num_threads):
        num_locks = draw(st.integers(min_value=1, max_value=num_resources))
        # Generate a permutation of resource IDs
        sequence = draw(
            st.lists(
                st.integers(min_value=0, max_value=num_resources - 1),
                min_size=num_locks,
                max_size=num_locks,
                unique=True,
            )
        )
        lock_sequences.append(sequence)

    return {
        "num_resources": num_resources,
        "num_threads": num_threads,
        "lock_sequences": lock_sequences,
        "has_timeout": draw(st.booleans()),
        "timeout": draw(st.floats(min_value=0.1, max_value=5.0)) if draw(st.booleans()) else None,
    }


@composite
def async_event_patterns(
    draw: DrawFn,
    max_events: int = 50,
) -> list[dict[str, Any]]:
    """Generate async event patterns for coroutine testing.

    Creates patterns of async events, delays, and scheduling scenarios.

    Args:
        draw: Hypothesis draw function
        max_events: Maximum number of events to generate

    Returns:
        List of event dictionaries

    Example:
        ```python
        @given(events=async_event_patterns())
        async def test_async_handling(events):
            for event in events:
                if event['type'] == 'delay':
                    await asyncio.sleep(event['duration'])
                elif event['type'] == 'task':
                    await asyncio.create_task(event['coro']())
        ```
    """
    num_events = draw(st.integers(min_value=1, max_value=max_events))

    events = []
    for _ in range(num_events):
        event_type = draw(st.sampled_from(["delay", "immediate", "cancel", "timeout"]))

        event: dict[str, Any] = {"type": event_type}

        if event_type == "delay":
            event["duration"] = draw(st.floats(min_value=0.0, max_value=1.0))
        elif event_type == "timeout":
            event["timeout"] = draw(st.floats(min_value=0.01, max_value=2.0))
        elif event_type == "cancel":
            event["after_delay"] = draw(st.floats(min_value=0.0, max_value=0.5))

        events.append(event)

    return events


@composite
def lock_contention_patterns(
    draw: DrawFn,
    num_locks: int = 5,
    num_operations: int = 20,
) -> dict[str, Any]:
    """Generate lock contention patterns for testing synchronization.

    Creates scenarios with varying levels of lock contention.

    Args:
        draw: Hypothesis draw function
        num_locks: Number of available locks
        num_operations: Number of operations competing for locks

    Returns:
        Dictionary containing lock contention configuration

    Example:
        ```python
        @given(pattern=lock_contention_patterns())
        async def test_lock_contention(pattern):
            locks = [asyncio.Lock() for _ in range(pattern['num_locks'])]
            # Execute operations with varying contention
            pass
        ```
    """
    # Generate lock access patterns
    operations: list[dict[str, Any]] = []
    for _ in range(num_operations):
        # Which lock(s) does this operation need?
        num_locks_needed = draw(st.integers(min_value=1, max_value=min(3, num_locks)))
        locks_needed = draw(
            st.lists(
                st.integers(min_value=0, max_value=num_locks - 1),
                min_size=num_locks_needed,
                max_size=num_locks_needed,
                unique=True,
            )
        )

        # How long to hold the lock?
        hold_duration = draw(st.floats(min_value=0.001, max_value=0.5))

        operations.append(
            {
                "locks_needed": sorted(locks_needed),  # Always acquire in order to prevent deadlock
                "hold_duration": hold_duration,
                "operation_id": len(operations),
            }
        )

    return {
        "num_locks": num_locks,
        "operations": operations,
        "concurrent_workers": draw(st.integers(min_value=2, max_value=20)),
    }


@composite
def task_cancellation_patterns(
    draw: DrawFn,
    num_tasks: int = 20,
) -> list[dict[str, Any]]:
    """Generate task cancellation scenarios for async testing.

    Creates patterns of task creation and cancellation to test cleanup.

    Args:
        draw: Hypothesis draw function
        num_tasks: Number of tasks in the pattern

    Returns:
        List of task configuration dictionaries

    Example:
        ```python
        @given(tasks=task_cancellation_patterns())
        async def test_task_cancellation(tasks):
            for task_config in tasks:
                task = asyncio.create_task(long_running())
                if task_config['should_cancel']:
                    await asyncio.sleep(task_config['cancel_after'])
                    task.cancel()
        ```
    """
    tasks = []
    for i in range(num_tasks):
        should_cancel = draw(st.booleans())

        config: dict[str, Any] = {
            "task_id": i,
            "should_cancel": should_cancel,
        }

        if should_cancel:
            config["cancel_after"] = draw(st.floats(min_value=0.0, max_value=1.0))
            config["expect_cancellation_error"] = draw(st.booleans())
        else:
            config["expected_duration"] = draw(st.floats(min_value=0.1, max_value=2.0))

        tasks.append(config)

    return tasks


@composite
def process_pool_patterns(
    draw: DrawFn,
    max_workers: int = 10,
    max_tasks: int = 100,
) -> dict[str, Any]:
    """Generate process pool execution patterns.

    Creates scenarios for testing process pool behavior under various conditions.

    Args:
        draw: Hypothesis draw function
        max_workers: Maximum number of worker processes
        max_tasks: Maximum number of tasks to submit

    Returns:
        Dictionary containing pool configuration

    Example:
        ```python
        @given(config=process_pool_patterns())
        def test_process_pool(config):
            with ProcessPoolExecutor(max_workers=config['workers']) as pool:
                futures = [pool.submit(task) for task in config['tasks']]
        ```
    """
    num_workers = draw(st.integers(min_value=1, max_value=max_workers))
    num_tasks = draw(st.integers(min_value=1, max_value=max_tasks))

    task_patterns = draw(
        st.sampled_from(
            [
                "uniform",  # All tasks similar duration
                "mixed",  # Mix of fast and slow
                "bursty",  # Some tasks much slower
            ]
        )
    )

    return {
        "workers": num_workers,
        "num_tasks": num_tasks,
        "task_pattern": task_patterns,
        "timeout": draw(st.one_of(st.none(), st.floats(min_value=1.0, max_value=30.0))),
        "max_tasks_per_child": draw(st.one_of(st.none(), st.integers(min_value=1, max_value=50))),
    }


@composite
def pid_recycling_scenarios(
    draw: DrawFn,
) -> dict[str, Any]:
    """Generate PID recycling attack scenarios.

    Creates scenarios where PIDs might be reused, testing protection mechanisms.

    Args:
        draw: Hypothesis draw function

    Returns:
        Dictionary containing PID recycling scenario

    Example:
        ```python
        @given(scenario=pid_recycling_scenarios())
        def test_pid_recycling_protection(scenario):
            # Test that system detects recycled PIDs correctly
            pass
        ```
    """
    # Simulate a PID that gets recycled
    original_pid = draw(st.integers(min_value=1, max_value=65535))
    recycled_pid = original_pid  # Same PID, different process

    # Process start times (seconds since epoch)
    original_start_time = draw(st.floats(min_value=1000000000, max_value=2000000000))

    # Recycled process starts after original
    time_gap = draw(st.floats(min_value=0.1, max_value=3600.0))
    recycled_start_time = original_start_time + time_gap

    # Tolerance for time comparison
    time_tolerance = draw(st.floats(min_value=0.0, max_value=2.0))

    return {
        "original_pid": original_pid,
        "recycled_pid": recycled_pid,
        "original_start_time": original_start_time,
        "recycled_start_time": recycled_start_time,
        "time_tolerance": time_tolerance,
        "should_detect_recycling": abs(recycled_start_time - original_start_time) > time_tolerance,
    }


__all__ = [
    "async_event_patterns",
    "deadlock_scenarios",
    "lock_contention_patterns",
    "pid_recycling_scenarios",
    "process_pool_patterns",
    "race_condition_triggers",
    "task_cancellation_patterns",
    "thread_counts",
]
