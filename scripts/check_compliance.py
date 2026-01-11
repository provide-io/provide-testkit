#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Check header and footer compliance of Python files in repositories.

This script analyzes Python files to verify:
- SPDX headers are present
- Footer emojis are present
- Compliance statistics per repository

Usage:
    # Check single repository
    python check_compliance.py /path/to/repo

    # Check multiple repositories
    python check_compliance.py /path/to/repo1 /path/to/repo2

    # Check all repos in parent directory
    python check_compliance.py --all /path/to/parent"""

import argparse
import os
from pathlib import Path
import sys
from typing import NamedTuple

# Directories to exclude when scanning
EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "workenv",
    ".git",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".hypothesis",
    ".eggs",
    ".tox",
    ".uv-cache",
    ".uv",
    ".cache",
    "node_modules",
}


class ComplianceStats(NamedTuple):
    """Statistics for a repository's compliance."""

    repo_name: str
    total_files: int
    files_with_spdx: int
    files_with_footer: int
    files_fully_compliant: int


def find_python_files(directory: Path) -> list[Path]:
    """
    Recursively find all Python files in a directory, excluding build/cache directories.

    Args:
        directory: Root directory to search

    Returns:
        List of Python file paths
    """
    python_files = []

    for root, dirs, files in os.walk(directory):
        # Remove excluded directories from the search
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return sorted(python_files)


def check_file_compliance(filepath: Path) -> tuple[bool, bool]:
    """
    Check if a file has SPDX header and footer.

    Args:
        filepath: Path to Python file

    Returns:
        Tuple of (has_spdx, has_footer)
    """
    try:
        content = filepath.read_text(encoding="utf-8")
        lines = content.splitlines()
    except OSError:
        return False, False

    if not lines:
        return False, False

    # Check for SPDX header in first 10 lines
    has_spdx = False
    first_10 = "\n".join(lines[:10])
    if "SPDX-FileCopyrightText" in first_10 and "SPDX-License-Identifier" in first_10:
        has_spdx = True

    # Check for footer in last 10 lines
    has_footer = False
    last_10 = "\n".join(lines[-10:])
    footer_emojis = [
        "🏗️",
        "🐍",
        "🧱",
        "🐝",
        "📁",
        "🍽️",
        "📖",
        "🧪",
        "✅",
        "🧩",
        "🔧",
        "🌊",
        "🪢",
        "🔌",
        "📞",
        "📄",
        "⚙️",
        "🥣",
        "🔬",
        "🔼",
        "🌶️",
        "📦",
        "🧰",
        "🌍",
        "🪄",
        "🔚",
    ]
    if any(emoji in last_10 for emoji in footer_emojis):
        has_footer = True

    return has_spdx, has_footer


def check_repository(repo_path: Path) -> ComplianceStats:
    """
    Check compliance for all Python files in a repository.

    Args:
        repo_path: Path to repository

    Returns:
        ComplianceStats for the repository
    """
    python_files = find_python_files(repo_path)

    if not python_files:
        return ComplianceStats(
            repo_name=repo_path.name,
            total_files=0,
            files_with_spdx=0,
            files_with_footer=0,
            files_fully_compliant=0,
        )

    spdx_count = 0
    footer_count = 0
    fully_compliant = 0

    for filepath in python_files:
        has_spdx, has_footer = check_file_compliance(filepath)

        if has_spdx:
            spdx_count += 1
        if has_footer:
            footer_count += 1
        if has_spdx and has_footer:
            fully_compliant += 1

    return ComplianceStats(
        repo_name=repo_path.name,
        total_files=len(python_files),
        files_with_spdx=spdx_count,
        files_with_footer=footer_count,
        files_fully_compliant=fully_compliant,
    )


def print_compliance_report(stats: list[ComplianceStats]) -> None:
    """
    Print a formatted compliance report.

    Args:
        stats: List of ComplianceStats to report
    """
    if not stats:
        print("No repositories to report")
        return

    # Print header
    print(f"{'Repository':<25} {'Total':<7} {'SPDX':<12} {'Footer':<12} {'Full':<12}")
    print("-" * 80)

    total_files = 0
    total_spdx = 0
    total_footer = 0
    total_compliant = 0

    for stat in stats:
        if stat.total_files == 0:
            continue

        spdx_pct = (100 * stat.files_with_spdx // stat.total_files) if stat.total_files > 0 else 0
        footer_pct = (100 * stat.files_with_footer // stat.total_files) if stat.total_files > 0 else 0
        full_pct = (100 * stat.files_fully_compliant // stat.total_files) if stat.total_files > 0 else 0

        print(
            f"{stat.repo_name:<25} "
            f"{stat.total_files:<7} "
            f"{stat.files_with_spdx:>4} ({spdx_pct:>3}%) "
            f"{stat.files_with_footer:>4} ({footer_pct:>3}%) "
            f"{stat.files_fully_compliant:>4} ({full_pct:>3}%)"
        )

        total_files += stat.total_files
        total_spdx += stat.files_with_spdx
        total_footer += stat.files_with_footer
        total_compliant += stat.files_fully_compliant

    # Print summary
    if len(stats) > 1:
        print("-" * 80)
        spdx_pct = (100 * total_spdx // total_files) if total_files > 0 else 0
        footer_pct = (100 * total_footer // total_files) if total_files > 0 else 0
        full_pct = (100 * total_compliant // total_files) if total_files > 0 else 0

        print(
            f"{'TOTAL':<25} "
            f"{total_files:<7} "
            f"{total_spdx:>4} ({spdx_pct:>3}%) "
            f"{total_footer:>4} ({footer_pct:>3}%) "
            f"{total_compliant:>4} ({full_pct:>3}%)"
        )


def parse_args() -> argparse.Namespace:
    """Build argument parser for CLI use."""
    parser = argparse.ArgumentParser(
        description="Check header and footer compliance of Python files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("repositories", nargs="*", help="Repository paths to check")
    parser.add_argument("--all", metavar="PARENT_DIR", help="Check all subdirectories in parent directory")
    return parser.parse_args()


def collect_repositories(args: argparse.Namespace) -> list[Path]:
    """Resolve target repositories based on CLI arguments."""
    if args.all:
        parent = Path(args.all).resolve()
        if not parent.exists() or not parent.is_dir():
            print(f"Error: {args.all} is not a valid directory", file=sys.stderr)
            sys.exit(1)

        return [item for item in parent.iterdir() if item.is_dir() and not item.name.startswith(".")]

    if args.repositories:
        repos: list[Path] = []
        for repo in args.repositories:
            repo_path = Path(repo).resolve()
            if not repo_path.exists():
                print(f"Warning: {repo} does not exist, skipping", file=sys.stderr)
                continue
            if not repo_path.is_dir():
                print(f"Warning: {repo} is not a directory, skipping", file=sys.stderr)
                continue
            repos.append(repo_path)
        return repos

    return [Path.cwd()]


def main() -> None:
    args = parse_args()
    repos_to_check = collect_repositories(args)

    if not repos_to_check:
        print("No repositories to check", file=sys.stderr)
        sys.exit(1)

    # Check each repository
    all_stats = [check_repository(repo_path) for repo_path in sorted(repos_to_check)]

    # Print report
    print_compliance_report(all_stats)


if __name__ == "__main__":
    main()

# 🧪✅🔚
