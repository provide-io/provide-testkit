"""
Consolidated Temporary File Utilities.

Provides unified utilities for creating and managing temporary files
and directories in tests with automatic cleanup capabilities.
"""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Any, TextIO

from provide.foundation.file import temp_file as foundation_temp_file


class TempFileManager:
    """Manager for temporary files and directories with automatic cleanup."""

    def __init__(self) -> None:
        """Initialize temp file manager."""
        self._temp_paths: list[Path] = []

    def create_file(
        self,
        content: str = "",
        suffix: str = "",
        prefix: str = "test_",
        text: bool = True,
    ) -> Path:
        """Create a temporary file with content.

        Args:
            content: Content to write to the file.
            suffix: File extension (e.g., ".txt", ".json").
            prefix: File name prefix.
            text: Whether to open in text mode.

        Returns:
            Path to the created temporary file.
        """
        with foundation_temp_file(suffix=suffix, prefix=prefix, text=text, cleanup=False) as path:
            if content:
                if text:
                    path.write_text(content)
                else:
                    path.write_bytes(content.encode() if isinstance(content, str) else content)

            self._temp_paths.append(path)
            return path

    def create_binary_file(
        self,
        content: bytes = b"",
        suffix: str = "",
        prefix: str = "test_",
    ) -> Path:
        """Create a temporary binary file with content.

        Args:
            content: Binary content to write to the file.
            suffix: File extension.
            prefix: File name prefix.

        Returns:
            Path to the created temporary file.
        """
        with foundation_temp_file(suffix=suffix, prefix=prefix, text=False, cleanup=False) as path:
            if content:
                path.write_bytes(content)

            self._temp_paths.append(path)
            return path

    def create_json_file(self, data: Any, suffix: str = ".json", prefix: str = "test_") -> Path:
        """Create a temporary JSON file with data.

        Args:
            data: Data to serialize as JSON.
            suffix: File extension (defaults to .json).
            prefix: File name prefix.

        Returns:
            Path to the created JSON file.
        """
        import json

        content = json.dumps(data, indent=2)
        return self.create_file(content=content, suffix=suffix, prefix=prefix)

    def create_yaml_file(self, data: Any, suffix: str = ".yaml", prefix: str = "test_") -> Path:
        """Create a temporary YAML file with data.

        Args:
            data: Data to serialize as YAML.
            suffix: File extension (defaults to .yaml).
            prefix: File name prefix.

        Returns:
            Path to the created YAML file.

        Raises:
            ImportError: If PyYAML is not available.
        """
        try:
            import yaml
        except ImportError as e:
            raise ImportError("PyYAML required for YAML file creation") from e

        content = yaml.safe_dump(data, default_flow_style=False)
        return self.create_file(content=content, suffix=suffix, prefix=prefix)

    def create_toml_file(self, data: Any, suffix: str = ".toml", prefix: str = "test_") -> Path:
        """Create a temporary TOML file with data.

        Args:
            data: Data to serialize as TOML.
            suffix: File extension (defaults to .toml).
            prefix: File name prefix.

        Returns:
            Path to the created TOML file.

        Raises:
            ImportError: If tomli_w is not available.
        """
        try:
            import tomli_w
        except ImportError as e:
            raise ImportError("tomli_w required for TOML file creation") from e

        content = tomli_w.dumps(data)
        return self.create_file(content=content, suffix=suffix, prefix=prefix)

    def create_directory(self, prefix: str = "test_") -> Path:
        """Create a temporary directory.

        Args:
            prefix: Directory name prefix.

        Returns:
            Path to the created temporary directory.
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self._temp_paths.append(temp_dir)
        return temp_dir

    def create_file_in_dir(
        self,
        directory: Path,
        name: str,
        content: str = "",
        text: bool = True,
    ) -> Path:
        """Create a file in an existing directory.

        Args:
            directory: Directory to create the file in.
            name: File name.
            content: Content to write to the file.
            text: Whether to open in text mode.

        Returns:
            Path to the created file.
        """
        file_path = directory / name
        if text:
            file_path.write_text(content)
        else:
            file_path.write_bytes(content.encode() if isinstance(content, str) else content)

        # Don't track this file separately since the directory will be cleaned up
        return file_path

    def create_directory_structure(self, structure: dict[str, Any], base_dir: Path | None = None) -> Path:
        """Create a directory structure from a nested dictionary.

        Args:
            structure: Dictionary describing the structure.
                      Keys are names, values are either strings (file content)
                      or dicts (subdirectories).
            base_dir: Base directory to create structure in. If None, creates a new temp dir.

        Returns:
            Path to the base directory.

        Example:
            structure = {
                "config.json": '{"debug": true}',
                "src": {
                    "main.py": "print('hello')",
                    "utils": {
                        "__init__.py": "",
                        "helpers.py": "def helper(): pass"
                    }
                }
            }
        """
        if base_dir is None:
            base_dir = self.create_directory()

        for name, content in structure.items():
            path = base_dir / name
            if isinstance(content, dict):
                # Create subdirectory
                path.mkdir(exist_ok=True)
                self.create_directory_structure(content, path)
            else:
                # Create file
                path.write_text(str(content))

        return base_dir

    def cleanup(self) -> None:
        """Clean up all managed temporary files and directories."""
        for path in self._temp_paths:
            if path.exists():
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil

                    shutil.rmtree(path)

        self._temp_paths.clear()

    def __enter__(self) -> TempFileManager:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and cleanup."""
        self.cleanup()


# Convenience functions for quick temporary file creation
def create_temp_file(
    content: str = "",
    suffix: str = "",
    prefix: str = "test_",
    cleanup: bool = True,
) -> Path:
    """Create a temporary file with content.

    Args:
        content: Content to write to the file.
        suffix: File extension.
        prefix: File name prefix.
        cleanup: If True, the file will be managed by Foundation's cleanup.

    Returns:
        Path to the created temporary file.
    """
    with foundation_temp_file(suffix=suffix, prefix=prefix, text=True, cleanup=cleanup) as path:
        if content:
            path.write_text(content)
        if cleanup:
            return path
        # For non-cleanup mode, return the path but don't use context manager
        pass

    # If cleanup=False, we need to create the file manually
    fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, text=True)
    try:
        with os.fdopen(fd, "w") as f:
            if content:
                f.write(content)
    except Exception:
        os.unlink(temp_path)
        raise

    return Path(temp_path)


def create_temp_dir(prefix: str = "test_") -> Path:
    """Create a temporary directory.

    Args:
        prefix: Directory name prefix.

    Returns:
        Path to the created temporary directory.
    """
    return Path(tempfile.mkdtemp(prefix=prefix))


__all__ = [
    "TempFileManager",
    "create_temp_file",
    "create_temp_dir",
]