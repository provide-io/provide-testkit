#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Example: Basic Usage Patterns

This example demonstrates the most commonly used provide-testkit fixtures
and basic testing patterns. Start here if you're new to provide-testkit.

Key fixtures used:
- temp_directory: Temporary directory for test files
- isolated_cli_runner: Isolated CLI testing environment
- clean_event_loop: Fresh event loop for async tests

Learning objectives:
- Understand basic fixture usage
- Learn common testing patterns
- See how fixtures provide automatic cleanup
- Practice the Arrange-Act-Assert pattern"""

import asyncio
import json
from pathlib import Path

import click
from click.testing import CliRunner
import pytest


def test_temp_directory_basic_usage(temp_directory: Path) -> None:
    """Basic usage of temp_directory fixture.

    This demonstrates the most fundamental testkit fixture - temp_directory.
    It provides complete isolation between tests and automatic cleanup.

    Key benefits:
    - Each test gets a fresh, empty directory
    - No interference between test runs
    - Automatic cleanup when test finishes
    - Works with pathlib.Path for modern file operations
    """
    # === VERIFICATION: Confirm we got a clean, isolated directory ===
    # The temp_directory fixture provides a pathlib.Path object
    # pointing to a unique temporary directory for this test
    assert temp_directory.exists()  # Directory was created
    assert temp_directory.is_dir()  # It's actually a directory

    # Verify it's empty (fresh start for every test)
    assert list(temp_directory.iterdir()) == []  # No files yet

    # === SETUP: Create test files to simulate real scenarios ===
    # Using the / operator with Path objects is the modern way
    # to construct file paths (works on Windows, macOS, Linux)
    config_file = temp_directory / "config.json"

    # Write JSON configuration data
    # This simulates testing with configuration files
    config_file.write_text('{"debug": true, "version": "1.0"}')

    # Create a simple text file
    # This demonstrates basic file operations in tests
    data_file = temp_directory / "data.txt"
    data_file.write_text("Hello, testkit!")

    # === VERIFICATION: Check our file operations worked correctly ===
    # Verify files were created successfully
    assert config_file.exists()  # JSON config file exists
    assert data_file.exists()  # Text data file exists

    # Verify we can read and parse the JSON content
    # This is a common pattern when testing configuration loading
    config_data = json.loads(config_file.read_text())
    assert config_data["debug"] is True  # Boolean values work
    assert config_data["version"] == "1.0"  # String values work

    # Verify text file content is exactly what we wrote
    assert data_file.read_text() == "Hello, testkit!"

    # === KEY BENEFIT: No manual cleanup required! ===
    # When this function ends, the temp_directory fixture automatically
    # deletes the entire directory and all files we created.
    # This prevents test pollution and keeps your filesystem clean.


def test_multiple_files_and_directories(temp_directory: Path) -> None:
    """Working with multiple files and nested directories."""
    # Arrange: Create nested structure
    src_dir = temp_directory / "src"
    src_dir.mkdir()

    tests_dir = temp_directory / "tests"
    tests_dir.mkdir()

    # Act: Create files in different directories
    main_file = src_dir / "main.py"
    main_file.write_text('print("Hello, World!")')

    test_file = tests_dir / "test_main.py"
    test_file.write_text("def test_main():\n    assert True")

    readme = temp_directory / "README.md"
    readme.write_text("# My Project\n\nA test project.")

    # Assert: Verify structure and content
    assert (temp_directory / "src").is_dir()
    assert (temp_directory / "tests").is_dir()
    assert main_file.exists()
    assert test_file.exists()
    assert readme.exists()

    # Check file contents
    assert 'print("Hello, World!")' in main_file.read_text()
    assert "def test_main():" in test_file.read_text()
    assert "# My Project" in readme.read_text()


# Example CLI command for testing
@click.command()
@click.option("--name", default="World", help="Name to greet")
@click.option("--uppercase", is_flag=True, help="Use uppercase")
def greet(name: str, uppercase: bool) -> None:
    """Simple greeting command."""
    message = f"Hello, {name}!"
    if uppercase:
        message = message.upper()
    click.echo(message)


def test_cli_basic_usage(isolated_cli_runner: CliRunner) -> None:
    """Basic CLI testing with isolated_cli_runner fixture."""
    # Arrange: The isolated_cli_runner fixture provides a Click CliRunner
    # in an isolated filesystem environment

    # Act: Run the CLI command
    result = isolated_cli_runner.invoke(greet, ["--name", "testkit"])

    # Assert: Check the command ran successfully
    assert result.exit_code == 0
    assert "Hello, testkit!" in result.output


def test_cli_with_flags(isolated_cli_runner: CliRunner) -> None:
    """Testing CLI commands with different flags."""
    # Arrange & Act: Test with uppercase flag
    result = isolated_cli_runner.invoke(greet, ["--name", "testkit", "--uppercase"])

    # Assert: Verify uppercase output
    assert result.exit_code == 0
    assert "HELLO, TESTKIT!" in result.output


def test_cli_default_behavior(isolated_cli_runner: CliRunner) -> None:
    """Testing CLI command default behavior."""
    # Arrange & Act: Run command with no arguments
    result = isolated_cli_runner.invoke(greet)

    # Assert: Verify default name is used
    assert result.exit_code == 0
    assert "Hello, World!" in result.output


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_event_loop")
async def test_async_basic_usage() -> None:
    """Basic async testing with clean_event_loop fixture."""

    # Arrange: Define an async function to test
    async def fetch_data(delay: float = 0.1) -> dict[str, str]:
        """Simulate async data fetching."""
        await asyncio.sleep(delay)
        return {"status": "success", "data": "test_data"}

    # Act: Call the async function
    result = await fetch_data()

    # Assert: Verify the result
    assert result["status"] == "success"
    assert result["data"] == "test_data"


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_event_loop")
async def test_multiple_async_operations() -> None:
    """Testing multiple concurrent async operations."""

    # Arrange: Define async operations
    async def task(task_id: int, delay: float = 0.1) -> str:
        await asyncio.sleep(delay)
        return f"task_{task_id}_complete"

    # Act: Run multiple tasks concurrently
    tasks = [task(i) for i in range(3)]
    results = await asyncio.gather(*tasks)

    # Assert: Verify all tasks completed
    assert len(results) == 3
    assert "task_0_complete" in results
    assert "task_1_complete" in results
    assert "task_2_complete" in results


def test_combining_fixtures(temp_directory: Path, isolated_cli_runner: CliRunner) -> None:
    """Combining multiple fixtures in a single test.

    This shows how you can use multiple fixtures together
    to create more complex test scenarios.
    """
    # Arrange: Create a config file using temp_directory
    config_file = temp_directory / "config.json"
    config_data = {"greeting": "Hi there", "debug": True}
    config_file.write_text(json.dumps(config_data, indent=2))

    # Create a CLI command that reads the config
    @click.command()
    @click.option("--config", type=click.Path(exists=True))
    @click.argument("name")
    def greet_from_config(config: str, name: str) -> None:
        """Greet using config file."""
        config_data = json.loads(Path(config).read_text())
        greeting = config_data.get("greeting", "Hello")
        click.echo(f"{greeting}, {name}!")
        if config_data.get("debug"):
            click.echo("Debug mode enabled")

    # Act: Use isolated_cli_runner to test the command
    result = isolated_cli_runner.invoke(greet_from_config, ["--config", str(config_file), "testkit"])

    # Assert: Verify both the greeting and debug output
    assert result.exit_code == 0
    assert "Hi there, testkit!" in result.output
    assert "Debug mode enabled" in result.output


def test_error_handling_example(temp_directory: Path) -> None:
    """Example of testing error conditions."""
    # Arrange: Create a file that we'll try to read incorrectly
    bad_json_file = temp_directory / "bad.json"
    bad_json_file.write_text('{"incomplete": json')

    # Act & Assert: Test that we handle JSON parsing errors
    with pytest.raises(json.JSONDecodeError):
        json.loads(bad_json_file.read_text())


def test_parametrized_example(temp_directory: Path) -> None:
    """Example showing how fixtures work with parameterized tests.

    Note: This test demonstrates the concept, but for actual parameterization,
    you would use @pytest.mark.parametrize decorator.
    """
    # Different file formats to test
    test_cases = [
        ("config.json", '{"key": "value"}', lambda f: json.loads(f.read_text())),
        ("config.txt", "key=value", lambda f: f.read_text().strip()),
        ("data.csv", "name,value\ntest,123", lambda f: f.read_text().split("\n")),
    ]

    for filename, content, parser in test_cases:
        # Arrange: Create file with specific content
        test_file = temp_directory / filename
        test_file.write_text(content)

        # Act: Parse the file
        parsed = parser(test_file)

        # Assert: Verify parsing worked
        assert parsed is not None
        if filename == "config.json":
            assert parsed["key"] == "value"
        elif filename == "config.txt":
            assert "key=value" in parsed
        elif filename == "data.csv":
            assert len(parsed) >= 2  # Header + data row


if __name__ == "__main__":
    # When run directly, this provides a quick demo
    print("🚀 Basic Usage Examples for provide-testkit")
    print("=" * 50)
    print("This file demonstrates the most common testkit fixtures:")
    print("  • temp_directory - Temporary directories with auto-cleanup")
    print("  • isolated_cli_runner - CLI testing with Click")
    print("  • clean_event_loop - Async testing support")
    print("")
    print("Run with pytest to see fixtures in action:")
    print("   pytest examples/basics/basic_usage.py -v")
    print("")
    print("Key concepts demonstrated:")
    print("  ✓ Automatic resource cleanup")
    print("  ✓ Test isolation")
    print("  ✓ Arrange-Act-Assert pattern")
    print("  ✓ Combining multiple fixtures")
    print("  ✓ Error condition testing")

# 🧪✅🔚
