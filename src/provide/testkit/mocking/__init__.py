"""
Mocking utilities for the provide-io ecosystem.

Standardized mocking patterns, fixtures, and utilities to reduce
boilerplate and ensure consistent mocking across all tests.

This module re-exports unittest.mock utilities and adds provide-specific
testing helpers. Import everything from here for consistency:

    from provide.testkit.mocking import Mock, patch, mock_logger

Re-exported from stdlib (unittest.mock):
    Mock, MagicMock, AsyncMock, PropertyMock - Mock object types
    patch, call, ANY, DEFAULT - Patching and assertion utilities
    mock_open - Mock for file operations
    create_autospec - Create mocks with automatic spec
    seal - Seal mocks to prevent new attributes
    sentinel - Create unique sentinel objects

Provide-specific utilities:
    mock_factory, magic_mock_factory, async_mock_factory, property_mock_factory
        - Factory fixtures for creating pre-configured mocks
    patch_fixture, patch_multiple_fixture - Patching with automatic cleanup
    auto_patch - Unified interface for object/dict/env patching
    spy_fixture - Create spies that call through to originals
    assert_mock_calls - Enhanced assertion helper with better errors
    mock_open_fixture - Fixture wrapper for mock_open

Time mocking utilities (from .time):
    mock_sleep, mock_time_sleep, mock_asyncio_sleep - Sleep function mocking
    SleepTracker - Track sleep call history and durations
    create_sleep_mock - Factory for sleep mocks
"""

from provide.testkit.mocking.fixtures import (
    ANY,
    AsyncMock,
    DEFAULT,
    MagicMock,
    Mock,
    PropertyMock,
    assert_mock_calls,
    async_mock_factory,
    auto_patch,
    call,
    create_autospec,
    magic_mock_factory,
    mock_factory,
    mock_open,
    mock_open_fixture,
    patch,
    patch_fixture,
    patch_multiple_fixture,
    property_mock_factory,
    seal,
    sentinel,
    spy_fixture,
)

__all__ = [
    "ANY",
    "AsyncMock",
    "DEFAULT",
    "MagicMock",
    "Mock",
    "PropertyMock",
    "assert_mock_calls",
    "async_mock_factory",
    "auto_patch",
    "call",
    "create_autospec",
    "magic_mock_factory",
    "mock_factory",
    "mock_open",
    "mock_open_fixture",
    "patch",
    "patch_fixture",
    "patch_multiple_fixture",
    "property_mock_factory",
    "seal",
    "sentinel",
    "spy_fixture",
]
