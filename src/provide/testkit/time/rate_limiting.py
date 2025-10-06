"""Rate limiting mock fixtures for testing.

Fixtures for testing rate-limited code.
"""

from __future__ import annotations

import pytest

from provide.testkit.time.classes import MockRateLimiter


@pytest.fixture
def rate_limiter_mock():
    """Mock for testing rate-limited code.

    Returns:
        Mock rate limiter that can be controlled in tests.

    Example:
        >>> def test_rate_limiting(rate_limiter_mock):
        ...     rate_limiter_mock.set_limit(after_calls=3)
        ...     assert rate_limiter_mock.check() is True  # Call 1
        ...     assert rate_limiter_mock.check() is True  # Call 2
        ...     assert rate_limiter_mock.check() is True  # Call 3
        ...     assert rate_limiter_mock.check() is False  # Rate limited!
    """
    return MockRateLimiter()


__all__ = [
    "rate_limiter_mock",
]
