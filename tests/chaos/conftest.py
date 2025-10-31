#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Pytest configuration for chaos strategy tests."""

from __future__ import annotations

from hypothesis import Verbosity, settings
import pytest

# Use smoke profile for testing the strategies themselves (fast)
settings.register_profile(
    "chaos_test",
    max_examples=50,  # Enough to validate strategies
    verbosity=Verbosity.normal,
    deadline=5000,
    print_blob=True,
)


@pytest.fixture(scope="session", autouse=True)
def configure_hypothesis_for_chaos_tests() -> None:
    """Configure Hypothesis for chaos strategy tests."""
    settings.load_profile("chaos_test")


# 🧪✅🔚
