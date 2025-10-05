"""Core Hypothesis strategies for chaos testing.

Provides foundational strategies for generating chaotic test inputs that explore
edge cases, boundary conditions, and failure scenarios.
"""

from __future__ import annotations

import sys
from typing import Any

from hypothesis import strategies as st
from hypothesis.strategies import DrawFn, composite

# Common exception types for failure injection
COMMON_EXCEPTIONS: tuple[type[Exception], ...] = (
    ValueError,
    TypeError,
    RuntimeError,
    IOError,
    OSError,
    TimeoutError,
    ConnectionError,
    MemoryError,
)


@composite
def chaos_timings(
    draw: DrawFn,
    min_value: float = 0.001,
    max_value: float = 10.0,
    allow_zero: bool = False,
) -> float:
    """Generate chaotic timing values for unpredictable delays.

    Useful for testing timeout handling, race conditions, and time-sensitive code.

    Args:
        draw: Hypothesis draw function
        min_value: Minimum timing value in seconds
        max_value: Maximum timing value in seconds
        allow_zero: Whether to allow zero delay

    Returns:
        A floating-point timing value in seconds

    Example:
        ```python
        @given(delay=chaos_timings())
        async def test_with_delay(delay):
            await asyncio.sleep(delay)
        ```
    """
    min_val = 0.0 if allow_zero else min_value
    return draw(st.floats(min_value=min_val, max_value=max_value, allow_nan=False, allow_infinity=False))


@composite
def failure_patterns(
    draw: DrawFn,
    max_failures: int = 10,
    exception_types: tuple[type[Exception], ...] | None = None,
) -> list[tuple[int, type[Exception]]]:
    """Generate patterns of when and how failures should occur.

    Returns a list of (iteration_number, exception_type) tuples for failure injection.

    Args:
        draw: Hypothesis draw function
        max_failures: Maximum number of failures to generate
        exception_types: Specific exception types to use (defaults to common types)

    Returns:
        List of (when_to_fail, exception_class) tuples

    Example:
        ```python
        @given(failures=failure_patterns())
        def test_with_failures(failures):
            for i, result in enumerate(operations):
                if any(i == when and exc for when, exc in failures):
                    raise next(exc for when, exc in failures if when == i)
        ```
    """
    exc_types = exception_types or COMMON_EXCEPTIONS
    num_failures = draw(st.integers(min_value=0, max_value=max_failures))

    return [
        (
            draw(st.integers(min_value=0, max_value=100)),
            draw(st.sampled_from(exc_types)),
        )
        for _ in range(num_failures)
    ]


@composite
def malformed_inputs(  # type: ignore[misc]
    draw: DrawFn,
    include_huge: bool = True,
    include_empty: bool = True,
    include_special: bool = True,
) -> Any:
    """Generate edge-case inputs for robust testing.

    Creates various malformed, extreme, or unusual inputs that often expose bugs.

    Args:
        draw: Hypothesis draw function
        include_huge: Include very large strings/data
        include_empty: Include empty/None values
        include_special: Include special numeric values (NaN, inf)

    Returns:
        Various malformed input values

    Example:
        ```python
        @given(data=malformed_inputs())
        def test_parser(data):
            result = parse(data)  # Should handle gracefully
        ```
    """
    strategies = []

    # Text inputs
    strategies.append(st.text(min_size=0, max_size=1000))
    if include_huge:
        strategies.append(st.text(min_size=100000, max_size=1000000))

    # Binary inputs
    strategies.append(st.binary(min_size=0, max_size=1000))
    if include_huge:
        strategies.append(st.binary(min_size=100000, max_size=1000000))

    # Numeric inputs
    strategies.append(st.integers())
    strategies.append(st.floats(allow_nan=include_special, allow_infinity=include_special))

    # Empty/None values
    if include_empty:
        strategies.extend([st.just(None), st.just(""), st.just(b""), st.just([])])

    # Lists and dicts
    strategies.append(st.lists(st.integers(), min_size=0, max_size=100))
    strategies.append(st.dictionaries(st.text(), st.integers(), min_size=0, max_size=100))

    return draw(st.one_of(*strategies))


@composite
def unicode_chaos(  # type: ignore[misc]
    draw: DrawFn,
    include_emoji: bool = True,
    include_rtl: bool = True,
    include_zero_width: bool = True,
    include_surrogates: bool = False,
) -> str:
    """Generate problematic Unicode strings for testing.

    Creates strings with emoji, RTL text, zero-width characters, and other
    Unicode edge cases that often cause issues.

    Args:
        draw: Hypothesis draw function
        include_emoji: Include emoji characters
        include_rtl: Include right-to-left text
        include_zero_width: Include zero-width characters
        include_surrogates: Include surrogate pairs (can be problematic)

    Returns:
        A Unicode string with chaotic properties

    Example:
        ```python
        @given(text=unicode_chaos())
        def test_text_handling(text):
            result = process_text(text)
        ```
    """
    strategies = []

    # Basic Unicode text
    strategies.append(st.text(min_size=0, max_size=100))

    # Emoji ranges
    if include_emoji:
        # Emoticons and pictographs
        strategies.append(
            st.text(
                alphabet=st.characters(min_codepoint=0x1F300, max_codepoint=0x1F9FF),
                min_size=1,
                max_size=20,
            )
        )

    # RTL characters (Arabic, Hebrew)
    if include_rtl:
        strategies.append(
            st.text(
                alphabet=st.characters(min_codepoint=0x0590, max_codepoint=0x08FF),
                min_size=1,
                max_size=50,
            )
        )

    # Zero-width characters
    if include_zero_width:
        zero_width_chars = "\u200b\u200c\u200d\ufeff"  # ZWSP, ZWNJ, ZWJ, ZWNBSP
        strategies.append(st.text(alphabet=zero_width_chars, min_size=1, max_size=10))

    # Control characters
    strategies.append(st.text(alphabet=st.characters(max_codepoint=0x001F), min_size=1, max_size=10))

    # Combining characters
    strategies.append(
        st.text(alphabet=st.characters(min_codepoint=0x0300, max_codepoint=0x036F), min_size=1, max_size=20)
    )

    return draw(st.one_of(*strategies))


@composite
def resource_limits(
    draw: DrawFn,
    min_memory: int = 1024,
    max_memory: int = 1024 * 1024 * 100,  # 100MB
    min_timeout: float = 0.01,
    max_timeout: float = 60.0,
) -> dict[str, Any]:
    """Generate resource constraint scenarios.

    Creates various resource limit configurations for testing behavior under constraints.

    Args:
        draw: Hypothesis draw function
        min_memory: Minimum memory limit in bytes
        max_memory: Maximum memory limit in bytes
        min_timeout: Minimum timeout in seconds
        max_timeout: Maximum timeout in seconds

    Returns:
        Dictionary with resource limit configuration

    Example:
        ```python
        @given(limits=resource_limits())
        def test_with_limits(limits):
            with resource_limiter(limits['memory'], limits['timeout']):
                perform_operation()
        ```
    """
    return {
        "memory": draw(st.integers(min_value=min_memory, max_value=max_memory)),
        "timeout": draw(st.floats(min_value=min_timeout, max_value=max_timeout)),
        "cpu_count": draw(st.integers(min_value=1, max_value=64)),
        "max_threads": draw(st.integers(min_value=1, max_value=1000)),
        "max_open_files": draw(st.integers(min_value=10, max_value=10000)),
    }


@composite
def edge_values(  # type: ignore[misc]
    draw: DrawFn,
    value_type: type = int,
) -> Any:
    """Generate boundary and edge-case values for a given type.

    Args:
        draw: Hypothesis draw function
        value_type: Type to generate edge values for

    Returns:
        Edge-case value of the specified type

    Example:
        ```python
        @given(value=edge_values(value_type=int))
        def test_integer_handling(value):
            result = process_int(value)
        ```
    """
    if value_type is int:
        edges = [
            st.just(0),
            st.just(1),
            st.just(-1),
            st.just(sys.maxsize),
            st.just(-sys.maxsize - 1),
            st.just(2**31 - 1),  # INT32_MAX
            st.just(-(2**31)),  # INT32_MIN
            st.just(2**63 - 1),  # INT64_MAX
            st.just(-(2**63)),  # INT64_MIN
        ]
        return draw(st.one_of(*edges))

    elif value_type is float:
        edges = [
            st.just(0.0),
            st.just(-0.0),
            st.just(1.0),
            st.just(-1.0),
            st.just(float("inf")),
            st.just(float("-inf")),
            st.just(float("nan")),
            st.just(sys.float_info.min),
            st.just(sys.float_info.max),
            st.just(sys.float_info.epsilon),
        ]
        return draw(st.one_of(*edges))

    elif value_type is str:
        edges = [
            st.just(""),
            st.just(" "),
            st.just("\n"),
            st.just("\t"),
            st.just("\x00"),
            st.just("0"),
            st.just("-1"),
            st.just("null"),
            st.just("None"),
            st.just("undefined"),
        ]
        return draw(st.one_of(*edges))

    else:
        # Generic approach for other types
        return draw(st.from_type(value_type))


__all__ = [
    "chaos_timings",
    "edge_values",
    "failure_patterns",
    "malformed_inputs",
    "resource_limits",
    "unicode_chaos",
]
