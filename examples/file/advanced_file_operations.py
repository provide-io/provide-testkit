#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Example: Advanced File Operations Testing

This example demonstrates advanced file and directory testing patterns
using provide-testkit fixtures for complex file system scenarios.

Key fixtures used:
- temp_directory: Isolated directory for file operations
- Various file testing patterns and edge cases

Learning objectives:
- Test complex file system operations
- Handle file permissions and ownership scenarios
- Test file watching and monitoring
- Validate file content and metadata
- Test concurrent file operations"""

import json
from pathlib import Path
import shutil
import time

import pytest


# Example classes for file operations
class FileManager:
    """Example file management class."""

    def __init__(self, base_directory: Path) -> None:
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(parents=True, exist_ok=True)

    def create_file_with_content(self, filename: str, content: str, encoding: str = "utf-8") -> Path:
        """Create a file with specific content."""
        file_path = self.base_directory / filename
        file_path.write_text(content, encoding=encoding)
        return file_path

    def create_binary_file(self, filename: str, data: bytes) -> Path:
        """Create a binary file."""
        file_path = self.base_directory / filename
        file_path.write_bytes(data)
        return file_path

    def copy_file(self, source: Path, destination: str) -> Path:
        """Copy a file to the base directory."""
        dest_path = self.base_directory / destination
        shutil.copy2(source, dest_path)
        return dest_path

    def move_file(self, source: str, destination: str) -> Path:
        """Move a file within the base directory."""
        source_path = self.base_directory / source
        dest_path = self.base_directory / destination
        source_path.rename(dest_path)
        return dest_path

    def delete_file(self, filename: str) -> bool:
        """Delete a file if it exists."""
        file_path = self.base_directory / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def set_permissions(self, filename: str, mode: int) -> None:
        """Set file permissions."""
        file_path = self.base_directory / filename
        file_path.chmod(mode)

    def get_file_info(self, filename: str) -> dict[str, any]:
        """Get comprehensive file information."""
        file_path = self.base_directory / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        stat_info = file_path.stat()
        return {
            "size": stat_info.st_size,
            "modified_time": stat_info.st_mtime,
            "permissions": oct(stat_info.st_mode)[-3:],
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir(),
            "exists": True,
        }


class ConfigManager:
    """Example configuration manager that works with multiple file formats."""

    def __init__(self, config_directory: Path) -> None:
        self.config_directory = Path(config_directory)
        self.config_directory.mkdir(parents=True, exist_ok=True)

    def save_json_config(self, name: str, config: dict[str, any]) -> Path:
        """Save configuration as JSON."""
        config_path = self.config_directory / f"{name}.json"
        config_path.write_text(json.dumps(config, indent=2))
        return config_path

    def load_json_config(self, name: str) -> dict[str, any]:
        """Load JSON configuration."""
        config_path = self.config_directory / f"{name}.json"
        return json.loads(config_path.read_text())

    def save_text_config(self, name: str, content: str) -> Path:
        """Save configuration as plain text."""
        config_path = self.config_directory / f"{name}.txt"
        config_path.write_text(content)
        return config_path

    def load_text_config(self, name: str) -> str:
        """Load text configuration."""
        config_path = self.config_directory / f"{name}.txt"
        return config_path.read_text()

    def backup_config(self, name: str) -> Path:
        """Create a backup of a configuration file."""
        original = self.config_directory / f"{name}.json"
        backup = self.config_directory / f"{name}.backup.json"
        shutil.copy2(original, backup)
        return backup

    def list_configs(self) -> list[str]:
        """List all configuration files."""
        configs = []
        for file_path in self.config_directory.glob("*.json"):
            if not file_path.name.endswith(".backup.json"):
                configs.append(file_path.stem)
        return sorted(configs)


# Test Patterns


def test_basic_file_operations(temp_directory: Path) -> None:
    """Pattern 1: Basic file creation and manipulation."""
    file_manager = FileManager(temp_directory)

    # Test file creation
    test_file = file_manager.create_file_with_content("test.txt", "Hello, World!")
    assert test_file.exists()
    assert test_file.read_text() == "Hello, World!"

    # Test file info
    info = file_manager.get_file_info("test.txt")
    assert info["size"] == len("Hello, World!")
    assert info["is_file"] is True
    assert info["is_directory"] is False

    # Test file deletion
    assert file_manager.delete_file("test.txt") is True
    assert not test_file.exists()
    assert file_manager.delete_file("nonexistent.txt") is False


def test_binary_file_operations(temp_directory: Path) -> None:
    """Pattern 2: Binary file handling."""
    file_manager = FileManager(temp_directory)

    # Create binary data
    binary_data = b"\x00\x01\x02\x03\xff\xfe\xfd"
    binary_file = file_manager.create_binary_file("data.bin", binary_data)

    # Verify binary content
    assert binary_file.read_bytes() == binary_data
    assert binary_file.stat().st_size == len(binary_data)

    # Test with larger binary data
    large_data = bytes(range(256)) * 100  # 25.6KB of data
    large_file = file_manager.create_binary_file("large.bin", large_data)
    assert large_file.read_bytes() == large_data


def test_file_permissions(temp_directory: Path) -> None:
    """Pattern 3: File permissions testing."""
    file_manager = FileManager(temp_directory)

    # Create test file
    test_file = file_manager.create_file_with_content("permissions_test.txt", "test content")

    # Test readable permissions
    file_manager.set_permissions("permissions_test.txt", 0o644)
    info = file_manager.get_file_info("permissions_test.txt")
    assert info["permissions"] == "644"

    # Test executable permissions
    file_manager.set_permissions("permissions_test.txt", 0o755)
    info = file_manager.get_file_info("permissions_test.txt")
    assert info["permissions"] == "755"

    # Verify file is still readable
    assert test_file.read_text() == "test content"


def test_file_copying_and_moving(temp_directory: Path) -> None:
    """Pattern 4: File copying and moving operations."""
    file_manager = FileManager(temp_directory)

    # Create source file
    source_content = "Original content for copying and moving tests"
    source_file = file_manager.create_file_with_content("source.txt", source_content)

    # Test copying
    copied_file = file_manager.copy_file(source_file, "copied.txt")
    assert copied_file.exists()
    assert copied_file.read_text() == source_content
    assert source_file.exists()  # Original should still exist

    # Test moving
    moved_file = file_manager.move_file("copied.txt", "moved.txt")
    assert moved_file.exists()
    assert moved_file.read_text() == source_content
    assert not (temp_directory / "copied.txt").exists()  # Original copy should be gone


def test_directory_structure_creation(temp_directory: Path) -> None:
    """Pattern 5: Complex directory structure creation."""

    # Create nested directory structure
    structure = {
        "config": ["app.json", "database.json"],
        "data": ["users.csv", "logs.txt"],
        "scripts": ["deploy.sh", "backup.py"],
        "docs": ["README.md", "API.md"],
    }

    for directory, files in structure.items():
        dir_path = temp_directory / directory
        dir_path.mkdir()

        for filename in files:
            file_path = dir_path / filename
            file_path.write_text(f"Content of {filename}")

    # Verify structure
    for directory, files in structure.items():
        dir_path = temp_directory / directory
        assert dir_path.is_dir()

        for filename in files:
            file_path = dir_path / filename
            assert file_path.exists()
            assert file_path.read_text() == f"Content of {filename}"


def test_configuration_management(temp_directory: Path) -> None:
    """Pattern 6: Configuration file management."""
    config_manager = ConfigManager(temp_directory / "configs")

    # Test JSON configuration
    app_config = {
        "database": {"host": "localhost", "port": 5432},
        "api": {"timeout": 30, "retries": 3},
        "features": ["auth", "logging", "metrics"],
    }

    json_path = config_manager.save_json_config("app", app_config)
    assert json_path.exists()

    loaded_config = config_manager.load_json_config("app")
    assert loaded_config == app_config

    # Test text configuration
    text_config = """
database_host=localhost
database_port=5432
api_timeout=30
features=auth,logging,metrics
    """.strip()

    config_manager.save_text_config("app_text", text_config)
    loaded_text = config_manager.load_text_config("app_text")
    assert loaded_text == text_config

    # Test configuration listing
    configs = config_manager.list_configs()
    assert "app" in configs

    # Test backup
    backup_path = config_manager.backup_config("app")
    assert backup_path.exists()
    backup_config = json.loads(backup_path.read_text())
    assert backup_config == app_config


def test_file_encoding_handling(temp_directory: Path) -> None:
    """Pattern 7: Different file encodings."""
    file_manager = FileManager(temp_directory)

    # Test UTF-8 (default)
    utf8_content = "Hello, UTF-8! Привет, мир!"
    utf8_file = file_manager.create_file_with_content("utf8.txt", utf8_content, "utf-8")
    assert utf8_file.read_text(encoding="utf-8") == utf8_content

    # Test ASCII
    ascii_content = "Hello, World!"
    ascii_file = file_manager.create_file_with_content("ascii.txt", ascii_content, "ascii")
    assert ascii_file.read_text(encoding="ascii") == ascii_content

    # Test handling of encoding errors
    with pytest.raises(UnicodeEncodeError):
        file_manager.create_file_with_content("invalid.txt", "Hello, 世界!", "ascii")


def test_large_file_operations(temp_directory: Path) -> None:
    """Pattern 8: Large file handling."""
    file_manager = FileManager(temp_directory)

    # Create a larger text file (1MB)
    large_content = "This is a test line.\n" * 50000  # Approximately 1MB
    large_file = file_manager.create_file_with_content("large.txt", large_content)

    # Verify size
    info = file_manager.get_file_info("large.txt")
    assert info["size"] > 1000000  # At least 1MB

    # Test reading chunks
    with large_file.open() as f:
        first_chunk = f.read(1000)
        assert first_chunk.startswith("This is a test line.")

    # Test file truncation
    with large_file.open("r+") as f:
        f.truncate(1000)

    # Verify truncation
    truncated_content = large_file.read_text()
    assert len(truncated_content) == 1000


def test_concurrent_file_access_simulation(temp_directory: Path) -> None:
    """Pattern 9: Simulating concurrent file access."""
    file_manager = FileManager(temp_directory)

    # Create a shared file
    shared_file = file_manager.create_file_with_content("shared.txt", "initial content")

    # Simulate multiple processes accessing the file
    # (In real tests, you might use threading or multiprocessing)
    results = []

    for i in range(5):
        # Read current content
        current = shared_file.read_text()
        results.append(f"Process {i}: {current}")

        # Append new content
        new_content = f"{current}\nLine from process {i}"
        shared_file.write_text(new_content)

    # Verify final state
    final_content = shared_file.read_text()
    assert "Process 0" in final_content
    assert "Process 4" in final_content
    assert final_content.count("\n") >= 5


def test_file_system_edge_cases(temp_directory: Path) -> None:
    """Pattern 10: Edge cases and error conditions."""
    file_manager = FileManager(temp_directory)

    # Test file with special characters in name
    special_name = "file with spaces & symbols!@#.txt"
    special_file = file_manager.create_file_with_content(special_name, "special content")
    assert special_file.exists()
    assert special_file.read_text() == "special content"

    # Test very long filename (within OS limits)
    long_name = "a" * 200 + ".txt"
    try:
        long_file = file_manager.create_file_with_content(long_name, "long name content")
        assert long_file.exists()
    except OSError:
        # Some filesystems have shorter limits
        pytest.skip("Filesystem doesn't support long filenames")

    # Test empty file
    empty_file = file_manager.create_file_with_content("empty.txt", "")
    assert empty_file.exists()
    assert empty_file.stat().st_size == 0

    # Test file that doesn't exist
    with pytest.raises(FileNotFoundError):
        file_manager.get_file_info("nonexistent.txt")


def test_symbolic_links_and_special_files(temp_directory: Path) -> None:
    """Pattern 11: Symbolic links and special file types."""
    file_manager = FileManager(temp_directory)

    # Create target file for symlink
    target_file = file_manager.create_file_with_content("target.txt", "target content")

    # Create symbolic link (skip if not supported)
    try:
        symlink_path = temp_directory / "symlink.txt"
        symlink_path.symlink_to(target_file)

        # Test symlink properties
        assert symlink_path.exists()
        assert symlink_path.is_symlink()
        assert symlink_path.read_text() == "target content"

        # Test symlink resolution
        assert symlink_path.resolve() == target_file.resolve()

    except (OSError, NotImplementedError):
        pytest.skip("Symbolic links not supported on this platform")


def test_file_timestamps_and_metadata(temp_directory: Path) -> None:
    """Pattern 12: File timestamps and metadata operations."""
    file_manager = FileManager(temp_directory)

    # Create file and record creation time
    test_file = file_manager.create_file_with_content("timestamp_test.txt", "initial")
    initial_info = file_manager.get_file_info("timestamp_test.txt")
    initial_mtime = initial_info["modified_time"]

    # Wait a bit and modify the file
    time.sleep(0.1)
    test_file.write_text("modified content")

    # Check that modification time changed
    updated_info = file_manager.get_file_info("timestamp_test.txt")
    updated_mtime = updated_info["modified_time"]

    assert updated_mtime > initial_mtime
    assert updated_info["size"] != initial_info["size"]


if __name__ == "__main__":
    print("=" * 65)
    print("This example demonstrates advanced file system testing:")
    print("")
    print("  • Basic file creation, reading, writing, deletion")
    print("  • Binary file handling")
    print("  • File permissions and metadata")
    print("  • File copying and moving")
    print("  • Complex directory structures")
    print("  • Configuration file management")
    print("  • Different file encodings")
    print("  • Large file operations")
    print("  • Concurrent access simulation")
    print("  • Edge cases and error conditions")
    print("  • Symbolic links and special files")
    print("  • Timestamps and metadata")
    print("")
    print("📋 Key Testing Patterns:")
    print("  ✓ Isolated file operations with temp_directory")
    print("  ✓ Binary and text file handling")
    print("  ✓ Permission and ownership testing")
    print("  ✓ Cross-platform file system operations")
    print("  ✓ Error condition testing")
    print("  ✓ Performance and scalability considerations")
    print("")
    print("🚀 Run with pytest to see examples:")
    print("   pytest examples/file/advanced_file_operations.py -v")
    print("")
    print("💡 Best Practices Demonstrated:")
    print("  • Always use temp_directory for isolation")
    print("  • Test both success and failure scenarios")
    print("  • Handle platform-specific limitations")
    print("  • Verify file metadata and properties")

# 🧪✅🔚
