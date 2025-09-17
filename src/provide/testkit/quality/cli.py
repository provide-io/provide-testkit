"""CLI commands for quality analysis."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import click

from .runner import QualityRunner


@click.group(name="quality")
@click.pass_context
def quality_cli(ctx: click.Context) -> None:
    """Quality analysis commands for provide-testkit."""
    ctx.ensure_object(dict)


@quality_cli.command("analyze")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--tool",
    multiple=True,
    type=click.Choice(["coverage", "security", "complexity", "documentation", "profiling"]),
    help="Specific tools to run (default: all available)",
)
@click.option(
    "--artifact-dir",
    type=click.Path(path_type=Path),
    default=".quality-artifacts",
    help="Directory for output artifacts",
)
@click.option(
    "--format", type=click.Choice(["terminal", "json", "summary"]), default="terminal", help="Output format"
)
@click.option("--fail-fast", is_flag=True, help="Stop on first failure")
@click.option("--config", type=click.Path(exists=True, path_type=Path), help="Configuration file (JSON)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def analyze_command(
    path: Path,
    tool: tuple[str, ...],
    artifact_dir: Path,
    format: str,
    fail_fast: bool,
    config: Path | None,
    verbose: bool,
) -> None:
    """Analyze code quality for the given path."""
    try:
        # Load configuration
        config_data = {}
        if config:
            config_data = json.loads(config.read_text())

        # Determine which tools to run
        if tool:
            tools_to_run = list(tool)
        else:
            tools_to_run = ["coverage", "security", "complexity", "documentation"]

        if verbose:
            click.echo(f"Analyzing {path} with tools: {', '.join(tools_to_run)}")
            click.echo(f"Artifacts will be saved to: {artifact_dir}")

        # Run quality analysis
        runner = QualityRunner()
        results = runner.run_tools(path, tools_to_run, artifact_dir=artifact_dir, tool_configs=config_data)

        # Output results
        if format == "json":
            output = {
                "path": str(path),
                "tools": tools_to_run,
                "results": {
                    tool: {
                        "passed": result.passed,
                        "score": result.score,
                        "details": result.details,
                        "execution_time": result.execution_time,
                    }
                    for tool, result in results.items()
                },
            }
            click.echo(json.dumps(output, indent=2))
        elif format == "summary":
            _print_summary(results, verbose)
        else:
            _print_terminal_results(results, verbose)

        # Exit with error code if any tool failed
        if any(not result.passed for result in results.values()):
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@quality_cli.command("gates")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--coverage", type=float, help="Minimum coverage percentage required")
@click.option("--security", type=float, help="Minimum security score required")
@click.option("--complexity", type=int, help="Maximum complexity allowed")
@click.option("--documentation", type=float, help="Minimum documentation coverage required")
@click.option("--config", type=click.Path(exists=True, path_type=Path), help="Gates configuration file (JSON)")
@click.option(
    "--artifact-dir",
    type=click.Path(path_type=Path),
    default=".quality-artifacts",
    help="Directory for output artifacts",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def gates_command(
    path: Path,
    coverage: float | None,
    security: float | None,
    complexity: int | None,
    documentation: float | None,
    config: Path | None,
    artifact_dir: Path,
    verbose: bool,
) -> None:
    """Run quality gates on the given path."""
    try:
        # Build and validate gates configuration
        gates = _build_gates_config(coverage, security, complexity, documentation, config)

        if verbose:
            _print_gate_info(path, gates)

        # Run quality gates and handle results
        results = _execute_quality_gates(path, gates, artifact_dir)
        _handle_gate_results(results, verbose)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _build_gates_config(
    coverage: float | None,
    security: float | None,
    complexity: int | None,
    documentation: float | None,
    config: Path | None,
) -> dict[str, Any]:
    """Build gates configuration from CLI arguments and config file."""
    gates = {}

    # Add CLI-specified gates
    if coverage is not None:
        gates["coverage"] = coverage
    if security is not None:
        gates["security"] = security
    if complexity is not None:
        gates["complexity"] = {"max_complexity": complexity}
    if documentation is not None:
        gates["documentation"] = documentation

    # Load from config file if provided
    if config:
        config_gates = json.loads(config.read_text())
        gates.update(config_gates)

    if not gates:
        click.echo("Error: No quality gates specified", err=True)
        sys.exit(1)

    return gates


def _print_gate_info(path: Path, gates: dict[str, Any]) -> None:
    """Print verbose information about gates being run."""
    click.echo(f"Running quality gates on {path}")
    click.echo(f"Gates: {gates}")


def _execute_quality_gates(path: Path, gates: dict[str, Any], artifact_dir: Path) -> Any:
    """Execute quality gates and return results."""
    runner = QualityRunner()
    return runner.run_with_gates(path, gates, artifact_dir=artifact_dir)


def _handle_gate_results(results: Any, verbose: bool) -> None:
    """Handle and display gate results, exit on failure."""
    # Print summary
    if results.passed:
        click.echo("✅ All quality gates passed!", fg="green")
    else:
        click.echo("❌ Quality gates failed!", fg="red")

    # Print detailed results if verbose
    if verbose:
        _print_detailed_results(results)

    # Exit with error code if gates failed
    if not results.passed:
        sys.exit(1)


def _print_detailed_results(results: Any) -> None:
    """Print detailed results for each tool."""
    click.echo("\nDetailed Results:")
    for tool, result in results.results.items():
        status = "✅ PASS" if result.passed else "❌ FAIL"
        score_text = f" (Score: {result.score:.1f}%)" if result.score is not None else ""
        click.echo(f"  {tool}: {status}{score_text}")


@quality_cli.command("coverage")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--min-coverage", type=float, default=80.0, help="Minimum coverage percentage")
@click.option(
    "--artifact-dir",
    type=click.Path(path_type=Path),
    default=".coverage-artifacts",
    help="Directory for coverage artifacts",
)
@click.option("--html", is_flag=True, help="Generate HTML report")
@click.option("--xml", is_flag=True, help="Generate XML report")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def coverage_command(
    path: Path, min_coverage: float, artifact_dir: Path, html: bool, xml: bool, verbose: bool
) -> None:
    """Run coverage analysis on the given path."""
    try:
        from .coverage.tracker import CoverageTracker

        config = {"min_coverage": min_coverage, "generate_html": html, "generate_xml": xml}

        tracker = CoverageTracker(config)
        result = tracker.analyze(path, artifact_dir=artifact_dir)

        status = "✅ PASSED" if result.passed else "❌ FAILED"
        coverage_pct = result.details.get("coverage_percentage", 0)

        click.echo(f"Coverage Analysis: {status}")
        click.echo(f"Coverage: {coverage_pct:.1f}% (required: {min_coverage}%)")

        if verbose and result.details.get("missing_files"):
            click.echo("\nFiles with missing coverage:")
            for file_info in result.details["missing_files"][:10]:  # Top 10
                click.echo(f"  {file_info['filename']}: {file_info['coverage']:.1f}%")

        if not result.passed:
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@quality_cli.command("security")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--min-score", type=float, default=90.0, help="Minimum security score")
@click.option(
    "--artifact-dir",
    type=click.Path(path_type=Path),
    default=".security-artifacts",
    help="Directory for security artifacts",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def security_command(path: Path, min_score: float, artifact_dir: Path, verbose: bool) -> None:
    """Run security analysis on the given path."""
    try:
        from .security.scanner import SecurityScanner

        config = {"min_score": min_score}
        scanner = SecurityScanner(config)
        result = scanner.analyze(path, artifact_dir=artifact_dir)

        status = "✅ PASSED" if result.passed else "❌ FAILED"
        score = result.score or 0

        click.echo(f"Security Analysis: {status}")
        click.echo(f"Score: {score:.1f}% (required: {min_score}%)")

        if verbose and result.details.get("issues"):
            issues = result.details["issues"]
            click.echo(f"\nFound {len(issues)} security issues:")
            for issue in issues[:5]:  # Top 5
                severity = issue.get("severity", "unknown")
                test_id = issue.get("test_id", "unknown")
                filename = issue.get("filename", "unknown")
                click.echo(f"  [{severity.upper()}] {test_id} in {filename}")

        if not result.passed:
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@quality_cli.command("complexity")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--max-complexity", type=int, default=10, help="Maximum complexity allowed")
@click.option(
    "--min-grade",
    type=click.Choice(["A", "B", "C", "D", "F"]),
    default="C",
    help="Minimum complexity grade required",
)
@click.option(
    "--artifact-dir",
    type=click.Path(path_type=Path),
    default=".complexity-artifacts",
    help="Directory for complexity artifacts",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def complexity_command(
    path: Path, max_complexity: int, min_grade: str, artifact_dir: Path, verbose: bool
) -> None:
    """Run complexity analysis on the given path."""
    try:
        from .complexity.analyzer import ComplexityAnalyzer

        config = {"max_complexity": max_complexity, "min_grade": min_grade}

        analyzer = ComplexityAnalyzer(config)
        result = analyzer.analyze(path, artifact_dir=artifact_dir)

        status = "✅ PASSED" if result.passed else "❌ FAILED"
        grade = result.details.get("overall_grade", "N/A")
        avg_complexity = result.details.get("average_complexity", 0)

        click.echo(f"Complexity Analysis: {status}")
        click.echo(f"Grade: {grade} (Average complexity: {avg_complexity:.1f})")

        if verbose and result.details.get("most_complex_functions"):
            click.echo("\nMost complex functions:")
            for func in result.details["most_complex_functions"][:5]:
                click.echo(f"  {func['name']}: {func['complexity']} (Grade {func['rank']})")

        if not result.passed:
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _print_terminal_results(results: dict[str, Any], verbose: bool) -> None:
    """Print results in terminal format."""
    click.echo("Quality Analysis Results")
    click.echo("=" * 50)

    for tool, result in results.items():
        status = "✅ PASSED" if result.passed else "❌ FAILED"
        score_text = f" ({result.score:.1f}%)" if result.score is not None else ""

        click.echo(f"{tool.title()}: {status}{score_text}")

        if verbose:
            if hasattr(result, "execution_time") and result.execution_time:
                click.echo(f"  Execution time: {result.execution_time:.2f}s")

            # Show key details
            details = result.details
            if tool == "coverage" and "coverage_percentage" in details:
                click.echo(f"  Coverage: {details['coverage_percentage']:.1f}%")
            elif tool == "security" and "total_issues" in details:
                click.echo(f"  Issues found: {details['total_issues']}")
            elif tool == "complexity" and "average_complexity" in details:
                click.echo(f"  Average complexity: {details['average_complexity']:.1f}")
                click.echo(f"  Grade: {details.get('overall_grade', 'N/A')}")
            elif tool == "documentation" and "total_coverage" in details:
                click.echo(f"  Documentation: {details['total_coverage']:.1f}%")

    click.echo()


def _print_summary(results: dict[str, Any], verbose: bool) -> None:
    """Print summary of results."""
    passed = sum(1 for result in results.values() if result.passed)
    total = len(results)

    if passed == total:
        click.echo(f"✅ All {total} quality checks passed!", fg="green")
    else:
        failed = total - passed
        click.echo(f"❌ {failed}/{total} quality checks failed!", fg="red")

    if verbose:
        for tool, result in results.items():
            status_icon = "✅" if result.passed else "❌"
            click.echo(f"  {status_icon} {tool}")


if __name__ == "__main__":
    quality_cli()
