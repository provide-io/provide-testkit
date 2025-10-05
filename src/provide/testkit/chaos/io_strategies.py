"""I/O and file system chaos strategies.

Provides Hypothesis strategies for generating file I/O failures, permission issues,
disk space problems, and network-related chaos scenarios.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hypothesis import strategies as st
from hypothesis.strategies import DrawFn, composite


@composite
def file_sizes(  # type: ignore[misc]
    draw: DrawFn,
    min_size: int = 0,
    max_size: int = 10 * 1024 * 1024,  # 10MB default
    include_huge: bool = False,
) -> int:
    """Generate realistic file size distributions.

    Args:
        draw: Hypothesis draw function
        min_size: Minimum file size in bytes
        max_size: Maximum file size in bytes
        include_huge: Include very large file sizes (GB range)

    Returns:
        File size in bytes

    Example:
        ```python
        @given(size=file_sizes())
        def test_file_handling(tmp_path, size):
            file_path = tmp_path / "test.dat"
            file_path.write_bytes(b"x" * size)
        ```
    """
    sizes = [
        st.just(0),  # Empty file
        st.integers(min_value=1, max_value=1024),  # Tiny files
        st.integers(min_value=1024, max_value=1024 * 1024),  # KB range
        st.integers(min_value=min_size, max_value=max_size),  # Normal range
    ]

    if include_huge:
        sizes.append(st.integers(min_value=100 * 1024 * 1024, max_value=1024 * 1024 * 1024))  # 100MB - 1GB

    return draw(st.one_of(*sizes))


@composite
def permission_patterns(
    draw: DrawFn,
) -> dict[str, Any]:
    """Generate file permission scenarios.

    Creates various permission configurations for testing access control.

    Args:
        draw: Hypothesis draw function

    Returns:
        Dictionary containing permission configuration

    Example:
        ```python
        @given(perms=permission_patterns())
        def test_file_permissions(tmp_path, perms):
            file_path = tmp_path / "test.txt"
            file_path.touch()
            os.chmod(file_path, perms['mode'])
        ```
    """
    # Common permission modes
    common_modes = [
        0o000,  # No permissions
        0o400,  # Read only (owner)
        0o600,  # Read/write (owner)
        0o644,  # Read/write (owner), read (others)
        0o755,  # All (owner), read/execute (others)
        0o777,  # All permissions
    ]

    mode = draw(st.sampled_from(common_modes))

    return {
        "mode": mode,
        "readable": (mode & 0o400) != 0,
        "writable": (mode & 0o200) != 0,
        "executable": (mode & 0o100) != 0,
        "change_during_test": draw(st.booleans()),
    }


@composite
def disk_full_scenarios(
    draw: DrawFn,
) -> dict[str, Any]:
    """Generate disk space exhaustion scenarios.

    Simulates running out of disk space during operations.

    Args:
        draw: Hypothesis draw function

    Returns:
        Dictionary containing disk full scenario

    Example:
        ```python
        @given(scenario=disk_full_scenarios())
        def test_disk_full_handling(scenario):
            # Simulate disk full at specific point
            pass
        ```
    """
    total_space = draw(st.integers(min_value=1024, max_value=1024 * 1024 * 100))  # Up to 100MB
    used_space = draw(st.integers(min_value=0, max_value=total_space))

    return {
        "total_space": total_space,
        "used_space": used_space,
        "available_space": total_space - used_space,
        "fills_at_byte": draw(st.integers(min_value=0, max_value=max(1, total_space - used_space))),
        "operation_size": draw(st.integers(min_value=1024, max_value=total_space)),
    }


@composite
def network_error_patterns(
    draw: DrawFn,
) -> list[dict[str, Any]]:
    """Generate network failure patterns.

    Creates sequences of network errors and recovery scenarios.

    Args:
        draw: Hypothesis draw function

    Returns:
        List of network error events

    Example:
        ```python
        @given(errors=network_error_patterns())
        async def test_network_resilience(errors):
            for error_event in errors:
                if error_event['type'] == 'timeout':
                    # Simulate timeout
                    pass
        ```
    """
    num_events = draw(st.integers(min_value=1, max_value=20))

    error_types = [
        "timeout",
        "connection_refused",
        "connection_reset",
        "dns_failure",
        "ssl_error",
        "partial_response",
        "slow_response",
    ]

    events = []
    for _ in range(num_events):
        error_type = draw(st.sampled_from(error_types))

        event: dict[str, Any] = {
            "type": error_type,
            "at_byte": draw(st.integers(min_value=0, max_value=10000)),
        }

        if error_type == "timeout":
            event["timeout_after"] = draw(st.floats(min_value=0.1, max_value=30.0))
        elif error_type == "slow_response":
            event["bytes_per_second"] = draw(st.integers(min_value=100, max_value=10000))
        elif error_type == "partial_response":
            event["bytes_received"] = draw(st.integers(min_value=0, max_value=10000))
            event["expected_bytes"] = draw(st.integers(min_value=event["bytes_received"], max_value=100000))

        events.append(event)

    return events


@composite
def buffer_overflow_patterns(
    draw: DrawFn,
    max_buffer_size: int = 1024 * 1024,  # 1MB
) -> dict[str, Any]:
    """Generate buffer overflow scenarios.

    Creates situations where data exceeds buffer capacity.

    Args:
        draw: Hypothesis draw function
        max_buffer_size: Maximum buffer size in bytes

    Returns:
        Dictionary containing buffer overflow configuration

    Example:
        ```python
        @given(config=buffer_overflow_patterns())
        def test_buffer_handling(config):
            buffer = bytearray(config['buffer_size'])
            # Attempt to write config['data_size'] bytes
        ```
    """
    buffer_size = draw(st.integers(min_value=64, max_value=max_buffer_size))

    # Data size might exceed buffer
    overflow = draw(st.booleans())
    if overflow:
        data_size = draw(st.integers(min_value=buffer_size + 1, max_value=buffer_size * 2))
    else:
        data_size = draw(st.integers(min_value=0, max_value=buffer_size))

    return {
        "buffer_size": buffer_size,
        "data_size": data_size,
        "will_overflow": data_size > buffer_size,
        "overflow_bytes": max(0, data_size - buffer_size),
        "chunk_size": draw(st.integers(min_value=1, max_value=min(buffer_size, 8192))),
    }


@composite
def file_corruption_patterns(
    draw: DrawFn,
) -> dict[str, Any]:
    """Generate file corruption scenarios.

    Simulates various types of file corruption for testing recovery.

    Args:
        draw: Hypothesis draw function

    Returns:
        Dictionary containing corruption configuration

    Example:
        ```python
        @given(corruption=file_corruption_patterns())
        def test_corruption_recovery(tmp_path, corruption):
            # Create and corrupt a file
            pass
        ```
    """
    corruption_type = draw(
        st.sampled_from(
            [
                "truncated",  # File cut short
                "random_bytes",  # Random corruption
                "header_corrupt",  # Header/magic bytes corrupted
                "encoding_error",  # Invalid encoding
                "checksum_mismatch",  # Bad checksum
            ]
        )
    )

    config: dict[str, Any] = {
        "type": corruption_type,
    }

    if corruption_type == "truncated":
        config["truncate_at_percent"] = draw(st.floats(min_value=0.0, max_value=1.0))
    elif corruption_type == "random_bytes":
        config["corrupt_percent"] = draw(st.floats(min_value=0.01, max_value=0.5))
        config["num_corruptions"] = draw(st.integers(min_value=1, max_value=100))
    elif corruption_type == "header_corrupt":
        config["header_bytes_to_corrupt"] = draw(st.integers(min_value=1, max_value=64))

    return config


@composite
def lock_file_scenarios(
    draw: DrawFn,
) -> dict[str, Any]:
    """Generate file lock conflict scenarios.

    Creates situations with competing file locks and stale locks.

    Args:
        draw: Hypothesis draw function

    Returns:
        Dictionary containing lock scenario configuration

    Example:
        ```python
        @given(scenario=lock_file_scenarios())
        def test_file_locking(tmp_path, scenario):
            # Test file locking behavior
            pass
        ```
    """
    return {
        "num_processes": draw(st.integers(min_value=2, max_value=20)),
        "lock_duration": draw(st.floats(min_value=0.01, max_value=5.0)),
        "has_stale_lock": draw(st.booleans()),
        "stale_lock_age": draw(st.floats(min_value=1.0, max_value=3600.0)),
        "timeout": draw(st.floats(min_value=0.1, max_value=30.0)),
        "check_interval": draw(st.floats(min_value=0.001, max_value=1.0)),
        "corrupted_lock_file": draw(st.booleans()),
        "lock_content_type": draw(st.sampled_from(["json", "plain_text", "binary", "empty"])),
    }


@composite
def path_traversal_patterns(
    draw: DrawFn,
) -> str:
    """Generate path traversal attack patterns.

    Creates potentially malicious path patterns for security testing.

    Args:
        draw: Hypothesis draw function

    Returns:
        A path string that might contain traversal attempts

    Example:
        ```python
        @given(path=path_traversal_patterns())
        def test_path_validation(path):
            # Ensure path traversal is blocked
            sanitized = sanitize_path(path)
        ```
    """
    patterns = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "./././../../../",
        "/etc/passwd",
        "C:\\Windows\\System32\\config\\sam",
        "./../.../../",
        "....//....//....//",
        "%2e%2e%2f%2e%2e%2f",  # URL encoded
        "..%252f..%252f",  # Double encoded
    ]

    # Mix safe and unsafe paths
    if draw(st.booleans()):
        return draw(st.sampled_from(patterns))
    else:
        # Safe relative path
        parts = draw(
            st.lists(
                st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10),
                min_size=1,
                max_size=5,
            )
        )
        return str(Path(*parts))


__all__ = [
    "buffer_overflow_patterns",
    "disk_full_scenarios",
    "file_corruption_patterns",
    "file_sizes",
    "lock_file_scenarios",
    "network_error_patterns",
    "path_traversal_patterns",
    "permission_patterns",
]
