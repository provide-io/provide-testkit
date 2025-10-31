#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Centralized setproctitle blocker installation logic.

This module provides a single function to conditionally install the
setproctitle import blocker only when running under pytest."""

from __future__ import annotations

import os
import sys


def should_install_blocker() -> bool:
    """Check if we should install the setproctitle blocker.

    Returns:
        True if running under pytest, False otherwise
    """
    return (
        "PYTEST_CURRENT_TEST" in os.environ  # Running under pytest
        or "pytest" in sys.modules  # pytest is already imported
        or any("pytest" in arg for arg in sys.argv)  # pytest in command line
    )


def install_setproctitle_blocker(force: bool = False) -> None:
    """Install the setproctitle blocker if in pytest context.

    This function is idempotent - it won't install the blocker twice.
    Only installs when running under pytest to avoid breaking production use.

    Args:
        force: If True, install unconditionally. If False (default), only install
               if pytest context is detected. Use force=True when calling from
               pytest_plugin.py which only loads during pytest runs.
    """
    if not force and not should_install_blocker():
        return

    from provide.testkit._blocker import SetproctitleImportBlocker

    # Check if already installed
    if any(isinstance(hook, SetproctitleImportBlocker) for hook in sys.meta_path):
        return

    # Install the blocker
    sys.meta_path.insert(0, SetproctitleImportBlocker())


__all__ = ["install_setproctitle_blocker", "should_install_blocker"]

# 🧪✅🔚
