# provide/testkit/process/system_fixtures.py
#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""System-level process management fixtures for testing.

This module provides fixtures for managing system-level process behaviors
during tests, including process title manipulation and system resource management.
"""

from __future__ import annotations

from collections.abc import Generator
import sys
from provide.testkit.mocking import MagicMock

import pytest


@pytest.fixture(scope="session", autouse=True)
def disable_setproctitle() -> Generator[None, None, None]:
    """Disables setproctitle during tests to prevent pytest-xdist performance issues.

    The setproctitle module causes severe performance degradation when running
    tests with pytest-xdist parallelization:
    - Immediate slowdown on test start
    - Progressive performance degradation over time
    - High CPU usage due to frequent system calls

    Mocks setproctitle as a no-op during regular test runs while preserving
    functionality for mutation testing tools like mutmut that use it for
    displaying progress information.

    Autouse and session-scoped - applies automatically to all tests in a session.

    Yields:
        None: Context manager for test execution with setproctitle disabled

    Note:
        Only disables setproctitle when NOT running under mutmut.
        Mutmut detection uses sys.argv to check for "mutmut" in arguments.
    """
    # Only disable if not running under mutmut
    # mutmut needs setproctitle to show which mutations are being tested
    if not any("mutmut" in arg for arg in sys.argv):
        # Check if setproctitle is already imported
        original_module = sys.modules.get("setproctitle")

        # Create a mock module with common setproctitle functions
        mock_setproctitle = MagicMock()
        mock_setproctitle.setproctitle = MagicMock(return_value=None)
        mock_setproctitle.getproctitle = MagicMock(return_value="python")
        mock_setproctitle.setthreadtitle = MagicMock(return_value=None)
        mock_setproctitle.getthreadtitle = MagicMock(return_value="")

        # Inject the mock into sys.modules before any imports
        sys.modules["setproctitle"] = mock_setproctitle

        try:
            yield
        finally:
            # Restore original module if it existed
            if original_module is not None:
                sys.modules["setproctitle"] = original_module
            elif "setproctitle" in sys.modules:
                del sys.modules["setproctitle"]
    else:
        # When running under mutmut, don't disable setproctitle
        yield


__all__ = [
    "disable_setproctitle",
]


# 🖥️🔧🚫📋🪄
