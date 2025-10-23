"""Git integration for mutation testing."""

from __future__ import annotations

from pathlib import Path
import subprocess

from provide.foundation import logger


def get_changed_files(
    base_path: Path | None = None, base_branch: str = "main", include_untracked: bool = False
) -> list[str]:
    """Get list of Python files changed since base branch.

    Args:
        base_path: Base directory (default: current directory)
        base_branch: Branch to compare against (default: main)
        include_untracked: Include untracked files (default: False)

    Returns:
        List of changed Python file paths relative to base_path
    """
    log = logger.get_logger(__name__)
    base_path = base_path or Path.cwd()

    try:
        # Get changed files
        cmd = ["git", "diff", "--name-only", f"{base_branch}...HEAD"]
        result = subprocess.run(cmd, cwd=base_path, capture_output=True, text=True, check=True)

        changed_files = result.stdout.strip().split("\n")

        # Add untracked files if requested
        if include_untracked:
            cmd = ["git", "ls-files", "--others", "--exclude-standard"]
            result = subprocess.run(cmd, cwd=base_path, capture_output=True, text=True, check=True)
            untracked = result.stdout.strip().split("\n")
            changed_files.extend(untracked)

        # Filter to Python files only
        python_files = [f for f in changed_files if f.endswith(".py") and f]

        # Exclude test files and generated code
        filtered_files = []
        for file in python_files:
            if any(pattern in file for pattern in ["test_", "/tests/", "_pb2.py", "/generated/"]):
                continue
            filtered_files.append(file)

        log.debug(f"Found {len(filtered_files)} changed Python files to mutate")
        return filtered_files

    except subprocess.CalledProcessError as e:
        log.warning(f"Failed to get changed files: {e}")
        return []
    except Exception as e:
        log.error(f"Error getting changed files: {e}")
        return []


def get_affected_modules(changed_files: list[str], base_path: Path | None = None) -> list[Path]:
    """Convert changed file paths to module paths.

    Args:
        changed_files: List of changed file paths
        base_path: Base directory (default: current directory)

    Returns:
        List of Path objects for affected modules
    """
    base_path = base_path or Path.cwd()
    modules = []

    for file in changed_files:
        file_path = base_path / file
        if file_path.exists():
            modules.append(file_path)

    return modules


def is_git_repo(path: Path | None = None) -> bool:
    """Check if path is inside a git repository.

    Args:
        path: Path to check (default: current directory)

    Returns:
        True if inside a git repo, False otherwise
    """
    path = path or Path.cwd()

    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
            check=True,
            timeout=5,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def get_current_branch(path: Path | None = None) -> str | None:
    """Get current git branch name.

    Args:
        path: Path to check (default: current directory)

    Returns:
        Branch name or None if not in a git repo
    """
    path = path or Path.cwd()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
