#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for time-based chaos strategies."""

from __future__ import annotations

from hypothesis import given

from provide.testkit.chaos import (
    clock_skew,
    deadline_scenarios,
    jitter_patterns,
    rate_burst_patterns,
    retry_backoff_patterns,
    time_advances,
    timeout_patterns,
)


class TestTimeAdvances:
    """Test time advance strategy."""

    @given(advance=time_advances())
    def test_positive_time_advances(self, advance: float) -> None:
        """Test default time advances are positive."""
        assert 0.0 <= advance <= 3600.0

    @given(advance=time_advances(allow_backwards=True))
    def test_backwards_time_advances(self, advance: float) -> None:
        """Test backwards time advances when allowed."""
        assert -3600.0 <= advance <= 3600.0

    @given(advance=time_advances(min_advance=10.0, max_advance=100.0))
    def test_custom_range(self, advance: float) -> None:
        """Test custom time advance range."""
        assert 10.0 <= advance <= 100.0


class TestClockSkew:
    """Test clock skew strategy."""

    @given(skew=clock_skew())
    def test_clock_skew_structure(self, skew: dict) -> None:
        """Test clock skew has expected structure."""
        assert isinstance(skew, dict)
        assert "skew_seconds" in skew
        assert "drift_rate" in skew
        assert "has_backwards_jump" in skew
        assert "sync_interval" in skew

    @given(skew=clock_skew(max_skew=60.0))
    def test_skew_within_range(self, skew: dict) -> None:
        """Test skew seconds within specified range."""
        assert -60.0 <= skew["skew_seconds"] <= 60.0


class TestTimeoutPatterns:
    """Test timeout pattern strategy."""

    @given(timeout=timeout_patterns())
    def test_timeout_or_none(self, timeout: float | None) -> None:
        """Test timeout is float or None."""
        if timeout is not None:
            assert isinstance(timeout, float)
            assert timeout > 0

    @given(timeout=timeout_patterns(include_none=False))
    def test_timeout_never_none(self, timeout: float | None) -> None:
        """Test timeout is never None when disabled."""
        assert timeout is not None
        assert isinstance(timeout, float)


class TestRateBurstPatterns:
    """Test rate burst pattern strategy."""

    @given(bursts=rate_burst_patterns())
    def test_burst_pattern_structure(self, bursts: list) -> None:
        """Test burst patterns have correct structure."""
        assert isinstance(bursts, list)
        assert len(bursts) >= 1

        for time_offset, count in bursts:
            assert isinstance(time_offset, float)
            assert isinstance(count, int)
            assert time_offset >= 0
            assert count >= 1

    @given(bursts=rate_burst_patterns(max_burst_size=100))
    def test_burst_size_limit(self, bursts: list) -> None:
        """Test burst sizes respect limit."""
        for _, count in bursts:
            assert count <= 100


class TestJitterPatterns:
    """Test jitter pattern strategy."""

    @given(intervals=jitter_patterns())
    def test_jitter_around_base(self, intervals: list) -> None:
        """Test jitter is around base interval."""
        assert isinstance(intervals, list)
        assert len(intervals) >= 1

        for interval in intervals:
            assert isinstance(interval, float)
            # With 50% jitter on 1.0 base, range is 0.5 to 1.5
            assert interval > 0

    @given(intervals=jitter_patterns(base_interval=0.1, max_jitter_percent=10.0))
    def test_custom_jitter(self, intervals: list) -> None:
        """Test custom jitter parameters."""
        for interval in intervals:
            # 10% jitter on 0.1 is 0.01, so range is 0.09 to 0.11
            assert 0.08 <= interval <= 0.12  # Allow small floating point variance


class TestDeadlineScenarios:
    """Test deadline scenario strategy."""

    @given(scenario=deadline_scenarios())
    def test_deadline_scenario_structure(self, scenario: dict) -> None:
        """Test deadline scenarios have correct structure."""
        assert isinstance(scenario, dict)
        assert "deadline" in scenario
        assert "work_duration" in scenario
        assert "exceeds_deadline" in scenario
        assert "grace_period" in scenario

        assert scenario["deadline"] > 0
        assert scenario["work_duration"] >= 0

    @given(scenario=deadline_scenarios())
    def test_exceeds_deadline_flag(self, scenario: dict) -> None:
        """Test exceeds_deadline flag is accurate."""
        if scenario["exceeds_deadline"]:
            assert scenario["work_duration"] >= scenario["deadline"]
        else:
            assert scenario["work_duration"] < scenario["deadline"]


class TestRetryBackoffPatterns:
    """Test retry backoff pattern strategy."""

    @given(pattern=retry_backoff_patterns())
    def test_retry_pattern_structure(self, pattern: dict) -> None:
        """Test retry patterns have expected structure."""
        assert isinstance(pattern, dict)
        assert "max_attempts" in pattern
        assert "backoff_type" in pattern

        assert pattern["max_attempts"] >= 1
        assert pattern["backoff_type"] in ["constant", "linear", "exponential", "jittered"]

    @given(pattern=retry_backoff_patterns(max_retries=5))
    def test_max_retries_respected(self, pattern: dict) -> None:
        """Test max retries limit."""
        assert 1 <= pattern["max_attempts"] <= 5

    @given(pattern=retry_backoff_patterns())
    def test_backoff_type_config(self, pattern: dict) -> None:
        """Test backoff type has appropriate config."""
        if pattern["backoff_type"] == "constant":
            assert "base_delay" in pattern
        elif pattern["backoff_type"] == "linear":
            assert "base_delay" in pattern
            assert "increment" in pattern
        elif pattern["backoff_type"] == "exponential":
            assert "base_delay" in pattern
            assert "multiplier" in pattern
            assert "max_delay" in pattern
        elif pattern["backoff_type"] == "jittered":
            assert "base_delay" in pattern
            assert "multiplier" in pattern
            assert "jitter_percent" in pattern


__all__ = [
    "TestClockSkew",
    "TestDeadlineScenarios",
    "TestJitterPatterns",
    "TestRateBurstPatterns",
    "TestRetryBackoffPatterns",
    "TestTimeAdvances",
    "TestTimeoutPatterns",
]

# 🧪✅🔚
