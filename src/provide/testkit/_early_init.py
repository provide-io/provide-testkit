#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Early initialization for provide-testkit.

This module is imported via a .pth file during Python's site initialization,
before any user code runs. It installs the setproctitle import blocker early
enough to prevent pytest-xdist from importing setproctitle and causing macOS
UX freezing.

The .pth file approach ensures the blocker is installed:
- Before pytest starts
- Before any conftest.py files are loaded
- Before any test collection happens
- At the same time as sitecustomize.py would run

This provides the best developer experience - completely automatic activation
with zero configuration needed."""

from __future__ import annotations

import os
import sys


def _is_testing_context() -> bool:
    """Quick detection if we're likely in a testing context.

    This uses heuristics to avoid the overhead of installing the import
    blocker when running regular (non-test) Python scripts.

    Returns:
        True if we appear to be running tests, False otherwise
    """
    # Check command line arguments
    argv_str = " ".join(sys.argv).lower()
    if any(keyword in argv_str for keyword in ["pytest", "test", "py.test"]):
        return True

    # Check environment variables
    env_keys = os.environ.keys()
    if any(key.startswith("PYTEST") for key in env_keys):
        return True

    # Check if pytest is already imported (rare but possible)
    return "pytest" in sys.modules


def _get_logger() -> any:
    """Get Foundation logger if available, otherwise return None.

    We attempt to import Foundation logger but gracefully handle if it's
    not available (e.g., during package installation, or in minimal environments).

    Returns:
        Foundation logger instance or None if not available
    """
    try:
        from provide.foundation import logger

        return logger
    except ImportError:
        return None


def _install_blocker() -> None:
    """Install setproctitle import blocker if in testing context.

    This function is called during Python site initialization via the .pth file.
    It performs quick detection and installs the blocker only if needed.

    The installation is idempotent - if the blocker is already in sys.meta_path,
    we don't add it again.

    Note:
        This function must be extremely defensive with error handling since any
        uncaught exception will cause Python startup to fail.

        IMPORTANT: We cannot use Foundation logger here because Foundation itself
        imports setproctitle during initialization, which would create a circular
        dependency. The blocker must be installed BEFORE Foundation is imported.
    """
    try:
        # Only proceed if we're in a testing context
        if not _is_testing_context():
            return

        # Use centralized installation logic with force=True
        # We use force=True here because context detection can fail in pytest-xdist
        # worker processes (different sys.argv, no PYTEST env vars yet), but we
        # still need the blocker installed to prevent macOS freezing.
        from provide.testkit._install_blocker import install_setproctitle_blocker

        install_setproctitle_blocker(force=True)

    except Exception:
        # Silently ignore any errors during blocker installation
        # We don't want to break Python startup if something goes wrong
        # The fallback mechanisms (pytest11 entry point, __init__.py) will
        # still attempt to install the blocker later
        pass


# Install the blocker immediately when this module is imported
# This happens during site initialization via the .pth file
_install_blocker()


__all__ = ["_get_logger", "_install_blocker", "_is_testing_context"]

# 🧪✅🔚
