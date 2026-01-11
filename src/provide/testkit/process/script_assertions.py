#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Assertion utilities for bash script testing.

Provides specialized assertion functions for validating bash script
execution results, file creation, git operations, and other common
script side effects.
"""

from __future__ import annotations

from pathlib import Path

from provide.testkit.process.script_fixtures import ScriptResult


def assert_script_success(result: ScriptResult, message: str | None = None) -> None:
    """Assert that a script executed successfully (exit code 0).

    Args:
        result: Script execution result.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If script did not succeed.
    """
    if message is None:
        message = (
            f"Script failed with exit code {result.returncode}\n"
            f"Command: {result.command}\n"
            f"Stdout: {result.stdout}\n"
            f"Stderr: {result.stderr}"
        )
    assert result.returncode == 0, message


def assert_script_failure(result: ScriptResult, message: str | None = None) -> None:
    """Assert that a script failed (non-zero exit code).

    Args:
        result: Script execution result.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If script succeeded.
    """
    if message is None:
        message = (
            f"Script unexpectedly succeeded with exit code 0\n"
            f"Command: {result.command}\n"
            f"Stdout: {result.stdout}"
        )
    assert result.returncode != 0, message


def assert_script_exit_code(
    result: ScriptResult,
    expected_code: int,
    message: str | None = None,
) -> None:
    """Assert that a script exited with a specific code.

    Args:
        result: Script execution result.
        expected_code: Expected exit code.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If exit code does not match.
    """
    if message is None:
        message = (
            f"Script exit code {result.returncode} does not match expected {expected_code}\n"
            f"Command: {result.command}\n"
            f"Stdout: {result.stdout}\n"
            f"Stderr: {result.stderr}"
        )
    assert result.returncode == expected_code, message


def assert_file_created(file_path: Path, message: str | None = None) -> None:
    """Assert that a file was created.

    Args:
        file_path: Path to the file.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If file does not exist.
    """
    if message is None:
        message = f"File does not exist: {file_path}"
    assert file_path.exists() and file_path.is_file(), message


def assert_directory_exists(dir_path: Path, message: str | None = None) -> None:
    """Assert that a directory exists.

    Args:
        dir_path: Path to the directory.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If directory does not exist.
    """
    if message is None:
        message = f"Directory does not exist: {dir_path}"
    assert dir_path.exists() and dir_path.is_dir(), message


def assert_file_contains(
    file_path: Path,
    content: str,
    message: str | None = None,
) -> None:
    """Assert that a file contains specific content.

    Args:
        file_path: Path to the file.
        content: Content to search for.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If file does not contain the content.
    """
    if not file_path.exists():
        raise AssertionError(f"File does not exist: {file_path}")

    file_content = file_path.read_text()
    if message is None:
        message = (
            f"File {file_path} does not contain expected content\n"
            f"Expected: {content!r}\n"
            f"File contents: {file_content!r}"
        )
    assert content in file_content, message


def assert_file_not_contains(
    file_path: Path,
    content: str,
    message: str | None = None,
) -> None:
    """Assert that a file does not contain specific content.

    Args:
        file_path: Path to the file.
        content: Content that should not be present.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If file contains the content.
    """
    if not file_path.exists():
        raise AssertionError(f"File does not exist: {file_path}")

    file_content = file_path.read_text()
    if message is None:
        message = (
            f"File {file_path} unexpectedly contains content\n"
            f"Unexpected: {content!r}\n"
            f"File contents: {file_content!r}"
        )
    assert content not in file_content, message


def assert_git_repo_cloned(repo_path: Path, message: str | None = None) -> None:
    """Assert that a git repository was cloned.

    Checks that the directory exists and contains a .git directory.

    Args:
        repo_path: Path to the repository.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If repository was not cloned.
    """
    if message is None:
        message = f"Git repository not found at: {repo_path}"

    assert repo_path.exists() and repo_path.is_dir(), f"{message} (directory missing)"

    git_dir = repo_path / ".git"
    assert git_dir.exists() and git_dir.is_dir(), f"{message} (.git directory missing)"


def assert_symlink_points_to(
    symlink_path: Path,
    target_path: Path,
    message: str | None = None,
) -> None:
    """Assert that a symlink points to a specific target.

    Args:
        symlink_path: Path to the symlink.
        target_path: Expected target path.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If symlink does not point to target.
    """
    if not symlink_path.exists():
        raise AssertionError(f"Symlink does not exist: {symlink_path}")

    if not symlink_path.is_symlink():
        raise AssertionError(f"Path is not a symlink: {symlink_path}")

    actual_target = symlink_path.resolve()
    expected_target = target_path.resolve()

    if message is None:
        message = (
            f"Symlink {symlink_path} does not point to expected target\n"
            f"Expected: {expected_target}\n"
            f"Actual: {actual_target}"
        )

    assert actual_target == expected_target, message


def assert_stdout_contains(
    result: ScriptResult,
    content: str,
    message: str | None = None,
) -> None:
    """Assert that script stdout contains specific content.

    Args:
        result: Script execution result.
        content: Content to search for in stdout.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If stdout does not contain the content.
    """
    if message is None:
        message = f"Stdout does not contain expected content\nExpected: {content!r}\nStdout: {result.stdout!r}"
    assert content in result.stdout, message


def assert_stderr_contains(
    result: ScriptResult,
    content: str,
    message: str | None = None,
) -> None:
    """Assert that script stderr contains specific content.

    Args:
        result: Script execution result.
        content: Content to search for in stderr.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If stderr does not contain the content.
    """
    if message is None:
        message = f"Stderr does not contain expected content\nExpected: {content!r}\nStderr: {result.stderr!r}"
    assert content in result.stderr, message


def assert_stdout_empty(result: ScriptResult, message: str | None = None) -> None:
    """Assert that script stdout is empty.

    Args:
        result: Script execution result.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If stdout is not empty.
    """
    if message is None:
        message = f"Stdout is not empty: {result.stdout!r}"
    assert not result.stdout or result.stdout.strip() == "", message


def assert_stderr_empty(result: ScriptResult, message: str | None = None) -> None:
    """Assert that script stderr is empty.

    Args:
        result: Script execution result.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If stderr is not empty.
    """
    if message is None:
        message = f"Stderr is not empty: {result.stderr!r}"
    assert not result.stderr or result.stderr.strip() == "", message


def assert_file_executable(file_path: Path, message: str | None = None) -> None:
    """Assert that a file has executable permissions.

    Args:
        file_path: Path to the file.
        message: Optional custom assertion message.

    Raises:
        AssertionError: If file is not executable.
    """
    if not file_path.exists():
        raise AssertionError(f"File does not exist: {file_path}")

    import os

    is_executable = os.access(file_path, os.X_OK)

    if message is None:
        message = f"File is not executable: {file_path}"

    assert is_executable, message


__all__ = [
    "assert_directory_exists",
    "assert_file_contains",
    "assert_file_created",
    "assert_file_executable",
    "assert_file_not_contains",
    "assert_git_repo_cloned",
    "assert_script_exit_code",
    "assert_script_failure",
    "assert_script_success",
    "assert_stderr_contains",
    "assert_stderr_empty",
    "assert_stdout_contains",
    "assert_stdout_empty",
    "assert_symlink_points_to",
]

# 🧪✅🔚
