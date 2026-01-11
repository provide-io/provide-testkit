#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for time mocking utilities."""

from __future__ import annotations

import asyncio
import time

import pytest

from provide.testkit.mocking.time import (
    SleepTracker,
    create_sleep_mock,
    mock_asyncio_sleep,
    mock_sleep,
    mock_time_sleep,
)


class TestSleepTracker:
    """Test SleepTracker class."""

    def test_init(self) -> None:
        """Test SleepTracker initialization."""
        tracker = SleepTracker()
        assert tracker.calls == []
        assert tracker.total_sleep_time == 0.0
        assert tracker.call_count == 0

    def test_add_call(self) -> None:
        """Test adding sleep calls."""
        tracker = SleepTracker()
        tracker.add_call(1.0)
        tracker.add_call(2.5)

        assert tracker.calls == [1.0, 2.5]
        assert tracker.total_sleep_time == 3.5
        assert tracker.call_count == 2

    def test_reset(self) -> None:
        """Test resetting tracker."""
        tracker = SleepTracker()
        tracker.add_call(1.0)
        tracker.add_call(2.0)

        tracker.reset()

        assert tracker.calls == []
        assert tracker.total_sleep_time == 0.0
        assert tracker.call_count == 0

    def test_call_count_property(self) -> None:
        """Test call_count property."""
        tracker = SleepTracker()
        assert tracker.call_count == 0

        tracker.add_call(1.0)
        assert tracker.call_count == 1

        tracker.add_call(2.0)
        assert tracker.call_count == 2


class TestMockSleep:
    """Test mock_sleep context manager."""

    def test_mocks_time_sleep(self) -> None:
        """Test that time.sleep is mocked."""
        with mock_sleep() as tracker:
            time.sleep(1.0)
            assert tracker.call_count == 1
            assert tracker.total_sleep_time == 1.0

    @pytest.mark.asyncio
    async def test_mocks_asyncio_sleep(self) -> None:
        """Test that asyncio.sleep is mocked."""
        with mock_sleep() as tracker:
            await asyncio.sleep(2.0)
            assert tracker.call_count == 1
            assert tracker.total_sleep_time == 2.0

    def test_instant_sleep_returns_immediately(self) -> None:
        """Test that instant=True makes sleep return immediately."""
        with mock_sleep(instant=True) as tracker:
            start = time.time()
            time.sleep(5.0)  # Should return immediately
            elapsed = time.time() - start

            assert elapsed < 0.1  # Should be nearly instant
            assert tracker.call_count == 1

    def test_tracks_multiple_calls(self) -> None:
        """Test tracking multiple sleep calls."""
        with mock_sleep() as tracker:
            time.sleep(1.0)
            time.sleep(2.0)
            time.sleep(3.0)

            assert tracker.call_count == 3
            assert tracker.calls == [1.0, 2.0, 3.0]
            assert tracker.total_sleep_time == 6.0

    def test_no_tracking(self) -> None:
        """Test disabling call tracking."""
        with mock_sleep(track_calls=False) as tracker:
            time.sleep(1.0)
            time.sleep(2.0)

            assert tracker.call_count == 0
            assert tracker.total_sleep_time == 0.0

    def test_custom_side_effect(self) -> None:
        """Test custom side effect."""
        called_with = []

        def custom_effect(duration: float) -> None:
            called_with.append(duration)

        with mock_sleep(instant=False, side_effect=custom_effect) as tracker:
            time.sleep(1.5)

            assert tracker.call_count == 1
            assert called_with == [1.5]


class TestMockTimeSleep:
    """Test mock_time_sleep context manager."""

    def test_mocks_only_time_sleep(self) -> None:
        """Test that only time.sleep is mocked."""
        with mock_time_sleep() as tracker:
            time.sleep(1.0)
            assert tracker.call_count == 1
            assert tracker.total_sleep_time == 1.0

    def test_instant_time_sleep(self) -> None:
        """Test instant time sleep."""
        with mock_time_sleep(instant=True) as tracker:
            start = time.time()
            time.sleep(5.0)
            elapsed = time.time() - start

            assert elapsed < 0.1
            assert tracker.call_count == 1

    def test_no_tracking_time_sleep(self) -> None:
        """Test disabling tracking for time sleep."""
        with mock_time_sleep(track_calls=False) as tracker:
            time.sleep(1.0)
            assert tracker.call_count == 0


class TestMockAsyncioSleep:
    """Test mock_asyncio_sleep context manager."""

    @pytest.mark.asyncio
    async def test_mocks_only_asyncio_sleep(self) -> None:
        """Test that only asyncio.sleep is mocked."""
        with mock_asyncio_sleep() as tracker:
            await asyncio.sleep(1.0)
            assert tracker.call_count == 1
            assert tracker.total_sleep_time == 1.0

    @pytest.mark.asyncio
    async def test_instant_asyncio_sleep(self) -> None:
        """Test instant asyncio sleep."""
        with mock_asyncio_sleep(instant=True) as tracker:
            start = time.time()
            await asyncio.sleep(5.0)
            elapsed = time.time() - start

            assert elapsed < 0.1
            assert tracker.call_count == 1

    @pytest.mark.asyncio
    async def test_no_tracking_asyncio_sleep(self) -> None:
        """Test disabling tracking for asyncio sleep."""
        with mock_asyncio_sleep(track_calls=False) as tracker:
            await asyncio.sleep(1.0)
            assert tracker.call_count == 0

    @pytest.mark.asyncio
    async def test_multiple_asyncio_sleeps(self) -> None:
        """Test tracking multiple asyncio sleep calls."""
        with mock_asyncio_sleep() as tracker:
            await asyncio.sleep(1.0)
            await asyncio.sleep(2.0)
            await asyncio.sleep(3.0)

            assert tracker.call_count == 3
            assert tracker.calls == [1.0, 2.0, 3.0]
            assert tracker.total_sleep_time == 6.0


class TestCreateSleepMock:
    """Test create_sleep_mock function."""

    def test_creates_mock_with_tracker(self) -> None:
        """Test creating a mock with tracker."""
        mock = create_sleep_mock()

        assert hasattr(mock, "tracker")
        assert isinstance(mock.tracker, SleepTracker)
        assert mock.tracker.call_count == 0

    def test_mock_tracks_calls(self) -> None:
        """Test that created mock tracks calls."""
        mock = create_sleep_mock(track_calls=True)

        mock(1.0)
        mock(2.0)

        assert mock.tracker.call_count == 2
        assert mock.tracker.total_sleep_time == 3.0

    def test_mock_no_tracking(self) -> None:
        """Test creating mock without tracking."""
        mock = create_sleep_mock(track_calls=False)

        mock(1.0)
        mock(2.0)

        assert mock.tracker.call_count == 0
        assert mock.tracker.total_sleep_time == 0.0

    def test_mock_called(self) -> None:
        """Test that mock is called."""
        mock = create_sleep_mock()

        mock(1.5)

        assert mock.called
        assert mock.call_count == 1
        mock.assert_called_once_with(1.5)


# 🧪✅🔚
