#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for async fixtures to prevent regression of recursion bugs."""

from __future__ import annotations

import asyncio

import pytest


@pytest.mark.asyncio
async def test_clean_event_loop_no_recursion(clean_event_loop):
    """Verify clean_event_loop fixture doesn't cause recursion during teardown.

    This test ensures that the fixture properly excludes the current task
    from cancellation to prevent RecursionError during asyncio task cleanup.
    """

    async def nested_task():
        await asyncio.sleep(0.01)

    task = asyncio.create_task(nested_task())
    await task
    # Fixture teardown should not cause RecursionError


@pytest.mark.asyncio
async def test_clean_event_loop_with_pending_tasks(clean_event_loop):
    """Verify clean_event_loop cancels pending tasks without recursion."""

    async def long_running_task():
        await asyncio.sleep(10)  # Will be cancelled

    # Create a task that will be pending during teardown
    task = asyncio.create_task(long_running_task())

    # Don't await - let it be cancelled during teardown
    await asyncio.sleep(0.01)

    # Task should still be running
    assert not task.done()
    # Fixture teardown will cancel it without RecursionError


# 🧱🏗️🔚
