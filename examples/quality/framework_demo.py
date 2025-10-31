#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Demonstration of the provide-testkit quality framework using mock tools.

This script demonstrates the quality framework functionality without requiring
external tool dependencies, proving the implementation works correctly."""

from __future__ import annotations

import json
from pathlib import Path
import time

from provide.testkit.quality.artifacts import ArtifactManager
from provide.testkit.quality.base import QualityResult
from provide.testkit.quality.report import ReportGenerator
from provide.testkit.quality.runner import QualityRunner


class MockCoverageTool:
    """Mock coverage tool for demonstration."""

    def __init__(self, config: dict[str, object] | None = None) -> None:
        self.config = config or {}

    def analyze(self, path: Path, *, artifact_dir: Path | None = None) -> QualityResult:
        """Mock coverage analysis."""
        start_time = time.time()

        # Simulate analysis
        coverage_percentage = 78.5
        lines_covered = 314
        lines_missing = 86
        total_lines = 400

        score = coverage_percentage
        passed = score >= self.config.get("min_coverage", 75.0)

        # Create mock artifacts
        if artifact_dir:
            artifact_dir.mkdir(parents=True, exist_ok=True)

            # Mock coverage report
            coverage_data = {
                "coverage": coverage_percentage,
                "lines_covered": lines_covered,
                "lines_missing": lines_missing,
                "files": [
                    {"file": "quality/base.py", "coverage": 85.2},
                    {"file": "quality/runner.py", "coverage": 92.1},
                    {"file": "quality/report.py", "coverage": 67.8},
                ],
            }
            coverage_file = artifact_dir / "coverage.json"
            coverage_file.write_text(json.dumps(coverage_data, indent=2))

        return QualityResult(
            tool="coverage",
            passed=passed,
            score=score,
            details={
                "coverage_percentage": coverage_percentage,
                "lines_covered": lines_covered,
                "lines_missing": lines_missing,
                "total_lines": total_lines,
                "min_coverage_required": self.config.get("min_coverage", 75.0),
            },
            artifacts=[coverage_file] if artifact_dir else [],
            execution_time=time.time() - start_time,
        )


class MockSecurityTool:
    """Mock security tool for demonstration."""

    def __init__(self, config: dict[str, object] | None = None) -> None:
        self.config = config or {}

    def analyze(self, path: Path, *, artifact_dir: Path | None = None) -> QualityResult:
        """Mock security analysis."""
        start_time = time.time()

        # Simulate security scan
        issues = [
            {"severity": "LOW", "test_id": "B101", "filename": "test_file.py", "line": 42},
            {"severity": "MEDIUM", "test_id": "B603", "filename": "cli.py", "line": 156},
            {"severity": "LOW", "test_id": "B104", "filename": "config.py", "line": 23},
        ]

        # Calculate score based on issues
        score = max(
            0,
            100
            - (
                len([i for i in issues if i["severity"] == "HIGH"]) * 20
                + len([i for i in issues if i["severity"] == "MEDIUM"]) * 10
                + len([i for i in issues if i["severity"] == "LOW"]) * 2
            ),
        )

        passed = score >= self.config.get("min_score", 85.0)

        # Create mock artifacts
        if artifact_dir:
            artifact_dir.mkdir(parents=True, exist_ok=True)

            security_file = artifact_dir / "security.json"
            security_file.write_text(json.dumps({"issues": issues}, indent=2))

        return QualityResult(
            tool="security",
            passed=passed,
            score=score,
            details={
                "total_issues": len(issues),
                "issues": issues,
                "severity_counts": {
                    "HIGH": len([i for i in issues if i["severity"] == "HIGH"]),
                    "MEDIUM": len([i for i in issues if i["severity"] == "MEDIUM"]),
                    "LOW": len([i for i in issues if i["severity"] == "LOW"]),
                },
                "min_score_required": self.config.get("min_score", 85.0),
            },
            artifacts=[security_file] if artifact_dir else [],
            execution_time=time.time() - start_time,
        )


class MockComplexityTool:
    """Mock complexity tool for demonstration."""

    def __init__(self, config: dict[str, object] | None = None) -> None:
        self.config = config or {}

    def analyze(self, path: Path, *, artifact_dir: Path | None = None) -> QualityResult:
        """Mock complexity analysis."""
        start_time = time.time()

        # Simulate complexity analysis
        functions = [
            {"name": "analyze_quality", "complexity": 8, "rank": "B"},
            {"name": "generate_report", "complexity": 12, "rank": "C"},
            {"name": "complex_function", "complexity": 18, "rank": "D"},
            {"name": "simple_function", "complexity": 3, "rank": "A"},
        ]

        avg_complexity = sum(f["complexity"] for f in functions) / len(functions)
        max_complexity = max(f["complexity"] for f in functions)

        # Calculate grade
        if avg_complexity <= 5:
            grade = "A"
            score = 100.0
        elif avg_complexity <= 10:
            grade = "B"
            score = 85.0
        elif avg_complexity <= 15:
            grade = "C"
            score = 70.0
        else:
            grade = "D"
            score = 55.0

        passed = avg_complexity <= self.config.get("max_complexity", 15) and score >= self.config.get(
            "min_score", 70.0
        )

        # Create mock artifacts
        if artifact_dir:
            artifact_dir.mkdir(parents=True, exist_ok=True)

            complexity_file = artifact_dir / "complexity.json"
            complexity_file.write_text(json.dumps({"functions": functions}, indent=2))

        return QualityResult(
            tool="complexity",
            passed=passed,
            score=score,
            details={
                "average_complexity": avg_complexity,
                "max_complexity": max_complexity,
                "overall_grade": grade,
                "total_functions": len(functions),
                "most_complex_functions": sorted(functions, key=lambda x: x["complexity"], reverse=True),
                "grade_breakdown": {
                    "A": len([f for f in functions if f["rank"] == "A"]),
                    "B": len([f for f in functions if f["rank"] == "B"]),
                    "C": len([f for f in functions if f["rank"] == "C"]),
                    "D": len([f for f in functions if f["rank"] == "D"]),
                },
            },
            artifacts=[complexity_file] if artifact_dir else [],
            execution_time=time.time() - start_time,
        )


def setup_mock_runner() -> QualityRunner:
    """Setup a quality runner with mock tools."""
    runner = QualityRunner(
        artifact_root=Path("quality-reports/artifacts"),
        tools=[],  # Start with empty tools
        config={
            "coverage": {"min_coverage": 75.0},
            "security": {"min_score": 85.0},
            "complexity": {"max_complexity": 15, "min_score": 70.0},
        },
    )

    # Manually add mock tools
    runner.tool_instances = {
        "coverage": MockCoverageTool(runner.config.get("coverage", {})),
        "security": MockSecurityTool(runner.config.get("security", {})),
        "complexity": MockComplexityTool(runner.config.get("complexity", {})),
    }

    return runner


def demonstrate_quality_runner() -> dict[str, QualityResult]:
    """Demonstrate the QualityRunner functionality."""
    print("=" * 50)

    # Setup
    target_path = Path("src/provide/testkit")
    runner = setup_mock_runner()

    print(f"Target: {target_path}")
    print(f"Tools: {list(runner.tool_instances.keys())}")
    print()

    # Run analysis
    print("Running analysis...")
    results = runner.run_all(target_path)

    # Display results
    print("📊 Results:")
    for tool_name, result in results.items():
        status_text = "PASSED" if result.passed else "FAILED"
        print(f"  {tool_name}: {status_text} (Score: {result.score:.1f}%)")

    print()
    return results


def demonstrate_quality_gates() -> None:
    """Demonstrate quality gates functionality."""
    print("🚪 Quality Gates Demonstration")
    print("=" * 50)

    target_path = Path("src/provide/testkit")
    runner = setup_mock_runner()

    # Define quality gates
    gates = {
        "coverage": 80.0,  # Require 80% coverage
        "security": 90.0,  # Require 90% security score
        "complexity": {"max_complexity": 12, "min_score": 75.0},  # Complex gate
    }

    print(f"Gates: {gates}")
    print()

    # Run with gates
    print("Running with quality gates...")
    gate_results = runner.run_with_gates(target_path, gates)

    if gate_results.failed_gates:
        print(f"Failed Gates: {', '.join(gate_results.failed_gates)}")

    print()
    return gate_results.results


def demonstrate_report_generation(results: dict[str, QualityResult]) -> None:
    """Demonstrate report generation in multiple formats."""
    print("📝 Report Generation Demonstration")
    print("=" * 50)

    # Setup reports directory
    reports_dir = Path("quality-reports")
    reports_dir.mkdir(exist_ok=True)

    report_gen = ReportGenerator()

    # Generate different format reports
    formats = ["terminal", "json", "html", "markdown"]

    for format_name in formats:
        print(f"  Generating {format_name} report...")

        report_content = report_gen.generate(results, format_name)

        # Save to file
        if format_name == "terminal":
            output_file = reports_dir / "report.txt"
        elif format_name == "json":
            output_file = reports_dir / "report.json"
        elif format_name == "html":
            output_file = reports_dir / "report.html"
        elif format_name == "markdown":
            output_file = reports_dir / "report.md"

        output_file.write_text(report_content)
        print(f"    Saved: {output_file}")

    print()


def demonstrate_artifact_management(results: dict[str, QualityResult]) -> None:
    """Demonstrate artifact management."""
    print("📚 Artifact Management Demonstration")
    print("=" * 50)

    # Setup artifact manager
    artifact_manager = ArtifactManager("quality-reports/artifacts")

    # Create organized directories
    for tool_name in results:
        artifact_manager.create_session_dir(tool_name)
        artifact_manager.create_timestamped_dir(tool_name)
        print(f"  Created directories for {tool_name}")

    # Generate summary report
    summary_path = artifact_manager.create_summary_report(results)
    print(f"  Summary report: {summary_path}")

    # Generate index
    index_path = artifact_manager.generate_index()
    print(f"  Artifact index: {index_path}")

    # Show disk usage
    usage = artifact_manager.get_disk_usage()
    print(f"  Disk usage: {usage['total_mb']:.2f} MB")

    print()


def create_comprehensive_demo() -> None:
    """Create a comprehensive demonstration output."""
    reports_dir = Path("quality-reports")
    reports_dir.mkdir(exist_ok=True)

    # Create README
    readme_content = f"""# Quality Framework Demonstration

This directory contains a comprehensive demonstration of the provide-testkit quality framework.

## Generated Files

### Reports
- `report.txt` - Terminal-style report
- `report.json` - JSON data format
- `report.html` - HTML dashboard
- `report.md` - Markdown summary

### Artifacts
- `artifacts/` - Tool artifacts and metadata
- `artifacts/index.json` - Comprehensive artifact index

## Framework Features Demonstrated

- **Coverage Analysis**: Mock tool simulating coverage.py integration
- **Security Scanning**: Mock tool simulating bandit integration
- **Complexity Analysis**: Mock tool simulating radon integration

- Configurable thresholds for each tool
- Boolean, numeric, and complex gate requirements
- Fail-fast option for CI/CD pipelines

- Multiple output formats (Terminal, JSON, HTML, Markdown)
- Tool-specific and aggregate reporting
- Rich formatting with status indicators

- Organized storage with timestamped directories
- Comprehensive indexing and metadata
- Disk usage tracking and cleanup utilities

- Pytest fixtures for easy test integration
- Quality decorators for function-level requirements
- CLI interface for command-line usage
- Lazy loading for performance optimization

## Real Implementation

This demonstration uses mock tools to show framework functionality.
The real implementation includes:

- **coverage.py** integration for code coverage
- **bandit** integration for security scanning
- **radon** integration for complexity analysis
- **interrogate** integration for documentation coverage
- **memray/cProfile** integration for performance profiling

Generated on: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

    (reports_dir / "README.md").write_text(readme_content)
    print(f"📋 Comprehensive demo documentation: {reports_dir / 'README.md'}")


def main() -> None:
    """Main demonstration function."""
    print("🚀 Provide-Testkit Quality Framework Demo")
    print("=" * 60)
    print()

    # 1. Demonstrate Quality Runner
    results = demonstrate_quality_runner()

    # 2. Demonstrate Quality Gates
    demonstrate_quality_gates()

    # 3. Demonstrate Report Generation
    demonstrate_report_generation(results)

    # 4. Demonstrate Artifact Management
    demonstrate_artifact_management(results)

    # 5. Create comprehensive demo documentation
    create_comprehensive_demo()

    # Final summary
    print("🎉 Quality Framework Demonstration Complete!")
    print("=" * 60)
    print()
    print("🌐 View quality-reports/report.html in your browser")
    print("📋 See quality-reports/README.md for complete overview")
    print()

    # Show what was actually demonstrated
    print("   • Quality tool orchestration")
    print("   • Quality gates with thresholds")
    print("   • Multi-format report generation")
    print("   • Artifact management system")
    print("   • Framework extensibility")
    print()


if __name__ == "__main__":
    main()

# 🧪✅🔚
