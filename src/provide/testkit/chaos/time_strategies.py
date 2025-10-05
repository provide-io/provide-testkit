"""Time-based chaos strategies for testing temporal behavior.

Provides Hypothesis strategies for generating chaotic time patterns, clock skew,
timeout scenarios, and timing-related edge cases.
"""

from __future__ import annotations

from typing import Any

from hypothesis import strategies as st
from hypothesis.strategies import DrawFn, composite


@composite
def time_advances(
    draw: DrawFn,
    min_advance: float = 0.0,
    max_advance: float = 3600.0,
    allow_backwards: bool = False,
) -> float:
    """Generate time progression patterns for time manipulation testing.

    Args:
        draw: Hypothesis draw function
        min_advance: Minimum time advance in seconds
        max_advance: Maximum time advance in seconds
        allow_backwards: Allow negative time advances (backwards jumps)

    Returns:
        Time advance value in seconds (can be negative if allowed)

    Example:
        ```python
        @given(advance=time_advances(allow_backwards=True))
        def test_with_time_jump(advance, chaos_time_source):
            chaos_time_source.advance(advance)
            # Test behavior after time jump
        ```
    """
    if allow_backwards:
        return draw(
            st.floats(min_value=-max_advance, max_value=max_advance, allow_nan=False, allow_infinity=False)
        )
    return draw(st.floats(min_value=min_advance, max_value=max_advance, allow_nan=False, allow_infinity=False))


@composite
def clock_skew(
    draw: DrawFn,
    max_skew: float = 300.0,
) -> dict[str, Any]:
    """Generate clock skew scenarios for distributed system testing.

    Simulates clock drift, NTP sync issues, and timezone problems.

    Args:
        draw: Hypothesis draw function
        max_skew: Maximum clock skew in seconds

    Returns:
        Dictionary containing skew configuration

    Example:
        ```python
        @given(skew=clock_skew())
        def test_with_clock_skew(skew):
            # Simulate clock skew between components
            pass
        ```
    """
    return {
        "skew_seconds": draw(st.floats(min_value=-max_skew, max_value=max_skew)),
        "drift_rate": draw(st.floats(min_value=0.0001, max_value=0.01)),  # seconds per second
        "has_backwards_jump": draw(st.booleans()),
        "sync_interval": draw(st.floats(min_value=1.0, max_value=3600.0)),
    }


@composite
def timeout_patterns(  # type: ignore[misc]
    draw: DrawFn,
    min_timeout: float = 0.01,
    max_timeout: float = 60.0,
    include_none: bool = True,
) -> float | None:
    """Generate realistic timeout scenarios.

    Args:
        draw: Hypothesis draw function
        min_timeout: Minimum timeout value in seconds
        max_timeout: Maximum timeout value in seconds
        include_none: Whether to include None (no timeout) as a possibility

    Returns:
        Timeout value in seconds, or None

    Example:
        ```python
        @given(timeout=timeout_patterns())
        async def test_operation_timeout(timeout):
            await asyncio.wait_for(operation(), timeout=timeout)
        ```
    """
    strategies = [
        st.floats(min_value=min_timeout, max_value=max_timeout, allow_nan=False, allow_infinity=False),
        # Edge case: very short timeouts
        st.floats(min_value=0.001, max_value=0.01),
    ]

    if include_none:
        strategies.append(st.just(None))

    return draw(st.one_of(*strategies))


@composite
def rate_burst_patterns(
    draw: DrawFn,
    max_burst_size: int = 1000,
    max_duration: float = 10.0,
) -> list[tuple[float, int]]:
    """Generate traffic burst patterns for rate limiting tests.

    Returns a list of (timestamp, request_count) representing burst patterns.

    Args:
        draw: Hypothesis draw function
        max_burst_size: Maximum number of requests in a burst
        max_duration: Maximum duration of burst pattern in seconds

    Returns:
        List of (time_offset, request_count) tuples

    Example:
        ```python
        @given(bursts=rate_burst_patterns())
        async def test_rate_limiter(bursts):
            for time_offset, count in bursts:
                await asyncio.sleep(time_offset)
                for _ in range(count):
                    await rate_limited_operation()
        ```
    """
    num_bursts = draw(st.integers(min_value=1, max_value=20))
    bursts = []

    current_time = 0.0
    for _ in range(num_bursts):
        # Time between bursts
        time_offset = draw(st.floats(min_value=0.0, max_value=max_duration / num_bursts))
        current_time += time_offset

        # Burst size
        burst_size = draw(st.integers(min_value=1, max_value=max_burst_size))

        bursts.append((current_time, burst_size))

    return bursts


@composite
def jitter_patterns(
    draw: DrawFn,
    base_interval: float = 1.0,
    max_jitter_percent: float = 50.0,
) -> list[float]:
    """Generate network-like timing jitter patterns.

    Simulates variable latency and timing uncertainty.

    Args:
        draw: Hypothesis draw function
        base_interval: Base time interval in seconds
        max_jitter_percent: Maximum jitter as percentage of base interval

    Returns:
        List of intervals with jitter applied

    Example:
        ```python
        @given(intervals=jitter_patterns(base_interval=0.1))
        async def test_with_jitter(intervals):
            for interval in intervals:
                await asyncio.sleep(interval)
                await send_packet()
        ```
    """
    num_intervals = draw(st.integers(min_value=1, max_value=100))
    jitter_range = base_interval * (max_jitter_percent / 100.0)

    return [
        base_interval + draw(st.floats(min_value=-jitter_range, max_value=jitter_range))
        for _ in range(num_intervals)
    ]


@composite
def deadline_scenarios(
    draw: DrawFn,
    min_deadline: float = 0.1,
    max_deadline: float = 10.0,
) -> dict[str, Any]:
    """Generate deadline-based test scenarios.

    Creates scenarios with operations that may or may not meet their deadlines.

    Args:
        draw: Hypothesis draw function
        min_deadline: Minimum deadline in seconds
        max_deadline: Maximum deadline in seconds

    Returns:
        Dictionary containing deadline scenario configuration

    Example:
        ```python
        @given(scenario=deadline_scenarios())
        async def test_deadline_handling(scenario):
            deadline = scenario['deadline']
            work_duration = scenario['work_duration']
            # Test if deadline handling works correctly
        ```
    """
    deadline = draw(st.floats(min_value=min_deadline, max_value=max_deadline))

    # Generate work duration that may exceed deadline
    exceeds_deadline = draw(st.booleans())
    if exceeds_deadline:
        work_duration = draw(st.floats(min_value=deadline, max_value=deadline * 2))
    else:
        work_duration = draw(st.floats(min_value=0.0, max_value=deadline * 0.9))

    return {
        "deadline": deadline,
        "work_duration": work_duration,
        "exceeds_deadline": exceeds_deadline,
        "grace_period": draw(st.floats(min_value=0.0, max_value=1.0)),
    }


@composite
def retry_backoff_patterns(
    draw: DrawFn,
    max_retries: int = 10,
) -> dict[str, Any]:
    """Generate retry and backoff patterns for resilience testing.

    Args:
        draw: Hypothesis draw function
        max_retries: Maximum number of retries

    Returns:
        Dictionary containing retry configuration

    Example:
        ```python
        @given(pattern=retry_backoff_patterns())
        def test_retry_logic(pattern):
            for attempt in range(pattern['max_attempts']):
                delay = pattern['backoff_strategy'](attempt)
                time.sleep(delay)
        ```
    """
    num_retries = draw(st.integers(min_value=1, max_value=max_retries))

    backoff_type = draw(st.sampled_from(["constant", "linear", "exponential", "jittered"]))

    config: dict[str, Any] = {
        "max_attempts": num_retries,
        "backoff_type": backoff_type,
    }

    if backoff_type == "constant":
        config["base_delay"] = draw(st.floats(min_value=0.01, max_value=5.0))
    elif backoff_type == "linear":
        config["base_delay"] = draw(st.floats(min_value=0.01, max_value=1.0))
        config["increment"] = draw(st.floats(min_value=0.1, max_value=2.0))
    elif backoff_type == "exponential":
        config["base_delay"] = draw(st.floats(min_value=0.01, max_value=1.0))
        config["multiplier"] = draw(st.floats(min_value=1.5, max_value=3.0))
        config["max_delay"] = draw(st.floats(min_value=10.0, max_value=60.0))
    elif backoff_type == "jittered":
        config["base_delay"] = draw(st.floats(min_value=0.01, max_value=1.0))
        config["multiplier"] = draw(st.floats(min_value=1.5, max_value=3.0))
        config["jitter_percent"] = draw(st.floats(min_value=0.0, max_value=50.0))

    return config


__all__ = [
    "clock_skew",
    "deadline_scenarios",
    "jitter_patterns",
    "rate_burst_patterns",
    "retry_backoff_patterns",
    "time_advances",
    "timeout_patterns",
]
