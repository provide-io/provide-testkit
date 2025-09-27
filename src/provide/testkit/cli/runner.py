"""
Enhanced CLI Test Runner.

Provides comprehensive testing support for CLI applications with
enhanced output processing, ANSI stripping, and detailed assertions.
"""

from __future__ import annotations

import re
from typing import Any

import click
from click.testing import CliRunner, Result


class CliTestRunner:
    """Enhanced test runner for CLI commands using Click's testing facilities.

    Provides additional utilities beyond the basic CliRunner including:
    - Full output capture (stdout + stderr)
    - ANSI code stripping
    - Enhanced error reporting
    - Isolated filesystem support
    """

    def __init__(self) -> None:
        """Initialize the CLI test runner."""
        self.runner = CliRunner()

    def invoke(
        self,
        cli: click.Command | click.Group,
        args: list[str] | None = None,
        input: str | None = None,
        env: dict[str, str] | None = None,
        catch_exceptions: bool = True,
        **kwargs: Any,
    ) -> Result:
        """Invoke a CLI command for testing.

        Args:
            cli: Click command or group to invoke
            args: Command line arguments
            input: Input to send to the command
            env: Environment variables
            catch_exceptions: Whether to catch exceptions
            **kwargs: Additional arguments passed to click.testing.CliRunner.invoke

        Returns:
            Click Result object with command output and exit code
        """
        return self.runner.invoke(
            cli,
            args=args,
            input=input,
            env=env,
            catch_exceptions=catch_exceptions,
            **kwargs,
        )

    def isolated_filesystem(self) -> object:
        """Context manager for isolated filesystem testing.

        Returns:
            Context manager that creates an isolated filesystem
        """
        return self.runner.isolated_filesystem()

    def get_full_output(self, result: Result) -> str:
        """Get combined stdout and stderr with ANSI codes stripped.

        This method combines all available output from a CLI command result
        and removes ANSI escape codes for easier testing.

        Args:
            result: Click Result object from invoke()

        Returns:
            Combined output string with ANSI codes removed
        """
        # Try multiple ways to get all output
        full_output = result.output or ""

        # Add stderr if it exists
        if hasattr(result, "stderr") and result.stderr:
            full_output += result.stderr

        # Add stderr_bytes if it exists (decoded)
        if hasattr(result, "stderr_bytes") and result.stderr_bytes:
            full_output += result.stderr_bytes.decode("utf-8", errors="ignore")

        # Strip ANSI escape codes
        return re.sub(r"\x1b\[[0-9;]*m", "", full_output)

    def assert_success(self, result: Result, expected_output: str | None = None) -> None:
        """Assert that a CLI command succeeded.

        Args:
            result: Click Result object from invoke()
            expected_output: Optional string that should be in the output

        Raises:
            AssertionError: If command failed or expected output not found
        """
        if result.exit_code != 0:
            full_output = self.get_full_output(result)
            raise AssertionError(
                f"Command failed with exit code {result.exit_code}\n"
                f"Output: {full_output}\n"
                f"Exception: {result.exception}"
            )

        if expected_output:
            full_output = self.get_full_output(result)
            if expected_output not in full_output:
                raise AssertionError(
                    f"Expected output not found.\n"
                    f"Expected: {expected_output}\n"
                    f"Actual: {full_output}"
                )

    def assert_error(
        self,
        result: Result,
        expected_error: str | None = None,
        exit_code: int | None = None,
    ) -> None:
        """Assert that a CLI command failed.

        Args:
            result: Click Result object from invoke()
            expected_error: Optional error message that should be in the output
            exit_code: Optional specific exit code to check for

        Raises:
            AssertionError: If command succeeded unexpectedly or error details don't match
        """
        if result.exit_code == 0:
            full_output = self.get_full_output(result)
            raise AssertionError(f"Command succeeded unexpectedly\nOutput: {full_output}")

        if exit_code is not None and result.exit_code != exit_code:
            raise AssertionError(
                f"Wrong exit code.\nExpected: {exit_code}\nActual: {result.exit_code}"
            )

        if expected_error:
            full_output = self.get_full_output(result)
            if expected_error not in full_output:
                raise AssertionError(
                    f"Expected error not found.\n"
                    f"Expected: {expected_error}\n"
                    f"Actual: {full_output}"
                )

    def assert_output_contains(self, result: Result, expected: str) -> None:
        """Assert that command output contains expected string.

        Args:
            result: Click Result object from invoke()
            expected: String that should be in the output

        Raises:
            AssertionError: If expected string not found in output
        """
        full_output = self.get_full_output(result)
        if expected not in full_output:
            raise AssertionError(
                f"Expected string not found in output.\n"
                f"Expected: {expected}\n"
                f"Actual: {full_output}"
            )

    def assert_output_not_contains(self, result: Result, unexpected: str) -> None:
        """Assert that command output does not contain unexpected string.

        Args:
            result: Click Result object from invoke()
            unexpected: String that should not be in the output

        Raises:
            AssertionError: If unexpected string found in output
        """
        full_output = self.get_full_output(result)
        if unexpected in full_output:
            raise AssertionError(
                f"Unexpected string found in output.\n"
                f"Unexpected: {unexpected}\n"
                f"Actual: {full_output}"
            )


# Standalone functions for backward compatibility
def assert_cli_success(result: Result, expected_output: str | None = None) -> None:
    """Assert that a CLI command succeeded."""
    runner = CliTestRunner()
    runner.assert_success(result, expected_output)


def assert_cli_error(
    result: Result,
    expected_error: str | None = None,
    exit_code: int | None = None,
) -> None:
    """Assert that a CLI command failed."""
    runner = CliTestRunner()
    runner.assert_error(result, expected_error, exit_code)


__all__ = [
    "CliTestRunner",
    "assert_cli_success",
    "assert_cli_error",
]