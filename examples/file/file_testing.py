#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Example: File and Directory Testing Patterns

This example demonstrates common patterns for testing file operations,
directory structures, and file content validation using provide-testkit.

Key fixtures used:
- temp_directory: Temporary directory for test files
- test_files_structure: Predefined directory structure
- file_content_fixtures: Content generation utilities

Learning objectives:
- Test file creation and modification
- Validate directory structures
- Test file permissions and metadata
- Handle file content assertions"""

from collections.abc import Mapping
from pathlib import Path


def test_basic_file_operations(temp_directory: Path) -> None:
    """Test basic file creation and content operations."""
    # Arrange: Create test file
    test_file = temp_directory / "config.json"

    # Act: Write content to file
    test_content = '{"debug": true, "log_level": "INFO"}'
    test_file.write_text(test_content)

    # Assert: Verify file exists and content is correct
    assert test_file.exists()
    assert test_file.is_file()
    assert test_file.read_text() == test_content


def test_directory_structure_creation(temp_directory: Path) -> None:
    """Test creating and validating directory structures."""
    # Arrange: Define expected structure
    expected_dirs = ["src", "tests", "docs", "config"]
    expected_files = ["README.md", "pyproject.toml", ".gitignore"]

    # Act: Create directory structure
    for dir_name in expected_dirs:
        (temp_directory / dir_name).mkdir()

    for file_name in expected_files:
        (temp_directory / file_name).touch()

    # Assert: Verify structure exists
    for dir_name in expected_dirs:
        assert (temp_directory / dir_name).is_dir()

    for file_name in expected_files:
        assert (temp_directory / file_name).is_file()


def test_file_permissions(temp_directory: Path) -> None:
    """Test file permission handling."""
    # Arrange: Create executable script
    script_file = temp_directory / "setup.sh"
    script_content = "#!/bin/bash\necho 'Setting up environment...'"

    # Act: Create file and set permissions
    script_file.write_text(script_content)
    script_file.chmod(0o755)  # Make executable

    # Assert: Verify permissions
    assert script_file.exists()
    stat = script_file.stat()
    assert stat.st_mode & 0o777 == 0o755


def test_nested_directory_operations(temp_directory: Path) -> None:
    """Test operations with nested directory structures."""
    # Arrange: Create nested structure
    nested_path = temp_directory / "project" / "src" / "package"
    nested_path.mkdir(parents=True)

    # Act: Create files in nested structure
    init_file = nested_path / "__init__.py"
    init_file.write_text('"""Package initialization."""')

    module_file = nested_path / "module.py"
    module_file.write_text('def hello():\n    return "Hello, World!"')

    # Assert: Verify nested structure
    assert nested_path.exists()
    assert init_file.exists()
    assert module_file.exists()

    # Verify parent directories
    assert (temp_directory / "project").exists()
    assert (temp_directory / "project" / "src").exists()


def test_file_content_patterns(temp_directory: Path) -> None:
    """Test common file content validation patterns."""
    # Arrange: Create various file types
    json_file = temp_directory / "data.json"
    csv_file = temp_directory / "data.csv"
    log_file = temp_directory / "app.log"

    # Act: Write different content types
    json_file.write_text('{"items": [1, 2, 3], "total": 3}')
    csv_file.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA")
    log_file.write_text("INFO: Application started\nERROR: Database connection failed")

    # Assert: Verify content patterns
    json_content = json_file.read_text()
    assert '"items"' in json_content
    assert '"total": 3' in json_content

    csv_content = csv_file.read_text()
    assert csv_content.startswith("name,age,city")
    assert "Alice,30,NYC" in csv_content

    log_content = log_file.read_text()
    assert "INFO:" in log_content
    assert "ERROR:" in log_content


def test_file_modification_tracking(temp_directory: Path) -> None:
    """Test tracking file modifications over time."""
    # Arrange: Create initial file
    tracked_file = temp_directory / "tracked.txt"
    initial_content = "Initial content"
    tracked_file.write_text(initial_content)

    initial_mtime = tracked_file.stat().st_mtime

    # Act: Modify file content
    import time

    time.sleep(0.1)  # Ensure timestamp difference

    modified_content = "Modified content"
    tracked_file.write_text(modified_content)

    # Assert: Verify modification
    assert tracked_file.read_text() == modified_content
    assert tracked_file.stat().st_mtime > initial_mtime


def test_temporary_file_cleanup(temp_directory: Path) -> None:
    """Test that temporary files are properly cleaned up."""
    # This test demonstrates that temp_directory fixture
    # automatically cleans up after the test

    # Arrange & Act: Create multiple temporary files
    for i in range(5):
        temp_file = temp_directory / f"temp_file_{i}.txt"
        temp_file.write_text(f"Temporary content {i}")
        assert temp_file.exists()

    # Assert: Files exist during test
    temp_files = list(temp_directory.glob("temp_file_*.txt"))
    assert len(temp_files) == 5

    # Note: Cleanup happens automatically after test completes


def test_file_with_predefined_structure(
    test_files_structure: Mapping[str, Path],
) -> None:
    """Test using predefined file structures."""
    # The test_files_structure fixture provides commonly needed files

    # Assert: Verify predefined files exist
    assert test_files_structure["README.md"].exists()
    assert test_files_structure["pyproject.toml"].exists()

    # Act: Use predefined structure for testing
    readme_content = test_files_structure["README.md"].read_text()
    assert len(readme_content) > 0

    # Demonstrate modification of predefined files
    config_file = test_files_structure["pyproject.toml"]
    original_content = config_file.read_text()

    # Modify for test
    test_content = original_content + "\n# Test modification"
    config_file.write_text(test_content)

    assert "# Test modification" in config_file.read_text()


if __name__ == "__main__":
    # Run examples directly for demonstration
    import tempfile

    print("=" * 50)

    # Create temporary directory for demonstration
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Demonstrate basic file operations
        demo_file = temp_path / "demo.txt"
        demo_file.write_text("Hello, provide-testkit!")

        # Demonstrate directory creation
        demo_dir = temp_path / "demo_structure"
        demo_dir.mkdir()
        (demo_dir / "subdir").mkdir()

        # Show file listing
        print("📋 Files created:")
        for item in temp_path.rglob("*"):
            relative_path = item.relative_to(temp_path)
            file_label = "[DIR]" if item.is_dir() else "[FILE]"
            print(f"   {file_label} {relative_path}")

    print("\n🎉 File testing examples completed!")
    print("Run with pytest to see fixtures in action:")
    print("   pytest examples/file_testing.py -v")

# 🧪✅🔚
