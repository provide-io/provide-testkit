#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""SetproctitleImportBlocker class for preventing macOS freezing with pytest-xdist.

This module contains only the blocker class definition to avoid circular imports."""

from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path
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
            # DEBUG: Track setproctitle import attempts
            import os
            import tempfile
            import traceback

            _pid = os.getpid()
            _debug_file = Path(tempfile.gettempdir()) / f"testkit-debug-{_pid}.log"
            with _debug_file.open("a") as f:
                f.write(f"🐛🚫 [PID {_pid}] setproctitle import BLOCKED!\n")
                f.write("🐛📍 Stack trace:\n")
                for line in traceback.format_stack()[:-1]:
                    f.write(f"  {line.strip()}\n")
                f.flush()

            # Check if there's a stub setproctitle.py in site-packages
            # If found, create a ModuleSpec to load it directly
            for sp in sys.path:
                stub_path = Path(sp) / "setproctitle.py"
                if stub_path.exists():
                    # Found stub - create a ModuleSpec to force loading this file
                    # This prevents Python from finding the real setproctitle package
                    with _debug_file.open("a") as f:
                        f.write(f"🐛📝 [PID {_pid}] Using stub file: {stub_path}\n")
                        f.flush()
                    loader = importlib.machinery.SourceFileLoader(fullname, str(stub_path))
                    spec = importlib.util.spec_from_file_location(
                        fullname, stub_path, loader=loader, submodule_search_locations=None
                    )
                    return spec
            # No stub found, block the real setproctitle
            with _debug_file.open("a") as f:
                f.write(f"🐛❌ [PID {_pid}] No stub found, raising ImportError\n")
                f.flush()
            raise ImportError("setproctitle import blocked by provide-testkit to prevent macOS freezing")
        return None


__all__ = ["SetproctitleImportBlocker"]

# 🧪✅🔚
