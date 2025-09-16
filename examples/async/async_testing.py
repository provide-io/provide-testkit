#!/usr/bin/env python3
"""
Example: Async/Await Testing Patterns

This example demonstrates testing asynchronous operations, event loops,
and concurrent code using provide-testkit's async utilities.

Key fixtures used:
- clean_event_loop: Fresh event loop for each test
- async_timeout: Timeout context for async operations
- async_context_manager: Lifecycle management for async resources

Learning objectives:
- Test async functions and coroutines
- Handle async context managers
- Test concurrent operations
- Manage event loop lifecycle
- Handle timeouts and cancellation
"""

import asyncio
from typing import Any

import pytest

from provide.testkit import async_timeout


@pytest.mark.asyncio
async def test_basic_async_operation(clean_event_loop):
    """Test basic async function execution."""

    async def fetch_data(delay: float = 0.1) -> str:
        """Simulate async data fetching."""
        await asyncio.sleep(delay)
        return "data_fetched"

    # Act: Execute async operation
    result = await fetch_data()

    # Assert: Verify result
    assert result == "data_fetched"


@pytest.mark.asyncio
async def test_async_with_timeout(async_timeout):
    """Test async operations with timeout control."""

    async def slow_operation() -> str:
        """Simulate slow async operation."""
        await asyncio.sleep(0.5)
        return "completed"

    # Act & Assert: Operation should complete within timeout
    async with async_timeout(1.0):
        result = await slow_operation()
        assert result == "completed"


@pytest.mark.asyncio
async def test_async_timeout_failure():
    """Test timeout failure handling."""

    async def very_slow_operation() -> str:
        """Simulate very slow operation that should timeout."""
        await asyncio.sleep(2.0)
        return "never_reached"

    # Act & Assert: Operation should timeout
    with pytest.raises(asyncio.TimeoutError):
        async with async_timeout(0.1):
            await very_slow_operation()


@pytest.mark.asyncio
async def test_concurrent_operations(clean_event_loop):
    """Test multiple concurrent async operations."""

    async def process_item(item_id: int, delay: float = 0.1) -> dict[str, Any]:
        """Process an item asynchronously."""
        await asyncio.sleep(delay)
        return {"id": item_id, "status": "processed", "timestamp": asyncio.get_event_loop().time()}

    # Act: Run multiple operations concurrently
    tasks = [process_item(i) for i in range(5)]
    results = await asyncio.gather(*tasks)

    # Assert: All operations completed
    assert len(results) == 5
    for i, result in enumerate(results):
        assert result["id"] == i
        assert result["status"] == "processed"
        assert "timestamp" in result


@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context managers."""

    class AsyncResource:
        def __init__(self, name: str):
            self.name = name
            self.is_open = False
            self.data: list[str] = []

        async def __aenter__(self):
            # Simulate async initialization
            await asyncio.sleep(0.01)
            self.is_open = True
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            # Simulate async cleanup
            await asyncio.sleep(0.01)
            self.is_open = False

        async def add_data(self, item: str):
            if not self.is_open:
                raise RuntimeError("Resource not open")
            await asyncio.sleep(0.01)
            self.data.append(item)

    # Act: Use async context manager
    async with AsyncResource("test_resource") as resource:
        assert resource.is_open
        await resource.add_data("item1")
        await resource.add_data("item2")

    # Assert: Resource was properly cleaned up
    assert not resource.is_open
    assert resource.data == ["item1", "item2"]


@pytest.mark.asyncio
async def test_async_exception_handling():
    """Test exception handling in async operations."""

    async def failing_operation(should_fail: bool = True) -> str:
        """Operation that can fail."""
        await asyncio.sleep(0.01)
        if should_fail:
            raise ValueError("Operation failed")
        return "success"

    # Test successful case
    result = await failing_operation(should_fail=False)
    assert result == "success"

    # Test failure case
    with pytest.raises(ValueError, match="Operation failed"):
        await failing_operation(should_fail=True)


@pytest.mark.asyncio
async def test_async_generator():
    """Test async generators and iteration."""

    async def async_number_generator(count: int):
        """Generate numbers asynchronously."""
        for i in range(count):
            await asyncio.sleep(0.01)  # Simulate async work
            yield i

    # Act: Collect results from async generator
    results = []
    async for number in async_number_generator(5):
        results.append(number)

    # Assert: All numbers generated
    assert results == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_async_queue_operations():
    """Test async queue operations."""

    async def producer(queue: asyncio.Queue, items: list[str]):
        """Produce items into the queue."""
        for item in items:
            await asyncio.sleep(0.01)
            await queue.put(item)
        await queue.put(None)  # Sentinel to signal completion

    async def consumer(queue: asyncio.Queue) -> list[str]:
        """Consume items from the queue."""
        results = []
        while True:
            item = await queue.get()
            if item is None:
                break
            results.append(item)
            queue.task_done()
        return results

    # Act: Set up producer-consumer pattern
    queue: asyncio.Queue = asyncio.Queue()
    items = ["apple", "banana", "cherry"]

    # Start producer and consumer concurrently
    producer_task = asyncio.create_task(producer(queue, items))
    consumer_task = asyncio.create_task(consumer(queue))

    # Wait for completion
    await producer_task
    results = await consumer_task

    # Assert: All items processed
    assert results == items


@pytest.mark.asyncio
async def test_async_lock_and_synchronization():
    """Test async locks and synchronization."""

    shared_resource = {"counter": 0}
    lock = asyncio.Lock()

    async def increment_counter(worker_id: int, increments: int):
        """Increment shared counter with proper locking."""
        for _ in range(increments):
            async with lock:
                # Critical section
                current = shared_resource["counter"]
                await asyncio.sleep(0.001)  # Simulate work that could cause race condition
                shared_resource["counter"] = current + 1

    # Act: Run multiple workers concurrently
    workers = [increment_counter(worker_id=i, increments=10) for i in range(3)]
    await asyncio.gather(*workers)

    # Assert: Counter incremented correctly (no race conditions)
    assert shared_resource["counter"] == 30


@pytest.mark.asyncio
async def test_async_event_coordination():
    """Test coordination between async tasks using events."""

    results = {"task1": None, "task2": None}
    start_event = asyncio.Event()
    task1_done = asyncio.Event()

    async def task1():
        """First task that signals when complete."""
        await start_event.wait()
        await asyncio.sleep(0.1)
        results["task1"] = "task1_complete"
        task1_done.set()

    async def task2():
        """Second task that waits for first task."""
        await start_event.wait()
        await task1_done.wait()  # Wait for task1 to complete
        results["task2"] = "task2_complete"

    # Act: Start tasks and coordinate execution
    t1 = asyncio.create_task(task1())
    t2 = asyncio.create_task(task2())

    # Signal tasks to start
    start_event.set()

    # Wait for completion
    await asyncio.gather(t1, t2)

    # Assert: Tasks completed in correct order
    assert results["task1"] == "task1_complete"
    assert results["task2"] == "task2_complete"


if __name__ == "__main__":
    # Run examples directly for demonstration
    print("🔄 Async Testing Examples")
    print("=" * 50)

    async def demo_async_operation():
        """Demonstrate basic async operation."""
        print("⏳ Starting async operation...")
        await asyncio.sleep(0.1)
        print("✅ Async operation completed!")
        return "demo_result"

    async def demo_concurrent_tasks():
        """Demonstrate concurrent task execution."""
        print("🔀 Starting concurrent tasks...")

        async def worker(worker_id: int):
            await asyncio.sleep(0.1)
            return f"Worker {worker_id} done"

        tasks = [worker(i) for i in range(3)]
        results = await asyncio.gather(*tasks)

        for result in results:
            print(f"   ✅ {result}")

    async def main():
        """Run all demonstrations."""
        await demo_async_operation()
        await demo_concurrent_tasks()
        print("\n🎉 Async examples completed!")
        print("Run with pytest to see fixtures in action:")
        print("   pytest examples/async_testing.py -v")

    # Run the demo
    asyncio.run(main())
