"""
MinimalTestCase Base Class.

Provides a lightweight base class for tests that need common utilities
but don't require Foundation state reset. Ideal for timing-sensitive
tests or tests that don't use Foundation components.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock


class MinimalTestCase:
    """Minimal test case base class without Foundation reset overhead.

    Provides common test utilities without the heavyweight Foundation reset:
    - Temporary file/directory tracking and cleanup
    - Mock tracking utilities
    - Common assertion methods
    - Output capture helpers

    Use this for timing-sensitive tests or tests that don't need
    Foundation state isolation.
    """

    def setup_method(self) -> None:
        """Set up test case with minimal overhead."""
        self._temp_files: list[Path] = []
        self._mocks: list[Mock] = []

    def teardown_method(self) -> None:
        """Clean up test case."""
        # Clean up temporary files
        for path in self._temp_files:
            if path.exists():
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil

                    shutil.rmtree(path)

        # Reset mocks
        for mock in self._mocks:
            mock.reset_mock()

    def create_temp_file(self, content: str = "", suffix: str = "") -> Path:
        """Create a temporary file that will be cleaned up."""
        from provide.foundation.file import temp_file

        with temp_file(suffix=suffix, text=True, cleanup=False) as path:
            if content:
                path.write_text(content)
            self._temp_files.append(path)
            return path

    def create_temp_dir(self) -> Path:
        """Create a temporary directory that will be cleaned up."""
        import tempfile

        temp_dir = Path(tempfile.mkdtemp())
        self._temp_files.append(temp_dir)
        return temp_dir

    def track_mock(self, mock: Mock) -> Mock:
        """Track a mock for automatic reset during teardown."""
        self._mocks.append(mock)
        return mock

    def assert_json_output(self, output: str, expected: dict[str, Any]) -> None:
        """Assert that output is valid JSON matching expected values."""
        try:
            actual = json.loads(output)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Output is not valid JSON: {e}\n{output}") from e

        for key, value in expected.items():
            assert key in actual, f"Key '{key}' not in output"
            assert actual[key] == value, f"Value mismatch for '{key}': {actual[key]} != {value}"

    def assert_contains_error(
        self, output: str, error_type: type[Exception], message: str | None = None
    ) -> None:
        """Assert that output contains an error of the specified type."""
        error_name = error_type.__name__
        assert error_name in output, f"Error type '{error_name}' not found in output: {output}"

        if message:
            assert message in output, f"Error message '{message}' not found in output: {output}"

    def assert_log_contains(self, captured_logs: str, level: str, message: str) -> None:
        """Assert that captured logs contain a message at the specified level."""
        log_line = f"[{level.lower()}]"
        assert log_line in captured_logs, f"Log level '{level}' not found in logs"
        assert message in captured_logs, f"Log message '{message}' not found in logs"

    def assert_file_exists(self, path: str | Path) -> None:
        """Assert that a file exists."""
        file_path = Path(path)
        assert file_path.exists(), f"File does not exist: {file_path}"
        assert file_path.is_file(), f"Path exists but is not a file: {file_path}"

    def assert_dir_exists(self, path: str | Path) -> None:
        """Assert that a directory exists."""
        dir_path = Path(path)
        assert dir_path.exists(), f"Directory does not exist: {dir_path}"
        assert dir_path.is_dir(), f"Path exists but is not a directory: {dir_path}"

    def assert_output_contains(self, output: str, expected: str) -> None:
        """Assert that output contains expected string."""
        assert expected in output, f"Expected '{expected}' not found in output: {output}"

    def assert_output_not_contains(self, output: str, unexpected: str) -> None:
        """Assert that output does not contain unexpected string."""
        assert unexpected not in output, f"Unexpected '{unexpected}' found in output: {output}"


__all__ = ["MinimalTestCase"]
