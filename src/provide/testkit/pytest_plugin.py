#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
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
- Uses standard Python import hook mechanism

Additionally, this plugin configures structlog with test-safe defaults BEFORE any
Foundation modules are imported. This ensures that fallback loggers created during
circular import resolution have proper processors and the BoundLogger wrapper class
(which supports trace level logging)."""

from __future__ import annotations

import sys

import structlog

# Configure structlog with test-safe defaults BEFORE Foundation imports.
# This ensures that even if Foundation's get_logger() falls back to structlog.get_logger()
# during circular import resolution, the returned loggers will have proper configuration
# with BoundLogger (which supports trace) rather than BoundLoggerFilteringAtNotset.


def _strip_foundation_context(
    _logger: object,
    _method_name: str,
    event_dict: dict[str, object],
) -> dict[str, object]:
    """Strip Foundation-specific bound context before rendering.

    Foundation binds logger_name and other context that PrintLogger
    doesn't accept as kwargs. This processor removes them.
    """
    event_dict.pop("logger_name", None)
    event_dict.pop("_foundation_level_hint", None)
    return event_dict


structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        _strip_foundation_context,  # type: ignore[list-item]
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    cache_logger_on_first_use=False,  # Disable caching for test isolation
)

# Install the import hook unconditionally
# This module is a pytest plugin (registered via pytest11 entry point) that ONLY
# loads when pytest is running, so we always want to install the blocker.
# These imports must be late (after structlog config above), so we suppress E402.
from provide.testkit._blocker import SetproctitleImportBlocker  # noqa: E402
from provide.testkit._install_blocker import install_setproctitle_blocker  # noqa: E402

install_setproctitle_blocker(force=True)

__all__ = ["SetproctitleImportBlocker", "pytest_load_initial_conftests"]


def pytest_load_initial_conftests() -> None:
    """Hook kept for documentation purposes.

    The actual setproctitle mocking happens at module level (above),
    not in this hook, because hooks run too late - xdist imports
    setproctitle before hooks execute.
    """


# 🧪✅🔚
