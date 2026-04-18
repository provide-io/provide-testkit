#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Memray stress test for fixture creation hot paths.

Profiles allocation patterns in:
- mock_logger / mock_logger_factory (created per-test)
- AutoPatch lifecycle (create, patch, cleanup)
- Hub/Container isolation fixtures (Container(), Hub() construction)
- SleepTracker creation
"""

import os

os.environ.setdefault("LOG_LEVEL", "ERROR")

from provide.testkit.logger.mocks import mock_logger_factory
from provide.testkit.mocking.fixtures import AutoPatch
from provide.testkit.mocking.time import SleepTracker, create_sleep_mock


def _stress_mock_loggers(cycles: int) -> None:
    """Stress-test mock logger creation."""
    for _ in range(cycles):
        _ = mock_logger_factory()


def _stress_auto_patch(cycles: int) -> None:
    """Stress-test AutoPatch create/cleanup lifecycle."""
    for _ in range(cycles):
        ap = AutoPatch()
        # Simulate typical usage: a few patches then cleanup
        ap.cleanup()


def _stress_sleep_tracker(cycles: int) -> None:
    """Stress-test SleepTracker and create_sleep_mock."""
    for _ in range(cycles):
        tracker = SleepTracker()
        tracker.add_call(1.0)
        tracker.add_call(2.0)
        tracker.reset()

    for _ in range(cycles):
        _ = create_sleep_mock(instant=True, track_calls=True)


def _stress_hub_container(cycles: int) -> None:
    """Stress-test isolated Container and Hub creation."""
    from provide.foundation.hub import Container

    for _ in range(cycles):
        _ = Container()

    from provide.foundation.context import CLIContext
    from provide.foundation.hub import Hub
    from provide.foundation.hub.registry import Registry

    for _ in range(cycles):
        component_registry = Registry()
        command_registry = Registry()
        _ = Hub(
            context=CLIContext(),
            component_registry=component_registry,
            command_registry=command_registry,
            use_shared_registries=False,
        )


def main() -> None:
    # Warmup
    _ = mock_logger_factory()
    ap = AutoPatch()
    ap.cleanup()
    t = SleepTracker()
    t.add_call(0.1)

    # Stress cycles
    _stress_mock_loggers(5_000)
    _stress_auto_patch(5_000)
    _stress_sleep_tracker(3_000)
    _stress_hub_container(2_000)

    print("Fixture creation stress complete: 18K cycles")


if __name__ == "__main__":
    main()
