#!/usr/bin/env python3
"""Memray stress test for FoundationTestCase setup overhead.

Profiles allocation patterns in:
- FoundationTestCase.setup_method() (per-test overhead)
- _needs_full_reset() frame inspection logic
- _minimal_state_reset() lightweight path
- MinimalTestCase base setup
"""

import os

os.environ.setdefault("LOG_LEVEL", "ERROR")

from provide.testkit.base.foundation import FoundationTestCase


class StubTestCase(FoundationTestCase):
    """Stub test case for profiling setup_method overhead."""

    def test_placeholder(self) -> None:
        """Placeholder test method for frame inspection to find."""


def main() -> None:
    instance = StubTestCase()

    # Warmup
    instance.setup_method()

    # Stress: 5K setup_method cycles (full reset path)
    for _ in range(5_000):
        instance.setup_method()

    # Stress: 3K _needs_full_reset calls (frame inspection overhead)
    for _ in range(3_000):
        instance._needs_full_reset()

    # Stress: 3K _minimal_state_reset calls (lightweight path)
    for _ in range(3_000):
        instance._minimal_state_reset()

    print("TestCase setup stress complete: 11K cycles")


if __name__ == "__main__":
    main()
