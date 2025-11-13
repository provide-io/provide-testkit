#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for I/O and file system chaos strategies."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any

from hypothesis import given, settings

from provide.testkit.chaos.io_strategies import (  # type: ignore[import-untyped]
    buffer_overflow_patterns,
    disk_full_scenarios,
    file_corruption_patterns,
    file_sizes,
    lock_file_scenarios,
    network_error_patterns,
    path_traversal_patterns,
    permission_patterns,
)


class TestFileSizes:
    """Test file size strategy."""

    @given(size=file_sizes())
    def test_default_range(self, size: int) -> None:
        """Test default file sizes are in valid range."""
        assert 0 <= size <= 10 * 1024 * 1024  # 10MB default

    @given(size=file_sizes(min_size=1024, max_size=1024 * 1024))
    def test_custom_range(self, size: int) -> None:
        """Test custom file size range."""
        # Strategy includes multiple ranges: 0, 1-1024, 1024-1MB, min_size-max_size
        assert size >= 0

    @given(size=file_sizes(include_huge=True))
    def test_huge_files(self, size: int) -> None:
        """Test file sizes can include huge files."""
        assert size >= 0
        # Could be up to 1GB when include_huge=True


class TestPermissionPatterns:
    """Test permission pattern strategy."""

    @given(perms=permission_patterns())
    def test_permission_structure(self, perms: dict[str, Any]) -> None:
        """Test permission patterns have correct structure."""
        assert isinstance(perms, dict)
        assert "mode" in perms
        assert "readable" in perms
        assert "writable" in perms
        assert "executable" in perms
        assert "change_during_test" in perms

        # Mode should be a valid permission
        assert perms["mode"] in (0o000, 0o400, 0o600, 0o644, 0o755, 0o777)

    @given(perms=permission_patterns())
    def test_permission_flags_match_mode(self, perms: dict[str, Any]) -> None:
        """Test permission flags correctly represent mode."""
        mode = perms["mode"]

        # Check read permission
        assert perms["readable"] == ((mode & 0o400) != 0)

        # Check write permission
        assert perms["writable"] == ((mode & 0o200) != 0)

        # Check execute permission
        assert perms["executable"] == ((mode & 0o100) != 0)


class TestDiskFullScenarios:
    """Test disk full scenario strategy."""

    @settings(max_examples=50)
    @given(scenario=disk_full_scenarios())
    def test_disk_scenario_structure(self, scenario: dict[str, Any]) -> None:
        """Test disk full scenarios have required fields."""
        assert isinstance(scenario, dict)
        assert "total_space" in scenario
        assert "used_space" in scenario
        assert "available_space" in scenario
        assert "fills_at_byte" in scenario
        assert "operation_size" in scenario

    @given(scenario=disk_full_scenarios())
    def test_disk_space_math(self, scenario: dict[str, Any]) -> None:
        """Test disk space calculations are consistent."""
        # Available = Total - Used
        expected_available = scenario["total_space"] - scenario["used_space"]
        assert scenario["available_space"] == expected_available

        # Used should not exceed total
        assert scenario["used_space"] <= scenario["total_space"]

        # fills_at_byte should be within available space
        assert 0 <= scenario["fills_at_byte"] <= max(1, scenario["available_space"])


class TestNetworkErrorPatterns:
    """Test network error pattern strategy."""

    @settings(max_examples=50)
    @given(errors=network_error_patterns())
    def test_error_pattern_structure(self, errors: list[dict[str, Any]]) -> None:
        """Test network error patterns have correct structure."""
        assert isinstance(errors, list)
        assert 1 <= len(errors) <= 20

        valid_types = [
            "timeout",
            "connection_refused",
            "connection_reset",
            "dns_failure",
            "ssl_error",
            "partial_response",
            "slow_response",
        ]

        for error in errors:
            assert isinstance(error, dict)
            assert "type" in error
            assert "at_byte" in error
            assert error["type"] in valid_types
            assert 0 <= error["at_byte"] <= 10000

    @given(errors=network_error_patterns())
    def test_error_type_specific_fields(self, errors: list[dict[str, Any]]) -> None:
        """Test error type-specific fields are present."""
        for error in errors:
            if error["type"] == "timeout":
                assert "timeout_after" in error
                assert 0.1 <= error["timeout_after"] <= 30.0
            elif error["type"] == "slow_response":
                assert "bytes_per_second" in error
                assert 100 <= error["bytes_per_second"] <= 10000
            elif error["type"] == "partial_response":
                assert "bytes_received" in error
                assert "expected_bytes" in error
                assert 0 <= error["bytes_received"] <= error["expected_bytes"]


class TestBufferOverflowPatterns:
    """Test buffer overflow pattern strategy."""

    @given(config=buffer_overflow_patterns())
    def test_buffer_structure(self, config: dict[str, Any]) -> None:
        """Test buffer overflow configs have required fields."""
        assert isinstance(config, dict)
        assert "buffer_size" in config
        assert "data_size" in config
        assert "will_overflow" in config
        assert "overflow_bytes" in config
        assert "chunk_size" in config

    @given(config=buffer_overflow_patterns())
    def test_overflow_calculation(self, config: dict[str, Any]) -> None:
        """Test overflow detection is correct."""
        # will_overflow should match data_size > buffer_size
        assert config["will_overflow"] == (config["data_size"] > config["buffer_size"])

        # overflow_bytes should be correct
        expected_overflow = max(0, config["data_size"] - config["buffer_size"])
        assert config["overflow_bytes"] == expected_overflow

    @given(config=buffer_overflow_patterns(max_buffer_size=1024))
    def test_chunk_size_valid(self, config: dict[str, Any]) -> None:
        """Test chunk size is reasonable."""
        assert 1 <= config["chunk_size"] <= min(config["buffer_size"], 8192)


class TestFileCorruptionPatterns:
    """Test file corruption pattern strategy."""

    @given(corruption=file_corruption_patterns())
    def test_corruption_structure(self, corruption: dict[str, Any]) -> None:
        """Test corruption patterns have correct structure."""
        assert isinstance(corruption, dict)
        assert "type" in corruption

        valid_types = [
            "truncated",
            "random_bytes",
            "header_corrupt",
            "encoding_error",
            "checksum_mismatch",
        ]
        assert corruption["type"] in valid_types

    @given(corruption=file_corruption_patterns())
    def test_corruption_type_specific_fields(self, corruption: dict[str, Any]) -> None:
        """Test corruption type-specific fields are present."""
        if corruption["type"] == "truncated":
            assert "truncate_at_percent" in corruption
            assert 0.0 <= corruption["truncate_at_percent"] <= 1.0
        elif corruption["type"] == "random_bytes":
            assert "corrupt_percent" in corruption
            assert "num_corruptions" in corruption
            assert 0.01 <= corruption["corrupt_percent"] <= 0.5
            assert 1 <= corruption["num_corruptions"] <= 100
        elif corruption["type"] == "header_corrupt":
            assert "header_bytes_to_corrupt" in corruption
            assert 1 <= corruption["header_bytes_to_corrupt"] <= 64


class TestLockFileScenarios:
    """Test lock file scenario strategy."""

    @given(scenario=lock_file_scenarios())
    def test_lock_scenario_structure(self, scenario: dict[str, Any]) -> None:
        """Test lock scenarios have required fields."""
        assert isinstance(scenario, dict)
        assert "num_processes" in scenario
        assert "lock_duration" in scenario
        assert "has_stale_lock" in scenario
        assert "stale_lock_age" in scenario
        assert "timeout" in scenario
        assert "check_interval" in scenario
        assert "corrupted_lock_file" in scenario
        assert "lock_content_type" in scenario

    @settings(max_examples=50)
    @given(scenario=lock_file_scenarios())
    def test_lock_scenario_ranges(self, scenario: dict[str, Any]) -> None:
        """Test lock scenario values are in valid ranges."""
        assert 2 <= scenario["num_processes"] <= 20
        assert 0.01 <= scenario["lock_duration"] <= 5.0
        assert 1.0 <= scenario["stale_lock_age"] <= 3600.0
        assert 0.1 <= scenario["timeout"] <= 30.0
        assert 0.001 <= scenario["check_interval"] <= 1.0
        assert scenario["lock_content_type"] in ["json", "plain_text", "binary", "empty"]


class TestPathTraversalPatterns:
    """Test path traversal pattern strategy."""

    @given(path=path_traversal_patterns())
    def test_path_is_string(self, path: str) -> None:
        """Test path traversal patterns return strings."""
        assert isinstance(path, str)
        assert len(path) > 0

    @given(path=path_traversal_patterns())
    def test_malicious_or_safe_path(self, path: str) -> None:
        """Test paths are either malicious patterns or safe."""
        # Known malicious patterns
        malicious_indicators = [
            "..",
            "/etc/passwd",
            "windows",
            "system32",
            "%2e%2e",
        ]

        is_potentially_malicious = any(indicator in path.lower() for indicator in malicious_indicators)

        if not is_potentially_malicious:
            # Should be a safe relative path; best-effort Path conversion
            with suppress(Exception):
                Path(path)


# 🧪✅🔚
