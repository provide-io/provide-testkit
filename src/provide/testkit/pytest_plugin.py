# provide/testkit/pytest_plugin.py
#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Pytest plugin that disables setproctitle to prevent pytest-xdist issues on macOS.

This plugin disables setproctitle at module-import time (not in a hook), ensuring
the mock is injected BEFORE pytest-xdist or any other code can import setproctitle.

On macOS, when setproctitle is installed, pytest-xdist's use of it to set worker
process titles causes the terminal/UX to freeze completely. This plugin prevents
that by mocking out setproctitle before it can be imported.

IMPORTANT: For pytest-xdist worker subprocesses to benefit from this plugin, you must
explicitly import this plugin at the top of your tests/conftest.py file:

    import provide.testkit.pytest_plugin  # noqa: F401

Worker subprocesses start with fresh Python interpreters and don't inherit sys.modules
from the parent process. By importing the plugin in conftest.py, you ensure it loads
early in both the main process and worker subprocesses, before xdist can import the
real setproctitle module.

The plugin is automatically registered via entry points, but explicit import ensures
proper load ordering in worker subprocesses.
"""

from __future__ import annotations

import sys
from types import ModuleType

# CRITICAL: This must happen at module-level (import time), NOT in a hook.
# Hooks run too late - xdist may have already imported setproctitle by then.
#
# By executing this at import time, we ensure the mock is in sys.modules
# BEFORE pytest-xdist workers initialize and try to import setproctitle.


# Lightweight no-op functions (much faster than MagicMock)
def _noop_setproctitle(title: str) -> None:
    """No-op replacement for setproctitle.setproctitle."""
    pass


def _noop_getproctitle() -> str:
    """No-op replacement for setproctitle.getproctitle."""
    return "python"


def _noop_setthreadtitle(title: str) -> None:
    """No-op replacement for setproctitle.setthreadtitle."""
    pass


def _noop_getthreadtitle() -> str:
    """No-op replacement for setproctitle.getthreadtitle."""
    return ""


if "setproctitle" not in sys.modules:
    # Create a lightweight fake module with no-op functions
    # This is much faster than MagicMock (zero overhead)
    mock_module = ModuleType("setproctitle")
    mock_module.setproctitle = _noop_setproctitle  # type: ignore[attr-defined]
    mock_module.getproctitle = _noop_getproctitle  # type: ignore[attr-defined]
    mock_module.setthreadtitle = _noop_setthreadtitle  # type: ignore[attr-defined]
    mock_module.getthreadtitle = _noop_getthreadtitle  # type: ignore[attr-defined]

    # Inject into sys.modules to intercept all imports
    sys.modules["setproctitle"] = mock_module
else:
    # setproctitle was already imported (edge case)
    # Replace its functions with lightweight no-ops
    existing_module = sys.modules["setproctitle"]

    # Replace all callable attributes with no-ops
    if hasattr(existing_module, "setproctitle"):
        existing_module.setproctitle = _noop_setproctitle
    if hasattr(existing_module, "getproctitle"):
        existing_module.getproctitle = _noop_getproctitle
    if hasattr(existing_module, "setthreadtitle"):
        existing_module.setthreadtitle = _noop_setthreadtitle
    if hasattr(existing_module, "getthreadtitle"):
        existing_module.getthreadtitle = _noop_getthreadtitle


def pytest_load_initial_conftests() -> None:
    """Hook kept for documentation purposes.

    The actual setproctitle mocking happens at module level (above),
    not in this hook, because hooks run too late - xdist imports
    setproctitle before hooks execute.
    """
    pass


# 🔌🚫📋🪄
