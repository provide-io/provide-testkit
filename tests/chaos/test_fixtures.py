#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for chaos testing fixtures."""

from __future__ import annotations

import pytest

from provide.testkit.chaos.fixtures import (  # type: ignore[import-untyped]
    ChaosFailureInjector,
    ChaosTimeSource,
)


class TestChaosTimeSource:
    """Test ChaosTimeSource fixture."""

    def test_initial_time(self) -> None:
        """Test initial time source."""
        source = ChaosTimeSource(start_time=1000.0)
        assert source() == 1000.0

    def test_advance_time(self) -> None:
        """Test advancing time."""
        source = ChaosTimeSource(start_time=1000.0)
        source.freeze()  # Freeze to prevent auto-update
        source.advance(60.0)
        assert source() == 1060.0

    def test_backwards_time(self) -> None:
        """Test backwards time jump."""
        source = ChaosTimeSource(start_time=1000.0)
        source.freeze()
        source.advance(-50.0)
        assert source() == 950.0

    def test_freeze_and_unfreeze(self) -> None:
        """Test freezing and unfreezing time."""
        source = ChaosTimeSource()
        source.freeze()
        time1 = source()
        time2 = source()
        assert time1 == time2  # Frozen

        source.unfreeze()
        # After unfreeze, time updates to real time

    def test_set_time(self) -> None:
        """Test setting absolute time."""
        source = ChaosTimeSource()
        source.set(2000.0)
        assert source() == 2000.0

    def test_reset(self) -> None:
        """Test resetting time source."""
        source = ChaosTimeSource(start_time=1000.0)
        source.freeze()
        source.advance(100.0)
        source.reset()
        assert not source._frozen


class TestChaosFailureInjector:
    """Test ChaosFailureInjector fixture."""

    def test_no_failures_initially(self) -> None:
        """Test no failures when patterns not set."""
        injector = ChaosFailureInjector()
        # Should not raise
        for _ in range(10):
            injector.check()

    def test_inject_failure_at_position(self) -> None:
        """Test failure injection at specific call."""
        injector = ChaosFailureInjector()
        injector.set_patterns([(2, ValueError)])

        # First two calls succeed
        injector.check()
        injector.check()

        # Third call should fail
        with pytest.raises(ValueError) as excinfo:
            injector.check()
        assert "Chaos-injected failure at call 2" in str(excinfo.value)

    def test_multiple_failures(self) -> None:
        """Test multiple failure injections."""
        injector = ChaosFailureInjector()
        injector.set_patterns([(1, ValueError), (3, IOError)])

        # Call 0: success
        injector.check()

        # Call 1: ValueError
        with pytest.raises(ValueError):
            injector.check()

        # Call 2: success
        injector.check()

        # Call 3: IOError
        with pytest.raises(OSError):
            injector.check()

    def test_reset_counter(self) -> None:
        """Test resetting call counter."""
        injector = ChaosFailureInjector()
        injector.set_patterns([(0, ValueError)])

        # First call fails
        with pytest.raises(ValueError):
            injector.check()

        # After reset, first call should fail again
        injector.reset()
        with pytest.raises(ValueError):
            injector.check()


__all__ = [
    "TestChaosFailureInjector",
    "TestChaosTimeSource",
]

# 🧪✅🔚
