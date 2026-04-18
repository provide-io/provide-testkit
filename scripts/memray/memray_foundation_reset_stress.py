#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Memray stress test for Foundation reset hot paths.

Profiles allocation patterns in:
- reset_foundation_setup_for_testing() (called before every test)
- reset_foundation_state() (internal reset orchestration)
- The full import chain triggered by lazy imports inside reset functions
"""

import os

os.environ.setdefault("LOG_LEVEL", "ERROR")

from provide.testkit.logger.reset import (
    reset_foundation_setup_for_testing,
    reset_foundation_state,
)


def main() -> None:
    # Warmup — trigger lazy imports and one-time initialization
    reset_foundation_setup_for_testing()
    reset_foundation_state()

    # Stress: 5K reset_foundation_setup_for_testing cycles
    # This is the most-called function in the entire test suite —
    # every test with the autouse fixture calls it.
    for _ in range(5_000):
        reset_foundation_setup_for_testing()

    # Stress: 5K reset_foundation_state cycles (lighter variant)
    for _ in range(5_000):
        reset_foundation_state()

    print("Foundation reset stress complete: 10K cycles")


if __name__ == "__main__":
    main()
