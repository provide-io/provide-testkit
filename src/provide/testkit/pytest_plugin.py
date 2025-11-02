#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Pytest plugin that disables setproctitle to prevent pytest-xdist issues on macOS.

On macOS, when setproctitle is installed, pytest-xdist's use of it to set worker
process titles causes the terminal/UX to freeze completely. This plugin prevents
setproctitle from being imported by using Python's import hook system.

The plugin uses sys.meta_path to intercept setproctitle imports and raise ImportError,
causing pytest-xdist to gracefully fall back to its built-in no-op implementation.

This approach is clean because:
- It leverages xdist's existing try/except ImportError fallback
- Works in both main process and worker subprocesses automatically
- Requires no manual installation or .venv modification
- Uses standard Python import hook mechanism"""

from __future__ import annotations

# Install the import hook unconditionally
# This module is a pytest plugin (registered via pytest11 entry point) that ONLY
# loads when pytest is running, so we always want to install the blocker.
from provide.testkit._blocker import SetproctitleImportBlocker
from provide.testkit._install_blocker import install_setproctitle_blocker

install_setproctitle_blocker(force=True)

__all__ = ["SetproctitleImportBlocker", "pytest_load_initial_conftests"]


def pytest_load_initial_conftests() -> None:
    """Hook kept for documentation purposes.

    The actual setproctitle mocking happens at module level (above),
    not in this hook, because hooks run too late - xdist imports
    setproctitle before hooks execute.
    """
    pass


# 🧪✅🔚
