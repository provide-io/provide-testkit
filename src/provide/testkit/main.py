"""Main CLI entry point for provide-testkit."""

from __future__ import annotations

import click

from .quality.cli import quality_cli


@click.group()
@click.version_option()
def main() -> None:
    """Provide Testkit - Testing utilities for the provide ecosystem."""
    pass


# Add quality commands
main.add_command(quality_cli)


if __name__ == "__main__":
    main()
