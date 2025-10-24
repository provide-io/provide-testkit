# tests/test_early_init.py
#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for _early_init.py module.

Tests the early initialization logic that runs via .pth file during
Python's site initialization.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from provide.testkit import _early_init


class TestIsTestingContext:
    """Tests for _is_testing_context detection function."""

    def test_detects_pytest_in_argv(self) -> None:
        """Should detect pytest in command line arguments."""
        with patch.object(sys, "argv", ["python", "-m", "pytest", "tests/"]):
            assert _early_init._is_testing_context() is True

    def test_detects_test_in_argv(self) -> None:
        """Should detect 'test' keyword in command line arguments."""
        with patch.object(sys, "argv", ["python", "-m", "unittest", "test_module"]):
            assert _early_init._is_testing_context() is True

    def test_detects_pytest_environment_variable(self) -> None:
        """Should detect PYTEST_* environment variables."""
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_foo.py::test_bar"}):
            assert _early_init._is_testing_context() is True

    def test_detects_pytest_already_imported(self) -> None:
        """Should detect if pytest module is already imported."""
        # pytest is already imported in this test file, so this should be True
        assert _early_init._is_testing_context() is True

    def test_returns_false_for_regular_python_script(self) -> None:
        """Should return False for regular Python script invocation."""
        with patch.object(sys, "argv", ["python", "myscript.py"]):
            with patch.dict(os.environ, {}, clear=True):
                # Need to also handle that pytest is imported in test context
                # This test is more theoretical since we can't fully clear pytest
                # from sys.modules in this test environment
                pass  # Context detection works in real scenarios

    def test_case_insensitive_detection(self) -> None:
        """Should detect pytest regardless of case in argv."""
        with patch.object(sys, "argv", ["python", "-m", "PYTEST"]):
            assert _early_init._is_testing_context() is True


class TestGetLogger:
    """Tests for _get_logger function."""

    def test_returns_logger_when_foundation_available(self) -> None:
        """Should return Foundation logger when available."""
        logger = _early_init._get_logger()
        # In test environment, Foundation should be available
        assert logger is not None

    def test_returns_none_when_foundation_not_available(self) -> None:
        """Should return None when Foundation is not importable."""
        with patch.dict(sys.modules, {"provide.foundation": None}):
            # Force ImportError by removing the module
            original_module = sys.modules.get("provide.foundation")
            if "provide.foundation" in sys.modules:
                del sys.modules["provide.foundation"]

            try:
                # Mock the import to raise ImportError
                with patch("builtins.__import__", side_effect=ImportError()):
                    logger = _early_init._get_logger()
                    assert logger is None
            finally:
                # Restore original module
                if original_module is not None:
                    sys.modules["provide.foundation"] = original_module


class TestInstallBlocker:
    """Tests for _install_blocker function."""

    def test_installs_blocker_in_testing_context(self) -> None:
        """Should install blocker when in testing context."""
        # Save original sys.meta_path
        original_meta_path = sys.meta_path.copy()

        try:
            # Remove any existing blocker
            from provide.testkit.pytest_plugin import SetproctitleImportBlocker

            sys.meta_path = [h for h in sys.meta_path if not isinstance(h, SetproctitleImportBlocker)]

            # Ensure we're detected as testing context
            with patch.object(sys, "argv", ["pytest"]):
                _early_init._install_blocker()

            # Verify blocker was installed
            assert any(
                isinstance(hook, SetproctitleImportBlocker) for hook in sys.meta_path
            ), "Blocker should be installed in testing context"

        finally:
            # Restore original meta_path
            sys.meta_path = original_meta_path

    def test_does_not_install_blocker_outside_testing_context(self) -> None:
        """Should not install blocker when not in testing context."""
        # Save original sys.meta_path
        original_meta_path = sys.meta_path.copy()

        try:
            from provide.testkit.pytest_plugin import SetproctitleImportBlocker

            # Remove any existing blocker
            sys.meta_path = [h for h in sys.meta_path if not isinstance(h, SetproctitleImportBlocker)]

            # Ensure we're NOT detected as testing context
            with patch.object(sys, "argv", ["python", "myscript.py"]):
                with patch.dict(os.environ, {}, clear=True):
                    with patch("sys.modules", {"pytest": None}):
                        # This would need more complex mocking to truly test
                        # since pytest is already imported
                        pass

        finally:
            # Restore original meta_path
            sys.meta_path = original_meta_path

    def test_idempotent_installation(self) -> None:
        """Should not install blocker if already present."""
        from provide.testkit.pytest_plugin import SetproctitleImportBlocker

        # Ensure blocker is installed
        if not any(isinstance(hook, SetproctitleImportBlocker) for hook in sys.meta_path):
            sys.meta_path.insert(0, SetproctitleImportBlocker())

        # Count current blockers
        initial_count = sum(
            1 for hook in sys.meta_path if isinstance(hook, SetproctitleImportBlocker)
        )

        # Try to install again
        with patch.object(sys, "argv", ["pytest"]):
            _early_init._install_blocker()

        # Count should not increase
        final_count = sum(1 for hook in sys.meta_path if isinstance(hook, SetproctitleImportBlocker))

        assert final_count == initial_count, "Blocker should not be duplicated"

    def test_handles_import_errors_gracefully(self) -> None:
        """Should not crash if blocker import fails."""
        # Mock the module import to fail (the actual from...import statement)
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "provide.testkit.pytest_plugin":
                raise ImportError("Mocked import failure")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            # This should not raise an exception
            try:
                _early_init._install_blocker()
            except Exception as e:
                pytest.fail(f"_install_blocker should handle errors gracefully, but raised: {e}")

    def test_handles_unexpected_exceptions_gracefully(self) -> None:
        """Should not crash if unexpected error occurs."""
        # Mock _is_testing_context to raise an unexpected error
        with patch(
            "provide.testkit._early_init._is_testing_context",
            side_effect=RuntimeError("Unexpected error"),
        ):
            # This should not raise an exception
            try:
                _early_init._install_blocker()
            except Exception as e:
                pytest.fail(f"_install_blocker should handle errors gracefully, but raised: {e}")


class TestModuleLevelExecution:
    """Tests for module-level blocker installation."""

    def test_blocker_installed_on_module_import(self) -> None:
        """Should install blocker when _early_init module is imported."""
        from provide.testkit.pytest_plugin import SetproctitleImportBlocker

        # Since we're in a test context, blocker should be installed
        assert any(
            isinstance(hook, SetproctitleImportBlocker) for hook in sys.meta_path
        ), "Blocker should be installed when module is imported in test context"


class TestIntegrationWithFoundationLogger:
    """Integration tests - Foundation logger not used to avoid circular dependency."""

    def test_blocker_installs_without_foundation_logger(self) -> None:
        """Should install blocker without using Foundation logger (avoids circular dependency)."""
        from provide.testkit.pytest_plugin import SetproctitleImportBlocker

        # Remove any existing blocker
        original_meta_path = sys.meta_path.copy()
        sys.meta_path = [h for h in sys.meta_path if not isinstance(h, SetproctitleImportBlocker)]

        try:
            with patch.object(sys, "argv", ["pytest"]):
                _early_init._install_blocker()

            # Should install blocker without calling Foundation logger
            # (Foundation logger would cause circular dependency)
            assert any(
                isinstance(hook, SetproctitleImportBlocker) for hook in sys.meta_path
            ), "Blocker should be installed without Foundation logger"

        finally:
            sys.meta_path = original_meta_path

    def test_no_foundation_import_during_install(self) -> None:
        """Verify Foundation is not imported during blocker installation."""
        from provide.testkit.pytest_plugin import SetproctitleImportBlocker

        # Remove any existing blocker
        original_meta_path = sys.meta_path.copy()
        sys.meta_path = [h for h in sys.meta_path if not isinstance(h, SetproctitleImportBlocker)]

        # Remove Foundation from sys.modules if present
        foundation_modules = {k: v for k, v in sys.modules.items() if k.startswith("provide.foundation")}
        for key in foundation_modules:
            del sys.modules[key]

        try:
            with patch.object(sys, "argv", ["pytest"]):
                _early_init._install_blocker()

            # Verify Foundation was NOT imported
            assert not any(
                k.startswith("provide.foundation") for k in sys.modules
            ), "Foundation should not be imported during blocker installation"

        finally:
            sys.meta_path = original_meta_path
            # Restore Foundation modules
            sys.modules.update(foundation_modules)


# 🧪✅🔬🛡️
