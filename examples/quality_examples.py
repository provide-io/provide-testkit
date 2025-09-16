#!/usr/bin/env python3
"""Examples demonstrating the quality module functionality."""

from __future__ import annotations

from pathlib import Path


# Example 1: Basic Quality Fixtures
def test_with_coverage_fixture(coverage_tracker):
    """Example using the coverage fixture."""
    # Start coverage tracking
    coverage_tracker.start()

    # Run your code/tests here
    def example_function():
        return "Hello, World!"

    result = example_function()

    # Stop tracking and get results
    coverage_tracker.stop()
    analysis = coverage_tracker.analyze(Path("./src"))

    assert analysis["passed"]
    assert analysis["coverage_percentage"] >= 80.0


def test_with_security_fixture(security_scanner):
    """Example using the security scanner fixture."""
    # Scan the current project
    result = security_scanner.scan(Path("./src"))

    # Check security score
    assert result["passed"]
    assert result["score"] >= 90.0

    # Access detailed issues
    issues = result.get("issues", [])
    print(f"Found {len(issues)} security issues")


def test_with_complexity_fixture(complexity_analyzer):
    """Example using the complexity analyzer fixture."""
    # Analyze code complexity
    result = complexity_analyzer.analyze(Path("./src"))

    # Check complexity requirements
    assert result["passed"]
    assert result["grade"] in ["A", "B", "C"]
    assert result["average_complexity"] <= 10.0


# Example 2: Quality Decorators
from provide.testkit.quality import (
    complexity_gate,
    coverage_gate,
    documentation_gate,
    performance_gate,
    quality_check,
    security_gate,
)


@coverage_gate(80.0)
def test_coverage_requirement():
    """This test requires 80% coverage to pass."""
    # Test implementation here
    assert True


@security_gate(95.0)
def test_security_requirement():
    """This test requires a 95% security score to pass."""
    # Test implementation here
    assert True


@complexity_gate(max_complexity=10, min_grade="B")
def test_complexity_requirement():
    """This test requires low complexity (max 10, grade B+)."""
    # Test implementation here
    assert True


@documentation_gate(min_coverage=80.0, min_grade="B")
def test_documentation_requirement():
    """This test requires 80% documentation coverage, grade B+."""
    # Test implementation here
    assert True


@performance_gate(max_memory_mb=50.0, max_execution_time=1.0)
def test_performance_requirement():
    """This test must use less than 50MB and execute in under 1 second."""
    # Test implementation here - this function will be profiled
    data = list(range(1000))
    result = sum(data)
    return result


@quality_check(
    coverage=80.0,
    security=True,
    complexity={"max_complexity": 10, "min_grade": "B"},
    documentation={"min_coverage": 80.0},
    performance={"max_memory_mb": 100.0}
)
def test_comprehensive_quality():
    """This test enforces multiple quality requirements at once."""
    # Test implementation here
    assert True


# Example 3: Using Quality Runner Directly
def example_quality_runner():
    """Example of using QualityRunner directly."""
    from provide.testkit.quality.runner import QualityRunner

    # Create runner with specific tools
    runner = QualityRunner()

    # Run quality analysis
    results = runner.run_tools(
        Path("./src"),
        ["coverage", "security", "complexity", "documentation"],
        artifact_dir=Path(".quality-artifacts")
    )

    # Check results
    for tool, result in results.items():
        print(f"{tool}: {'PASS' if result.passed else 'FAIL'} (Score: {result.score}%)")

    # Run with quality gates
    gates = {
        "coverage": 80.0,
        "security": 90.0,
        "complexity": {"max_complexity": 10, "min_grade": "B"},
        "documentation": 75.0
    }

    gate_results = runner.run_with_gates(Path("./src"), gates)

    if gate_results.passed:
        print("✅ All quality gates passed!")
    else:
        print("❌ Quality gates failed!")
        for tool, result in gate_results.results.items():
            if not result.passed:
                print(f"  Failed: {tool}")


# Example 4: Configuration-Based Quality Checks
def example_with_configuration():
    """Example using configuration files for quality settings."""
    import json

    from provide.testkit.quality.runner import QualityRunner

    # Create configuration
    config = {
        "coverage": {
            "min_coverage": 85.0,
            "generate_html": True,
            "exclude": ["*/tests/*", "*/migrations/*"]
        },
        "security": {
            "min_score": 95.0,
            "ignore_issues": ["B101"]  # Ignore specific bandit issues
        },
        "complexity": {
            "max_complexity": 8,
            "min_grade": "A",
            "exclude": ["*/legacy/*"]
        },
        "documentation": {
            "min_coverage": 90.0,
            "min_grade": "A",
            "ignore_init_method": True
        }
    }

    # Save configuration to file
    config_path = Path("quality_config.json")
    config_path.write_text(json.dumps(config, indent=2))

    try:
        # Run with configuration
        runner = QualityRunner()
        results = runner.run_tools(
            Path("./src"),
            ["coverage", "security", "complexity", "documentation"],
            tool_configs=config
        )

        # Process results
        print("Quality Analysis Results:")
        for tool, result in results.items():
            status = "✅ PASS" if result.passed else "❌ FAIL"
            score = f" ({result.score:.1f}%)" if result.score else ""
            print(f"  {tool}: {status}{score}")

    finally:
        # Cleanup
        config_path.unlink(missing_ok=True)


# Example 5: Artifact Management
def example_artifact_management():
    """Example of advanced artifact management."""
    from provide.testkit.quality.artifacts import ArtifactManager
    from provide.testkit.quality.runner import QualityRunner

    # Create artifact manager
    artifact_manager = ArtifactManager(".quality-artifacts")

    # Run quality analysis
    runner = QualityRunner()
    results = runner.run_tools(Path("./src"), ["coverage", "security", "complexity"])

    # Organize artifacts
    for tool, result in results.items():
        tool_dir = artifact_manager.create_timestamped_dir(tool)
        artifact_manager.organize_artifacts(result, tool_dir)

    # Create summary report
    summary_path = artifact_manager.create_summary_report(results)
    print(f"Summary report created: {summary_path}")

    # Generate index
    index_path = artifact_manager.generate_index()
    print(f"Artifact index: {index_path}")

    # Check disk usage
    usage = artifact_manager.get_disk_usage()
    print(f"Artifacts use {usage['total_mb']:.2f} MB")

    # Cleanup old artifacts (keep last 3 runs)
    artifact_manager.cleanup_old_artifacts(keep_count=3)

    # Export artifacts
    export_path = artifact_manager.export_artifacts("quality_export.tar.gz")
    print(f"Artifacts exported to: {export_path}")


# Example 6: Custom Quality Tool Integration
def example_custom_quality_tool():
    """Example of creating a custom quality tool."""
    import json
    import time

    from provide.testkit.quality.base import QualityResult, QualityTool

    class CustomLintTool(QualityTool):
        """Custom linting tool example."""

        def __init__(self, config: dict[str, any] | None = None):
            self.config = config or {}

        def analyze(self, path: Path, **kwargs) -> QualityResult:
            """Run custom analysis."""
            start_time = time.time()

            # Simulate analysis
            issues_found = 5
            total_files = 20

            # Calculate score
            score = max(0, 100 - (issues_found * 5))
            passed = score >= self.config.get("min_score", 80)

            return QualityResult(
                tool="custom_lint",
                passed=passed,
                score=score,
                details={
                    "issues_found": issues_found,
                    "total_files": total_files,
                    "issue_types": ["style", "naming", "unused"],
                },
                execution_time=time.time() - start_time
            )

        def report(self, result: QualityResult, format: str = "terminal") -> str:
            """Generate report."""
            if format == "json":
                return json.dumps({
                    "tool": result.tool,
                    "passed": result.passed,
                    "score": result.score,
                    "details": result.details
                }, indent=2)

            return f"""Custom Lint Report
Status: {'PASS' if result.passed else 'FAIL'}
Score: {result.score}%
Issues: {result.details['issues_found']}
Files: {result.details['total_files']}"""

    # Use custom tool
    custom_tool = CustomLintTool({"min_score": 85})
    result = custom_tool.analyze(Path("./src"))

    print(custom_tool.report(result))


if __name__ == "__main__":
    # Run examples
    print("Quality Module Examples")
    print("=" * 50)

    print("\n1. Quality Runner Example:")
    example_quality_runner()

    print("\n2. Configuration Example:")
    example_with_configuration()

    print("\n3. Artifact Management Example:")
    example_artifact_management()

    print("\n4. Custom Quality Tool Example:")
    example_custom_quality_tool()