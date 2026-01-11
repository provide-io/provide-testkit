#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Special file test fixtures.

Fixtures for creating specialized files like binary files, read-only files,
symbolic links, and executable files."""

from __future__ import annotations

from collections.abc import Callable, Generator
from pathlib import Path
import stat
import sys

import pytest

from provide.foundation.file import temp_file as foundation_temp_file
from provide.foundation.file.safe import safe_delete


@pytest.fixture
def binary_file() -> Generator[Path, None, None]:
    """
    Create a temporary binary file for testing.

    Yields:
        Path to a binary file containing sample binary data.
    """
    with foundation_temp_file(suffix=".bin", text=False, cleanup=False) as path:
        # Write some binary data
        path.write_bytes(
            b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09" + b"\xff\xfe\xfd\xfc\xfb\xfa\xf9\xf8\xf7\xf6"
        )

    yield path
    safe_delete(path, missing_ok=True)


@pytest.fixture
def readonly_file() -> Generator[Path, None, None]:
    """
    Create a read-only file for permission testing.

    Yields:
        Path to a read-only file.
    """
    with foundation_temp_file(suffix=".txt", text=True, cleanup=False) as path:
        path.write_text("Read-only content")

    # Make file read-only
    if sys.platform == "win32":
        # Windows: Only read-only bit is meaningful
        path.chmod(stat.S_IREAD)
    else:
        # Unix: Full permission control
        path.chmod(0o444)

    yield path

    # Restore write permission for cleanup
    if sys.platform == "win32":
        path.chmod(stat.S_IWRITE | stat.S_IREAD)
    else:
        path.chmod(0o644)
    safe_delete(path, missing_ok=True)


@pytest.fixture
def temp_symlink() -> Generator[Callable[..., Path], None, None]:
    """
    Create temporary symbolic links for testing.

    Returns:
        Function that creates symbolic links.
    """
    created_links: list[Path] = []

    def _make_symlink(target: Path | str, link_name: Path | str | None = None) -> Path:
        """
        Create a temporary symbolic link.

        Args:
            target: Target path for the symlink
            link_name: Optional link name (auto-generated if None)

        Returns:
            Path to created symlink

        Raises:
            pytest.skip: On Windows if symlinks require admin/developer mode
        """
        target = Path(target)

        if link_name is None:
            with foundation_temp_file(cleanup=True) as temp_path:
                link_name = Path(str(temp_path) + "_link")
        else:
            link_name = Path(link_name)

        # On Windows, symlink creation requires special permissions
        if sys.platform == "win32":
            try:
                link_name.symlink_to(target)
            except OSError as e:
                pytest.skip(f"Symlink creation requires admin rights or Developer Mode on Windows: {e}")
        else:
            link_name.symlink_to(target)

        created_links.append(link_name)

        return link_name

    yield _make_symlink

    # Cleanup
    for link in created_links:
        safe_delete(link, missing_ok=True)


@pytest.fixture
def temp_executable_file() -> Generator[Callable[..., Path], None, None]:
    """
    Create temporary executable files for testing.

    Returns:
        Function that creates executable files.
    """
    created_files: list[Path] = []

    def _make_executable(content: str | None = None, suffix: str | None = None) -> Path:
        """
        Create a temporary executable file.

        Args:
            content: Script content (platform-specific default if None)
            suffix: File suffix (platform-specific default if None)

        Returns:
            Path to created executable file
        """
        # Platform-specific defaults
        if content is None:
            content = "@echo off\necho test\n" if sys.platform == "win32" else "#!/bin/sh\necho 'test'\n"
        if suffix is None:
            suffix = ".bat" if sys.platform == "win32" else ".sh"

        with foundation_temp_file(suffix=suffix, text=True, cleanup=False) as path:
            path.write_text(content)

        # Make executable (Unix only - Windows uses file extension)
        if sys.platform != "win32":
            current = path.stat().st_mode
            path.chmod(current | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        created_files.append(path)
        return path

    yield _make_executable

    # Cleanup
    for path in created_files:
        safe_delete(path, missing_ok=True)


__all__ = [
    "binary_file",
    "readonly_file",
    "temp_executable_file",
    "temp_symlink",
]

# 🧪✅🔚
