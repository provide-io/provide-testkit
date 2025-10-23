# provide/testkit/pytest_plugin.py
#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

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
- Uses standard Python import hook mechanism
"""

from __future__ import annotations

import sys
from typing import Any


class SetproctitleImportBlocker:
    """Import hook that blocks setproctitle imports by raising ImportError.

    This hooks into Python's import system via sys.meta_path and intercepts
    any attempt to import setproctitle, causing it to fail with ImportError.

    pytest-xdist has built-in fallback handling for ImportError when importing
    setproctitle, so this causes it to use its no-op implementation instead.
    """

    def find_spec(
        self,
        fullname: str,
        path: Any = None,
        target: Any = None,
    ) -> None:
        """Block setproctitle imports by raising ImportError.

        When setproctitle is imported, this hook raises ImportError,
        which pytest-xdist catches and handles gracefully by using
        its built-in no-op fallback implementation.
        """
        if fullname == "setproctitle":
            raise ImportError("setproctitle import blocked by provide-testkit to prevent macOS freezing")
        return None


# Install the import hook at module load time
# This happens BEFORE any other code runs, including xdist's worker initialization
if not any(isinstance(hook, SetproctitleImportBlocker) for hook in sys.meta_path):
    sys.meta_path.insert(0, SetproctitleImportBlocker())


def pytest_load_initial_conftests() -> None:
    """Hook kept for documentation purposes.

    The actual setproctitle mocking happens at module level (above),
    not in this hook, because hooks run too late - xdist imports
    setproctitle before hooks execute.
    """
    pass


# 🔌🚫📋🪄
