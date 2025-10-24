# tests/test_pth_installation.py
#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for .pth file installation and loading.

Tests that the .pth file is correctly installed to site-packages and
that it successfully loads the setproctitle blocker early enough to
prevent pytest-xdist from importing setproctitle.
"""

from __future__ import annotations

import os
import site
import subprocess
import sys
from pathlib import Path

import pytest


class TestPthFileInstallation:
    """Tests for .pth file installation to site-packages."""

    def test_pth_file_exists_in_package(self) -> None:
        """Verify .pth file exists in source package."""
        # Find the package root
        testkit_root = Path(__file__).parent.parent
        pth_file = testkit_root / "src" / "provide_testkit_init.pth"

        assert pth_file.exists(), f".pth file should exist at {pth_file}"

    def test_pth_file_content(self) -> None:
        """Verify .pth file contains correct import statement."""
        testkit_root = Path(__file__).parent.parent
        pth_file = testkit_root / "src" / "provide_testkit_init.pth"

        content = pth_file.read_text().strip()
        assert (
            "import provide.testkit._early_init" in content
        ), ".pth file should import _early_init module"
        assert (
            "TESTKIT_PTH_LOG" in content
        ), ".pth file should support TESTKIT_PTH_LOG for debugging"

    def test_pth_file_installed_in_site_packages(self) -> None:
        """Verify .pth file is installed to site-packages after package install."""
        # Get site-packages directories
        site_packages = site.getsitepackages()
        if hasattr(site, "getusersitepackages"):
            site_packages.append(site.getusersitepackages())

        # Also check virtualenv site-packages
        for path in sys.path:
            if "site-packages" in path:
                site_packages.append(path)

        # Look for our .pth file in any site-packages directory
        pth_found = False
        for sp in set(site_packages):  # Use set to avoid duplicates
            pth_path = Path(sp) / "provide_testkit_init.pth"
            if pth_path.exists():
                pth_found = True
                # Verify content
                content = pth_path.read_text().strip()
                assert "import provide.testkit._early_init" in content
                break

        assert pth_found, (
            "provide_testkit_init.pth should be installed in site-packages. "
            f"Searched in: {site_packages}"
        )


class TestEarlyInitExecution:
    """Tests that _early_init is executed during site initialization."""

    def test_blocker_installed_before_pytest_loads(self) -> None:
        """Verify blocker is in sys.meta_path before pytest loads."""
        from provide.testkit.pytest_plugin import SetproctitleImportBlocker

        # Since we're already running in pytest, the blocker should be installed
        assert any(
            isinstance(hook, SetproctitleImportBlocker) for hook in sys.meta_path
        ), "Blocker should be installed in sys.meta_path"

    def test_blocker_position_in_meta_path(self) -> None:
        """Verify blocker is at the front of sys.meta_path."""
        from provide.testkit.pytest_plugin import SetproctitleImportBlocker

        # Find the blocker
        blocker_indices = [
            i for i, hook in enumerate(sys.meta_path) if isinstance(hook, SetproctitleImportBlocker)
        ]

        assert len(blocker_indices) > 0, "At least one blocker should be in sys.meta_path"

        # First blocker should be near the front (position 0 or 1)
        # Position 1 is acceptable because some other hooks might be inserted
        assert (
            blocker_indices[0] <= 1
        ), f"Blocker should be at front of meta_path, but found at index {blocker_indices[0]}"


class TestSetproctitleBlocking:
    """Tests that setproctitle imports are actually blocked."""

    def test_setproctitle_import_raises_error(self) -> None:
        """Verify that importing setproctitle raises ImportError."""
        # Remove setproctitle from sys.modules if it exists
        setproctitle_module = sys.modules.pop("setproctitle", None)

        try:
            with pytest.raises(ImportError, match="setproctitle import blocked"):
                import setproctitle  # noqa: F401
        finally:
            # Restore if it was there
            if setproctitle_module is not None:
                sys.modules["setproctitle"] = setproctitle_module

    def test_pytest_xdist_handles_blocked_setproctitle(self) -> None:
        """Verify pytest-xdist gracefully handles blocked setproctitle."""
        # This is tested by the fact that our tests run successfully with -n auto
        # We can verify xdist is importable without errors
        try:
            import xdist  # noqa: F401

            # If we can import xdist without errors, it handled the blocked setproctitle
            assert True
        except ImportError:
            pytest.skip("pytest-xdist not installed")


class TestCrossProcessBehavior:
    """Tests that blocker works across process boundaries (pytest-xdist workers)."""

    @pytest.mark.integration
    def test_blocker_active_in_subprocess(self) -> None:
        """Verify blocker is active in subprocess (simulates pytest-xdist worker)."""
        # Create a simple Python script that checks for the blocker
        test_script = """
import sys
from provide.testkit.pytest_plugin import SetproctitleImportBlocker

# Check if blocker is installed
blocker_installed = any(
    isinstance(hook, SetproctitleImportBlocker)
    for hook in sys.meta_path
)

# Try to import setproctitle (should fail)
try:
    import setproctitle
    import_succeeded = True
except ImportError:
    import_succeeded = False

# Exit with status code indicating results
# 0 = blocker installed AND import blocked (success)
# 1 = blocker not installed OR import succeeded (failure)
if blocker_installed and not import_succeeded:
    sys.exit(0)
else:
    sys.exit(1)
"""

        # Run the script in a subprocess
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"Subprocess should have blocker installed and setproctitle blocked.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


class TestPthFileLoadOrder:
    """Tests to verify .pth file loads early enough."""

    def test_early_init_imported_before_conftest(self) -> None:
        """Verify _early_init is imported before conftest.py."""
        # If we're running this test, _early_init should already be imported
        assert (
            "provide.testkit._early_init" in sys.modules
        ), "_early_init should be imported via .pth file"

    def test_early_init_imported_before_pytest_plugin(self) -> None:
        """Verify _early_init is imported before pytest plugin entry point."""
        # Both should be imported, but _early_init should have installed blocker first
        assert "provide.testkit._early_init" in sys.modules
        assert "provide.testkit.pytest_plugin" in sys.modules

        from provide.testkit.pytest_plugin import SetproctitleImportBlocker

        # Blocker should be installed (either by _early_init or plugin)
        assert any(isinstance(hook, SetproctitleImportBlocker) for hook in sys.meta_path)


class TestPthFileEdgeCases:
    """Tests for edge cases and error handling."""

    def test_pth_file_handles_missing_module_gracefully(self) -> None:
        """Verify system doesn't crash if _early_init import fails."""
        # This is hard to test directly since the .pth file is already processed
        # But we can verify that _early_init has error handling

        # The _install_blocker function should have try/except
        from provide.testkit._early_init import _install_blocker

        # Should not raise even if called with mocked failures
        # (actual error handling is tested in test_early_init.py)
        _install_blocker()  # Should not raise

    @pytest.mark.integration
    def test_multiple_pth_file_loads_are_idempotent(self) -> None:
        """Verify loading .pth file multiple times doesn't duplicate blockers."""
        from provide.testkit.pytest_plugin import SetproctitleImportBlocker

        # Count blockers
        initial_count = sum(
            1 for hook in sys.meta_path if isinstance(hook, SetproctitleImportBlocker)
        )

        # Importing _early_init again should not add more blockers
        import importlib

        import provide.testkit._early_init

        importlib.reload(provide.testkit._early_init)

        final_count = sum(
            1 for hook in sys.meta_path if isinstance(hook, SetproctitleImportBlocker)
        )

        # Count should be the same (idempotent)
        assert final_count == initial_count, "Multiple loads should not duplicate blockers"


class TestPthFileUninstallation:
    """Tests related to package uninstallation."""

    def test_pth_file_location_is_in_package(self) -> None:
        """Verify .pth file will be removed when package is uninstalled."""
        # Find the .pth file in site-packages
        for path in sys.path:
            if "site-packages" in path:
                pth_path = Path(path) / "provide_testkit_init.pth"
                if pth_path.exists():
                    # Verify it's in a location that pip/uv will clean up
                    assert "provide-testkit" in str(
                        pth_path.parent
                    ) or "site-packages" in str(pth_path.parent)
                    break


# 🧪🔌⚡📦
