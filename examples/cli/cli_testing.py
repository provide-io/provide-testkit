#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Example: CLI Application Testing Patterns

This example demonstrates testing Click-based CLI applications using
provide-testkit's CLI testing utilities and integration with provide-foundation.

Key fixtures used:
- isolated_cli_runner: Click CLI test runner with isolation
- temp_directory: Temporary directories for CLI input/output
- mock_context: Mocked application context

Learning objectives:
- Test CLI commands and arguments
- Validate command output and exit codes
- Test interactive CLI prompts
- Handle file input/output in CLI tests
- Test CLI error conditions"""

from pathlib import Path

import click
from click import Context
from click.testing import CliRunner


# Example CLI application for testing
@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: Context, verbose: bool) -> None:
    """Example CLI application for testing purposes."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("name")
@click.option("--greeting", default="Hello", help="Greeting to use")
@click.pass_context
def greet(ctx: Context, name: str, greeting: str) -> None:
    """Greet someone with a customizable greeting."""
    if ctx.obj["verbose"]:
        click.echo(f"Verbose mode: Greeting {name}")
    click.echo(f"{greeting}, {name}!")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option("--format", "output_format", default="json", type=click.Choice(["json", "yaml", "txt"]))
def convert(input_file: Path, output_file: Path, output_format: str) -> None:
    """Convert file from one format to another."""
    # Simulate file conversion
    content = input_file.read_text()

    if output_format == "json":
        converted = f'{{"content": "{content.strip()}"}}'
    elif output_format == "yaml":
        converted = f'content: "{content.strip()}"'
    else:  # txt
        converted = content.upper()

    output_file.write_text(converted)
    click.echo(f"Converted {input_file} to {output_file} ({output_format})")


@cli.command()
@click.option("--count", default=1, help="Number of items to process")
@click.confirmation_option(prompt="Are you sure you want to proceed?")
def process(count: int) -> None:
    """Process items with confirmation."""
    for i in range(count):
        click.echo(f"Processing item {i + 1}")
    click.echo("Processing completed!")


@cli.command()
@click.option("--fail", is_flag=True, help="Force command to fail")
def status(fail: bool) -> None:
    """Check application status."""
    if fail:
        click.echo("Error: Something went wrong!", err=True)
        raise click.ClickException("Status check failed")
    click.echo("Status: All systems operational")


# Test cases
def test_basic_command_execution(isolated_cli_runner: CliRunner) -> None:
    """Test basic CLI command execution."""
    # Act: Run simple greet command
    result = isolated_cli_runner.invoke(cli, ["greet", "Alice"])

    # Assert: Command succeeded and output is correct
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output


def test_command_with_options(isolated_cli_runner: CliRunner) -> None:
    """Test CLI command with options."""
    # Act: Run greet command with custom greeting
    result = isolated_cli_runner.invoke(cli, ["greet", "Bob", "--greeting", "Hi"])

    # Assert: Custom greeting was used
    assert result.exit_code == 0
    assert "Hi, Bob!" in result.output


def test_verbose_flag(isolated_cli_runner: CliRunner) -> None:
    """Test global verbose flag."""
    # Act: Run command with verbose flag
    result = isolated_cli_runner.invoke(cli, ["--verbose", "greet", "Charlie"])

    # Assert: Verbose output is included
    assert result.exit_code == 0
    assert "Verbose mode: Greeting Charlie" in result.output
    assert "Hello, Charlie!" in result.output


def test_file_input_output(isolated_cli_runner: CliRunner, temp_directory: Path) -> None:
    """Test CLI commands that work with files."""
    # Arrange: Create input file
    input_file = temp_directory / "input.txt"
    input_file.write_text("Hello World")

    output_file = temp_directory / "output.json"

    # Act: Run convert command
    result = isolated_cli_runner.invoke(
        cli, ["convert", str(input_file), str(output_file), "--format", "json"]
    )

    # Assert: Command succeeded and file was created
    assert result.exit_code == 0
    assert output_file.exists()
    assert output_file.read_text() == '{"content": "Hello World"}'
    assert f"Converted {input_file} to {output_file} (json)" in result.output


def test_different_output_formats(isolated_cli_runner: CliRunner, temp_directory: Path) -> None:
    """Test CLI command with different output format options."""
    # Arrange: Create input file
    input_file = temp_directory / "data.txt"
    input_file.write_text("test data")

    # Test JSON format
    json_output = temp_directory / "output.json"
    result = isolated_cli_runner.invoke(
        cli, ["convert", str(input_file), str(json_output), "--format", "json"]
    )
    assert result.exit_code == 0
    assert json_output.read_text() == '{"content": "test data"}'

    # Test YAML format
    yaml_output = temp_directory / "output.yaml"
    result = isolated_cli_runner.invoke(
        cli, ["convert", str(input_file), str(yaml_output), "--format", "yaml"]
    )
    assert result.exit_code == 0
    assert yaml_output.read_text() == 'content: "test data"'

    # Test TXT format
    txt_output = temp_directory / "output.txt"
    result = isolated_cli_runner.invoke(cli, ["convert", str(input_file), str(txt_output), "--format", "txt"])
    assert result.exit_code == 0
    assert txt_output.read_text() == "TEST DATA"


def test_interactive_confirmation(isolated_cli_runner: CliRunner) -> None:
    """Test CLI command with interactive confirmation."""
    # Act: Run process command with automatic 'yes' response
    result = isolated_cli_runner.invoke(cli, ["process", "--count", "3"], input="y\n")

    # Assert: Command executed after confirmation
    assert result.exit_code == 0
    assert "Processing item 1" in result.output
    assert "Processing item 2" in result.output
    assert "Processing item 3" in result.output
    assert "Processing completed!" in result.output


def test_interactive_cancellation(isolated_cli_runner: CliRunner) -> None:
    """Test CLI command cancellation through interactive prompt."""
    # Act: Run process command with 'no' response
    result = isolated_cli_runner.invoke(cli, ["process", "--count", "2"], input="n\n")

    # Assert: Command was cancelled
    assert result.exit_code == 1  # Click confirmation aborts with exit code 1
    assert "Processing item" not in result.output


def test_error_handling(isolated_cli_runner: CliRunner) -> None:
    """Test CLI error handling."""
    # Act: Run status command with failure flag
    result = isolated_cli_runner.invoke(cli, ["status", "--fail"])

    # Assert: Command failed with expected error
    assert result.exit_code != 0
    assert "Error: Something went wrong!" in result.output


def test_missing_file_error(isolated_cli_runner: CliRunner, temp_directory: Path) -> None:
    """Test CLI error when input file doesn't exist."""
    # Arrange: Reference non-existent file
    missing_file = temp_directory / "missing.txt"
    output_file = temp_directory / "output.json"

    # Act: Run convert command with missing input file
    result = isolated_cli_runner.invoke(cli, ["convert", str(missing_file), str(output_file)])

    # Assert: Command failed due to missing file
    assert result.exit_code != 0
    assert "does not exist" in result.output.lower()


def test_invalid_option_value(isolated_cli_runner: CliRunner, temp_directory: Path) -> None:
    """Test CLI error handling for invalid option values."""
    # Arrange: Create input file
    input_file = temp_directory / "input.txt"
    input_file.write_text("test")
    output_file = temp_directory / "output.txt"

    # Act: Run convert command with invalid format
    result = isolated_cli_runner.invoke(
        cli, ["convert", str(input_file), str(output_file), "--format", "invalid"]
    )

    # Assert: Command failed due to invalid format
    assert result.exit_code != 0
    assert "invalid" in result.output.lower()


def test_help_output(isolated_cli_runner: CliRunner) -> None:
    """Test CLI help output."""
    # Act: Get help for main command
    result = isolated_cli_runner.invoke(cli, ["--help"])

    # Assert: Help is displayed
    assert result.exit_code == 0
    assert "Example CLI application" in result.output
    assert "greet" in result.output
    assert "convert" in result.output

    # Act: Get help for specific command
    result = isolated_cli_runner.invoke(cli, ["greet", "--help"])

    # Assert: Command-specific help is displayed
    assert result.exit_code == 0
    assert "Greet someone" in result.output
    assert "--greeting" in result.output


def test_cli_with_environment_variables(isolated_cli_runner: CliRunner) -> None:
    """Test CLI behavior with environment variables."""
    # Act: Run command with environment variable
    result = isolated_cli_runner.invoke(cli, ["greet", "Alice"], env={"GREETING_PREFIX": "Hi there"})

    # Assert: Command executed (environment is isolated)
    assert result.exit_code == 0
    # Note: This example doesn't use the env var, but shows how to test with env


if __name__ == "__main__":
    # Run examples directly for demonstration
    print("🖥️  CLI Testing Examples")
    print("=" * 50)

    # Demonstrate CLI usage
    from click.testing import CliRunner

    runner = CliRunner()

    print("Demo 1: Basic greeting")
    result = runner.invoke(cli, ["greet", "TestUser"])
    print(f"   Output: {result.output.strip()}")
    print(f"   Exit code: {result.exit_code}")

    print("\nDemo 2: Custom greeting")
    result = runner.invoke(cli, ["greet", "TestUser", "--greeting", "Welcome"])
    print(f"   Output: {result.output.strip()}")

    print("\nDemo 3: Verbose mode")
    result = runner.invoke(cli, ["--verbose", "greet", "TestUser"])
    print(f"   Output: {result.output.strip()}")

    print("\nDemo 4: Status check")
    result = runner.invoke(cli, ["status"])
    print(f"   Output: {result.output.strip()}")

    print("\n🎉 CLI examples completed!")
    print("Run with pytest to see fixtures in action:")
    print("   pytest examples/cli_testing.py -v")

# 🧪✅🔚
