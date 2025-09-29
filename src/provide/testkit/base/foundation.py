"""
FoundationTestCase Base Class.

Provides a common base class for all Foundation-based tests with
standard utilities, automatic setup/cleanup, and common assertions.
"""

from __future__ import annotations

import pytest

from provide.testkit.base.minimal import MinimalTestCase
from provide.testkit.logger import reset_foundation_setup_for_testing


class FoundationTestCase(MinimalTestCase):
    """Base test case for Foundation-based tests.

    Provides common utilities for testing Foundation applications:
    - Automatic Foundation reset between tests
    - Temporary file/directory tracking and cleanup
    - Mock tracking utilities
    - Common assertion methods
    - Output capture helpers
    """

    def setup_method(self) -> None:
        """Set up test case with Foundation reset."""
        # Check if this test/class is marked as timing_sensitive
        if self._needs_full_reset():
            reset_foundation_setup_for_testing()

        # Always call parent setup for basic utilities
        super().setup_method()

    def _needs_full_reset(self) -> bool:
        """Check if this test needs full Foundation reset.

        Returns False if test/class is marked with timing_sensitive marker.
        """
        # Get the current test item from pytest's request fixture
        # We need to be careful here as this runs during setup
        try:
            import inspect

            # Get the test method
            frame = inspect.currentframe()
            while frame:
                if frame.f_code.co_name.startswith('test_'):
                    test_method = getattr(self, frame.f_code.co_name, None)
                    if test_method and hasattr(test_method, 'pytestmark'):
                        marks = getattr(test_method, 'pytestmark', [])
                        for mark in marks:
                            if mark.name == 'timing_sensitive':
                                return False
                    break
                frame = frame.f_back

            # Check class-level markers
            if hasattr(self.__class__, 'pytestmark'):
                marks = getattr(self.__class__, 'pytestmark', [])
                for mark in marks:
                    if mark.name == 'timing_sensitive':
                        return False
        except Exception:
            # If we can't determine, default to full reset for safety
            pass

        return True


__all__ = ["FoundationTestCase"]