#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for TimeMachine registry tracking."""

from __future__ import annotations

from provide.testkit.time.classes import TimeMachine, get_active_time_machines


class TestTimeMachineRegistry:
    """Test TimeMachine registry tracking."""

    def test_registry_empty_initially(self) -> None:
        """Registry should be empty when no TimeMachines exist."""
        # Clear any leftover instances
        for machine in get_active_time_machines():
            machine.cleanup()

        assert len(get_active_time_machines()) == 0

    def test_timemachine_registers_on_creation(self) -> None:
        """TimeMachine should register itself on creation."""
        machine = TimeMachine()
        try:
            assert machine in get_active_time_machines()
        finally:
            machine.cleanup()

    def test_timemachine_unregisters_on_cleanup(self) -> None:
        """TimeMachine should unregister on cleanup."""
        machine = TimeMachine()
        assert machine in get_active_time_machines()

        machine.cleanup()
        assert machine not in get_active_time_machines()

    def test_multiple_timemachines_tracked(self) -> None:
        """Multiple TimeMachines should all be tracked."""
        machines = [TimeMachine() for _ in range(3)]
        try:
            active = get_active_time_machines()
            assert len(active) >= 3
            for machine in machines:
                assert machine in active
        finally:
            for machine in machines:
                machine.cleanup()

    def test_cleanup_idempotent(self) -> None:
        """Cleanup should be safe to call multiple times."""
        machine = TimeMachine()
        machine.cleanup()
        machine.cleanup()  # Should not raise
        assert machine not in get_active_time_machines()

    def test_registry_returns_copy(self) -> None:
        """get_active_time_machines should return a copy."""
        machine = TimeMachine()
        try:
            registry1 = get_active_time_machines()
            registry2 = get_active_time_machines()

            # Should be equal but not the same object
            assert registry1 == registry2
            assert registry1 is not registry2
        finally:
            machine.cleanup()

    def test_frozen_timemachine_tracked(self) -> None:
        """Frozen TimeMachine should still be tracked."""
        machine = TimeMachine()
        try:
            machine.freeze()
            assert machine in get_active_time_machines()
            assert machine.is_frozen
        finally:
            machine.cleanup()


# 🧪✅🔚
