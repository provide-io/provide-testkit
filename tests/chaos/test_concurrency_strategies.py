#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for concurrency chaos strategies."""

from __future__ import annotations

from hypothesis import HealthCheck, given, settings

from provide.testkit.chaos.concurrency_strategies import (
    async_event_patterns,
    deadlock_scenarios,
    lock_contention_patterns,
    pid_recycling_scenarios,
    process_pool_patterns,
    race_condition_triggers,
    task_cancellation_patterns,
    thread_counts,
)

CHAOS_SETTINGS = {"deadline": None, "suppress_health_check": [HealthCheck.too_slow]}


def chaos_given(*args, max_examples: int | None = None, **kwargs):
    config = dict(CHAOS_SETTINGS)
    if max_examples is not None:
        config["max_examples"] = max_examples
    return settings(**config)(given(*args, **kwargs))


class TestThreadCounts:
    """Test thread count strategy."""

    @chaos_given(count=thread_counts())
    def test_default_range(self, count: int) -> None:
        """Test default thread counts are in valid range."""
        assert 1 <= count <= 100

    @chaos_given(count=thread_counts(min_threads=5, max_threads=20))
    def test_custom_range(self, count: int) -> None:
        """Test custom thread count range."""
        # With include_extremes=True (default), can be 1, 20, or 5-20
        assert count == 1 or count == 20 or (5 <= count <= 20)

    @chaos_given(count=thread_counts(include_extremes=False))
    def test_no_extremes(self, count: int) -> None:
        """Test thread counts without forced extremes."""
        assert isinstance(count, int)
        assert count >= 1


class TestRaceConditionTriggers:
    """Test race condition trigger strategy."""

    @chaos_given(timings=race_condition_triggers())
    def test_timing_structure(self, timings: list) -> None:
        """Test race condition timings have correct structure."""
        assert isinstance(timings, list)
        assert len(timings) == 10  # Default num_operations

        for op_id, delay in timings:
            assert isinstance(op_id, int)
            assert isinstance(delay, float)
            assert 0 <= delay <= 0.1  # Default max_delay
            assert 0 <= op_id < 10

    @chaos_given(timings=race_condition_triggers(num_operations=5, max_delay=1.0), max_examples=50)
    def test_custom_parameters(self, timings: list) -> None:
        """Test race condition timings with custom parameters."""
        assert len(timings) == 5
        for _, delay in timings:
            assert 0 <= delay <= 1.0


class TestDeadlockScenarios:
    """Test deadlock scenario strategy."""

    @chaos_given(scenario=deadlock_scenarios())
    def test_deadlock_structure(self, scenario: dict) -> None:
        """Test deadlock scenario has required fields."""
        assert isinstance(scenario, dict)
        assert "num_resources" in scenario
        assert "num_threads" in scenario
        assert "lock_sequences" in scenario
        assert "has_timeout" in scenario
        assert "timeout" in scenario

        # Validate values
        assert scenario["num_resources"] == 5  # Default
        assert 2 <= scenario["num_threads"] <= 10
        assert len(scenario["lock_sequences"]) == scenario["num_threads"]

    @chaos_given(scenario=deadlock_scenarios(num_resources=3))
    def test_lock_sequences_valid(self, scenario: dict) -> None:
        """Test lock sequences contain valid resource IDs."""
        for sequence in scenario["lock_sequences"]:
            assert isinstance(sequence, list)
            assert len(sequence) >= 1
            for resource_id in sequence:
                assert 0 <= resource_id < scenario["num_resources"]
            # Sequences should have unique resource IDs
            assert len(sequence) == len(set(sequence))


class TestAsyncEventPatterns:
    """Test async event pattern strategy."""

    @chaos_given(events=async_event_patterns())
    def test_event_structure(self, events: list) -> None:
        """Test async events have correct structure."""
        assert isinstance(events, list)
        assert 1 <= len(events) <= 50  # Default max_events

        for event in events:
            assert isinstance(event, dict)
            assert "type" in event
            assert event["type"] in ["delay", "immediate", "cancel", "timeout"]

            if event["type"] == "delay":
                assert "duration" in event
                assert 0.0 <= event["duration"] <= 1.0
            elif event["type"] == "timeout":
                assert "timeout" in event
                assert 0.01 <= event["timeout"] <= 2.0
            elif event["type"] == "cancel":
                assert "after_delay" in event
                assert 0.0 <= event["after_delay"] <= 0.5

    @chaos_given(events=async_event_patterns(max_events=10), max_examples=50)
    def test_custom_event_count(self, events: list) -> None:
        """Test async events with custom max count."""
        assert 1 <= len(events) <= 10


class TestLockContentionPatterns:
    """Test lock contention pattern strategy."""

    @chaos_given(pattern=lock_contention_patterns())
    def test_contention_structure(self, pattern: dict) -> None:
        """Test lock contention pattern has required fields."""
        assert isinstance(pattern, dict)
        assert "num_locks" in pattern
        assert "operations" in pattern
        assert "concurrent_workers" in pattern

        assert pattern["num_locks"] == 5  # Default
        assert len(pattern["operations"]) == 20  # Default num_operations
        assert 2 <= pattern["concurrent_workers"] <= 20

    @chaos_given(pattern=lock_contention_patterns(num_locks=3, num_operations=10), max_examples=50)
    def test_operation_validity(self, pattern: dict) -> None:
        """Test operations have valid lock requirements."""
        for op in pattern["operations"]:
            assert "locks_needed" in op
            assert "hold_duration" in op
            assert "operation_id" in op

            # Locks should be sorted (to prevent deadlock)
            assert op["locks_needed"] == sorted(op["locks_needed"])

            # All lock IDs should be valid
            for lock_id in op["locks_needed"]:
                assert 0 <= lock_id < pattern["num_locks"]

            # Hold duration should be positive
            assert 0.001 <= op["hold_duration"] <= 0.5


class TestTaskCancellationPatterns:
    """Test task cancellation pattern strategy."""

    @chaos_given(tasks=task_cancellation_patterns())
    def test_task_structure(self, tasks: list) -> None:
        """Test task cancellation patterns have correct structure."""
        assert isinstance(tasks, list)
        assert len(tasks) == 20  # Default num_tasks

        for task in tasks:
            assert "task_id" in task
            assert "should_cancel" in task

            if task["should_cancel"]:
                assert "cancel_after" in task
                assert "expect_cancellation_error" in task
                assert 0.0 <= task["cancel_after"] <= 1.0
            else:
                assert "expected_duration" in task
                assert 0.1 <= task["expected_duration"] <= 2.0

    @chaos_given(tasks=task_cancellation_patterns(num_tasks=10), max_examples=50)
    def test_custom_task_count(self, tasks: list) -> None:
        """Test task cancellation with custom count."""
        assert len(tasks) == 10


class TestProcessPoolPatterns:
    """Test process pool pattern strategy."""

    @chaos_given(config=process_pool_patterns())
    def test_pool_structure(self, config: dict) -> None:
        """Test process pool config has required fields."""
        assert isinstance(config, dict)
        assert "workers" in config
        assert "num_tasks" in config
        assert "task_pattern" in config
        assert "timeout" in config
        assert "max_tasks_per_child" in config

        assert 1 <= config["workers"] <= 10  # Default max_workers
        assert 1 <= config["num_tasks"] <= 100  # Default max_tasks
        assert config["task_pattern"] in ["uniform", "mixed", "bursty"]

        if config["timeout"] is not None:
            assert 1.0 <= config["timeout"] <= 30.0

        if config["max_tasks_per_child"] is not None:
            assert 1 <= config["max_tasks_per_child"] <= 50

    @chaos_given(config=process_pool_patterns(max_workers=4, max_tasks=20))
    def test_custom_pool_params(self, config: dict) -> None:
        """Test process pool with custom parameters."""
        assert 1 <= config["workers"] <= 4
        assert 1 <= config["num_tasks"] <= 20


class TestPidRecyclingScenarios:
    """Test PID recycling scenario strategy."""

    @chaos_given(scenario=pid_recycling_scenarios())
    def test_pid_recycling_structure(self, scenario: dict) -> None:
        """Test PID recycling scenario has required fields."""
        assert isinstance(scenario, dict)
        assert "original_pid" in scenario
        assert "recycled_pid" in scenario
        assert "original_start_time" in scenario
        assert "recycled_start_time" in scenario
        assert "time_tolerance" in scenario
        assert "should_detect_recycling" in scenario

        # PIDs should match (it's a recycling scenario)
        assert scenario["original_pid"] == scenario["recycled_pid"]

        # Recycled process starts after original
        assert scenario["recycled_start_time"] > scenario["original_start_time"]

        # Time tolerance should be reasonable
        assert 0.0 <= scenario["time_tolerance"] <= 2.0

        # Detection logic should be correct
        time_gap = abs(scenario["recycled_start_time"] - scenario["original_start_time"])
        expected_detection = time_gap > scenario["time_tolerance"]
        assert scenario["should_detect_recycling"] == expected_detection

    @chaos_given(scenario=pid_recycling_scenarios())
    def test_pid_ranges(self, scenario: dict) -> None:
        """Test PIDs are in valid range."""
        assert 1 <= scenario["original_pid"] <= 65535
        assert 1 <= scenario["recycled_pid"] <= 65535


# 🧪✅🔚
