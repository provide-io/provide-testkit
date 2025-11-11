#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Example: Your First Test with provide-testkit

This is the absolute simplest example to get you started with provide-testkit.
If you're completely new to testing or provide-testkit, start here!

Key fixture used:
- temp_directory: Creates a temporary directory that's automatically cleaned up

Learning objectives:
- Write your very first test using provide-testkit
- Understand what a fixture is
- See automatic cleanup in action
- Build confidence with testing"""

from pathlib import Path


def test_my_first_testkit_test(temp_directory: Path) -> None:
    """My very first test using provide-testkit!

    This test demonstrates:
    - How to use a fixture (temp_directory)
    - Basic file operations in tests
    - Automatic cleanup (no manual cleanup needed!)
    """
    # Step 1: Create a file in the temporary directory
    # The temp_directory fixture gives us a clean directory to work with
    my_file = temp_directory / "hello.txt"
    my_file.write_text("Hello, testkit!")

    # Step 2: Verify the file was created correctly
    assert my_file.exists()  # Check the file exists
    assert my_file.read_text() == "Hello, testkit!"  # Check the content

    # Step 3: That's it! No cleanup needed
    # The temp_directory fixture automatically cleans up when the test ends


def test_working_with_multiple_files(temp_directory: Path) -> None:
    """A slightly more complex test with multiple files."""
    # Create several files
    file1 = temp_directory / "file1.txt"
    file2 = temp_directory / "file2.txt"
    file3 = temp_directory / "file3.txt"

    # Write different content to each
    file1.write_text("First file")
    file2.write_text("Second file")
    file3.write_text("Third file")

    # Verify all files exist
    assert file1.exists()
    assert file2.exists()
    assert file3.exists()

    # Verify their contents
    assert file1.read_text() == "First file"
    assert file2.read_text() == "Second file"
    assert file3.read_text() == "Third file"


def test_creating_directories(temp_directory: Path) -> None:
    """Test creating subdirectories and files within them."""
    # Create a subdirectory
    sub_dir = temp_directory / "my_subdir"
    sub_dir.mkdir()

    # Create a file in the subdirectory
    sub_file = sub_dir / "nested_file.txt"
    sub_file.write_text("I'm in a subdirectory!")

    # Verify everything was created
    assert sub_dir.exists()
    assert sub_dir.is_dir()
    assert sub_file.exists()
    assert sub_file.read_text() == "I'm in a subdirectory!"


def test_what_happens_without_fixture() -> None:
    """This test shows what happens without the temp_directory fixture.

    Notice this test doesn't use temp_directory as a parameter.
    We have to handle file paths manually and be careful about cleanup.
    """
    import tempfile

    # Without the fixture, we need to create our own temporary directory
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Now we can work with files (but we need to handle paths manually)
        file_path = temp_dir / "manual_file.txt"
        with file_path.open("w") as f:
            f.write("Manual file handling")

        # Verify the file
        with file_path.open() as f:
            content = f.read()
        assert content == "Manual file handling"

    finally:
        # IMPORTANT: We must manually clean up!
        import shutil

        shutil.rmtree(temp_dir)

    # This shows why fixtures are better:
    # - Less code to write
    # - Automatic cleanup
    # - Better error handling
    # - More readable tests


def test_common_mistake_example(temp_directory: Path) -> None:
    """This shows a common mistake and how to avoid it."""
    # ❌ Common mistake: Trying to create files outside temp_directory
    # This would work but defeats the purpose of isolated testing:
    # bad_file = Path("/tmp/my_test_file.txt")  # Don't do this!

    good_file = temp_directory / "my_test_file.txt"
    good_file.write_text("This is isolated and will be cleaned up!")

    assert good_file.exists()
    # The fixture ensures this file is cleaned up automatically


if __name__ == "__main__":
    print("🌟 Your First Test with provide-testkit")
    print("=" * 40)
    print("This example shows the absolute basics:")
    print("")
    print("💡 What is a fixture?")
    print("   A fixture is a piece of code that sets up something")
    print("   your test needs, then cleans it up afterward.")
    print("")
    print("   • Creates a temporary directory for your test")
    print("   • Automatically cleans it up when done")
    print("   • Keeps your tests isolated from each other")
    print("")
    print("🚀 To run this test:")
    print("   pytest examples/basics/first_test.py -v")
    print("")
    print("📚 Next steps:")
    print("   Check out basic_usage.py for more examples!")

# 🧪✅🔚
