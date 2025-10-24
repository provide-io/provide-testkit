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

import importlib.machinery
import importlib.util
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
    ) -> Any:
        """Block setproctitle imports or redirect to stub file.

        When setproctitle is imported, this hook either:
        1. Returns a ModuleSpec for the stub file (if found) - for mutmut compatibility
        2. Raises ImportError to block the real package - for pytest-xdist

        The stub file approach allows mutation testing tools like mutmut to
        import setproctitle without actually using the C extension that causes
        macOS freezing with pytest-xdist.

        Returns:
            ModuleSpec if stub file exists, otherwise raises ImportError
        """
        if fullname == "setproctitle":
            # Check if there's a stub setproctitle.py in site-packages
            # If found, create a ModuleSpec to load it directly
            import os

            for sp in sys.path:
                stub_path = os.path.join(sp, "setproctitle.py")
                if os.path.exists(stub_path):
                    # Found stub - create a ModuleSpec to force loading this file
                    # This prevents Python from finding the real setproctitle package
                    loader = importlib.machinery.SourceFileLoader(fullname, stub_path)
                    spec = importlib.util.spec_from_file_location(
                        fullname, stub_path, loader=loader, submodule_search_locations=None
                    )
                    return spec
            # No stub found, block the real setproctitle
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
