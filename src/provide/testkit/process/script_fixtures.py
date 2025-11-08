#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Bash script testing fixtures and utilities.

Provides fixtures and utilities for testing bash scripts with
subprocess execution, output capture, environment isolation,
and workspace management.
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from pathlib import Path
import shutil
import subprocess

import attrs
import pytest

from provide.foundation.file import temp_dir
from provide.foundation.process import run


@attrs.define
class ScriptResult:
    """Result of a bash script execution.

    Attributes:
        returncode: Exit code from the script.
        stdout: Standard output as string.
        stderr: Standard error as string.
        command: Command that was executed.
        cwd: Working directory where script was executed.
        duration: Execution duration in seconds.
    """

    returncode: int
    stdout: str
    stderr: str
    command: str | list[str]
    cwd: Path
    duration: float = 0.0

    @property
    def success(self) -> bool:
        """Check if script succeeded (exit code 0).

        Returns:
            True if returncode is 0, False otherwise.
        """
        return self.returncode == 0

    @property
    def failed(self) -> bool:
        """Check if script failed (non-zero exit code).

        Returns:
            True if returncode is non-zero, False otherwise.
        """
        return self.returncode != 0


@attrs.define
class ScriptExecutionContext:
    """Context for executing bash scripts in isolation.

    Provides a temporary workspace with environment variable
    control and automatic cleanup.

    Attributes:
        workspace: Path to temporary workspace directory.
        env: Environment variables for script execution.
        timeout: Timeout in seconds for script execution.
    """

    workspace: Path
    env: dict[str, str] = attrs.field(factory=dict)
    timeout: int = 60

    def run_script(
        self,
        script_path: Path | str,
        args: list[str] | None = None,
        check: bool = False,
    ) -> ScriptResult:
        """Execute a bash script in the isolated workspace.

        Args:
            script_path: Path to the bash script to execute.
            args: Optional arguments to pass to the script.
            check: If True, raise exception on non-zero exit code.

        Returns:
            ScriptResult with execution details.

        Raises:
            subprocess.CalledProcessError: If check=True and script fails.
            subprocess.TimeoutExpired: If execution exceeds timeout.
        """
        script_path = Path(script_path)
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        command = ["bash", str(script_path)]
        if args:
            command.extend(args)

        import time

        start_time = time.time()

        try:
            result = run(
                command,
                cwd=self.workspace,
                env=self.env if self.env else None,
                timeout=self.timeout,
                check=check,
            )
            duration = time.time() - start_time

            return ScriptResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=command,
                cwd=self.workspace,
                duration=duration,
            )
        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            return ScriptResult(
                returncode=e.returncode,
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                command=command,
                cwd=self.workspace,
                duration=duration,
            )

    def run_command(
        self,
        command: str | list[str],
        check: bool = False,
    ) -> ScriptResult:
        """Execute a shell command in the isolated workspace.

        Args:
            command: Shell command to execute (string or list).
            check: If True, raise exception on non-zero exit code.

        Returns:
            ScriptResult with execution details.

        Raises:
            subprocess.CalledProcessError: If check=True and command fails.
            subprocess.TimeoutExpired: If execution exceeds timeout.
        """
        import time

        start_time = time.time()

        try:
            result = run(
                command,
                cwd=self.workspace,
                env=self.env if self.env else None,
                timeout=self.timeout,
                check=check,
                shell=isinstance(command, str),
            )
            duration = time.time() - start_time

            return ScriptResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=command,
                cwd=self.workspace,
                duration=duration,
            )
        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            return ScriptResult(
                returncode=e.returncode,
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                command=command,
                cwd=self.workspace,
                duration=duration,
            )

    def create_file(self, name: str, content: str = "") -> Path:
        """Create a file in the workspace.

        Args:
            name: File name (can include subdirectories).
            content: File content.

        Returns:
            Path to the created file.
        """
        file_path = self.workspace / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path

    def create_directory(self, name: str) -> Path:
        """Create a directory in the workspace.

        Args:
            name: Directory name (can be nested path).

        Returns:
            Path to the created directory.
        """
        dir_path = self.workspace / name
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def file_exists(self, name: str) -> bool:
        """Check if a file or directory exists in workspace.

        Args:
            name: File or directory name.

        Returns:
            True if path exists, False otherwise.
        """
        return (self.workspace / name).exists()

    def read_file(self, name: str) -> str:
        """Read a file from the workspace.

        Args:
            name: File name.

        Returns:
            File contents as string.

        Raises:
            FileNotFoundError: If file does not exist.
        """
        return (self.workspace / name).read_text()

    def init_git_repo(self) -> None:
        """Initialize a git repository in the workspace.

        Raises:
            RuntimeError: If git is not available.
        """
        if not shutil.which("git"):
            raise RuntimeError("git command not found")

        run(["git", "init"], cwd=self.workspace, check=True)
        run(["git", "config", "user.email", "test@example.com"], cwd=self.workspace, check=True)
        run(["git", "config", "user.name", "Test User"], cwd=self.workspace, check=True)


@pytest.fixture
def script_execution_context() -> Generator[ScriptExecutionContext, None, None]:
    """Create an isolated script execution context.

    Provides a temporary workspace directory with utilities
    for running bash scripts in isolation.

    Yields:
        ScriptExecutionContext with temporary workspace.
    """
    with temp_dir(prefix="script_test_") as workspace:
        yield ScriptExecutionContext(workspace=workspace)


@pytest.fixture
def isolated_workspace() -> Generator[Path, None, None]:
    """Create an isolated temporary workspace directory.

    Yields:
        Path to temporary workspace directory.
    """
    with temp_dir(prefix="workspace_test_") as workspace:
        yield workspace


@pytest.fixture
def git_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace with git initialized.

    Yields:
        Path to git-initialized workspace directory.
    """
    with temp_dir(prefix="git_test_") as workspace:
        if not shutil.which("git"):
            pytest.skip("git command not available")

        run(["git", "init"], cwd=workspace, check=True)
        run(["git", "config", "user.email", "test@example.com"], cwd=workspace, check=True)
        run(["git", "config", "user.name", "Test User"], cwd=workspace, check=True)

        yield workspace


@pytest.fixture
def bash_script_runner(
    isolated_workspace: Path,
) -> Callable[[Path | str, list[str] | None, dict[str, str] | None], ScriptResult]:
    """Create a bash script runner fixture.

    Returns:
        Function that executes bash scripts and returns results.

    Example:
        def test_my_script(bash_script_runner):
            result = bash_script_runner("path/to/script.sh", args=["--flag"])
            assert result.success
            assert "expected output" in result.stdout
    """

    def _run_script(
        script_path: Path | str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 60,
    ) -> ScriptResult:
        """Execute a bash script.

        Args:
            script_path: Path to bash script.
            args: Optional script arguments.
            env: Optional environment variables.
            timeout: Timeout in seconds.

        Returns:
            ScriptResult with execution details.
        """
        context = ScriptExecutionContext(
            workspace=isolated_workspace,
            env=env or {},
            timeout=timeout,
        )
        return context.run_script(script_path, args=args)

    return _run_script


@pytest.fixture
def mock_git_repo() -> Callable[[Path, str], Path]:
    """Create a factory for mock git repositories.

    Returns:
        Function that creates a mock git repo with commits.

    Example:
        def test_git_clone(mock_git_repo, isolated_workspace):
            repo = mock_git_repo(isolated_workspace, "test-repo")
            # repo is a path to a git repository with initial commit
    """

    def _create_repo(base_dir: Path, repo_name: str, add_commits: bool = True) -> Path:
        """Create a mock git repository.

        Args:
            base_dir: Directory to create repo in.
            repo_name: Name of the repository.
            add_commits: If True, add an initial commit.

        Returns:
            Path to the created git repository.
        """
        if not shutil.which("git"):
            pytest.skip("git command not available")

        repo_path = base_dir / repo_name
        repo_path.mkdir(parents=True, exist_ok=True)

        run(["git", "init"], cwd=repo_path, check=True)
        run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
        run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)

        if add_commits:
            readme = repo_path / "README.md"
            readme.write_text(f"# {repo_name}\n\nTest repository.")
            run(["git", "add", "README.md"], cwd=repo_path, check=True)
            run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

        return repo_path

    return _create_repo


__all__ = [
    "ScriptExecutionContext",
    "ScriptResult",
    "bash_script_runner",
    "git_workspace",
    "isolated_workspace",
    "mock_git_repo",
    "script_execution_context",
]

# 🧪✅🔚
