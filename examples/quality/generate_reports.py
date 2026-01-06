#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Demonstration script for the provide-testkit quality module.

This script runs all quality tools on the testkit itself and generates
comprehensive reports in multiple formats to prove the implementation works."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

from provide.testkit.quality.artifacts import ArtifactManager
from provide.testkit.quality.report import ReportGenerator
from provide.testkit.quality.runner import QualityRunner


def install_quality_tools() -> None:
    """Install required quality tools."""
    import subprocess

    tools = [
        "coverage[toml]",
        "bandit[toml]",
        "radon",
        "interrogate",
        # Note: memray is optional and complex to install
    ]

    for tool in tools:
        try:
            print(f"  Installing {tool}...")
            subprocess.run(["uv", "tool", "install", tool], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Failed to install {tool}: {e}")
            print(f"     Error output: {e.stderr}")
    print()


def create_quality_config() -> dict[str, object]:
    """Create configuration for quality tools."""
    return {
        "coverage": {
            "min_coverage": 70.0,
            "generate_html": True,
            "generate_xml": True,
            "exclude": ["*/tests/*", "*/test_*", "*/__pycache__/*", "*/examples/*"],
        },
        "security": {
            "min_score": 85.0,
            "ignore_issues": [
                "B101",  # assert_used - OK in tests
                "B603",  # subprocess_without_shell_equals_true
            ],
        },
        "complexity": {
            "max_complexity": 15,
            "min_grade": "C",
            "min_score": 70.0,
            "exclude": ["*/tests/*", "*/examples/*"],
        },
        "documentation": {
            "min_coverage": 60.0,
            "min_grade": "C",
            "min_score": 60.0,
            "ignore_init_method": True,
            "ignore_magic": True,
            "ignore_setters": True,
            "ignore": [
                "__pycache__",
                "*.pyc",
                "test_*",
                "tests/*",
                "*/.venv/*",
                "*/venv/*",
                "*/workenv/*",
                "*/examples/*",
            ],
        },
    }


def setup_reports_directory() -> Path:
    """Setup the quality reports directory structure."""
    reports_dir = Path("quality-reports")

    # Create directory structure
    subdirs = ["summary", "coverage", "security", "complexity", "documentation", "profiling", "artifacts"]

    for subdir in subdirs:
        (reports_dir / subdir).mkdir(parents=True, exist_ok=True)

    return reports_dir


def run_quality_analysis(reports_dir: Path) -> dict[str, object]:
    """Run comprehensive quality analysis."""
    print("🔍 Running Quality Analysis")
    print("=" * 50)

    # Source directory to analyze
    source_path = Path("src/provide/testkit")

    # Setup quality runner with configuration
    config = create_quality_config()
    runner = QualityRunner(artifact_root=reports_dir / "artifacts", config=config)

    # Available tools (some may not be installed)
    tools_to_try = ["coverage", "security", "complexity", "documentation"]

    print(f"Analyzing: {source_path}")
    print(f"Tools to run: {', '.join(tools_to_try)}")
    print()

    # Run analysis
    start_time = time.time()
    results = runner.run_tools(source_path, tools=tools_to_try, artifact_dir=reports_dir / "artifacts")

    analysis_time = time.time() - start_time

    # Print immediate results
    print("📊 Analysis Results:")
    print("-" * 30)

    for tool_name, result in results.items():
        status_text = "PASSED" if result.passed else "FAILED"
        score_text = f" ({result.score:.1f}%)" if result.score else ""
        time_text = f" [{result.execution_time:.2f}s]" if result.execution_time else ""

        print(f"{tool_name.title()}: {status_text}{score_text}{time_text}")

        # Show key details
        if tool_name == "coverage" and "coverage_percentage" in result.details:
            print(f"  Coverage: {result.details['coverage_percentage']:.1f}%")
        elif tool_name == "security" and "total_issues" in result.details:
            print(f"  Issues: {result.details['total_issues']}")
        elif tool_name == "complexity" and "average_complexity" in result.details:
            print(f"  Avg Complexity: {result.details['average_complexity']:.1f}")
            print(f"  Grade: {result.details.get('overall_grade', 'N/A')}")
        elif tool_name == "documentation" and "total_coverage" in result.details:
            print(f"  Doc Coverage: {result.details['total_coverage']:.1f}%")

    print(f"\nTotal analysis time: {analysis_time:.2f} seconds")
    print()

    return results


def generate_comprehensive_reports(results: dict[str, object], reports_dir: Path) -> None:
    """Generate comprehensive reports in multiple formats."""
    print("📝 Generating Comprehensive Reports")
    print("=" * 50)

    # Initialize report generator
    report_gen = ReportGenerator()

    # Generate summary reports
    summary_dir = reports_dir / "summary"

    # 1. JSON Report (comprehensive data)
    json_report = report_gen.generate(results, "json")
    (summary_dir / "overall_report.json").write_text(json_report)

    # 2. HTML Dashboard
    print("  🌐 Generating HTML dashboard...")
    html_report = report_gen.generate(results, "html")
    (summary_dir / "dashboard.html").write_text(html_report)

    # 3. Markdown Summary
    print("  📋 Generating Markdown summary...")
    md_report = report_gen.generate(results, "markdown")
    (summary_dir / "README.md").write_text(md_report)

    # 4. Terminal Report (for logs)
    print("  💻 Generating terminal report...")
    terminal_report = report_gen.generate(results, "terminal")
    (summary_dir / "terminal_output.txt").write_text(terminal_report)

    # Generate tool-specific reports
    for tool_name, result in results.items():
        tool_dir = reports_dir / tool_name

        # Tool-specific JSON
        tool_json = {
            "tool": result.tool,
            "passed": result.passed,
            "score": result.score,
            "execution_time": result.execution_time,
            "details": result.details,
            "artifacts": [str(p) for p in result.artifacts],
        }
        (tool_dir / f"{tool_name}_report.json").write_text(json.dumps(tool_json, indent=2))

        # Tool-specific analysis
        if tool_name == "coverage":
            generate_coverage_analysis(result, tool_dir)
        elif tool_name == "security":
            generate_security_analysis(result, tool_dir)
        elif tool_name == "complexity":
            generate_complexity_analysis(result, tool_dir)
        elif tool_name == "documentation":
            generate_documentation_analysis(result, tool_dir)

    print()


def generate_coverage_analysis(result: any, output_dir: Path) -> None:
    """Generate detailed coverage analysis."""
    details = result.details

    # Coverage summary
    summary = f"""# Coverage Analysis Report

## Summary
- **Overall Coverage**: {details.get("coverage_percentage", 0):.1f}%
- **Lines Covered**: {details.get("lines_covered", 0)}
- **Lines Missing**: {details.get("lines_missing", 0)}
- **Total Lines**: {details.get("total_lines", 0)}

## Status
- **Score**: {result.score:.1f}%

## Artifacts
"""

    for artifact in result.artifacts:
        summary += f"- `{artifact}`\n"

    (output_dir / "coverage_summary.md").write_text(summary)


def generate_security_analysis(result: any, output_dir: Path) -> None:
    """Generate detailed security analysis."""
    details = result.details

    # Security summary
    summary = f"""# Security Analysis Report

## Summary
- **Security Score**: {result.score:.1f}%
- **Total Issues**: {details.get("total_issues", 0)}

## Issue Breakdown
"""

    if "severity_counts" in details:
        for severity, count in details["severity_counts"].items():
            summary += f"- **{severity}**: {count} issues\n"

    if details.get("issues"):
        summary += "\n## Top Issues\n"
        for i, issue in enumerate(details["issues"][:5], 1):
            summary += f"{i}. **{issue.get('test_id', 'Unknown')}** ({issue.get('severity', 'Unknown')})\n"
            summary += f"   - File: `{issue.get('filename', 'Unknown')}`\n"
            summary += f"   - Line: {issue.get('line_number', 'Unknown')}\n\n"

    (output_dir / "security_summary.md").write_text(summary)


def generate_complexity_analysis(result: any, output_dir: Path) -> None:
    """Generate detailed complexity analysis."""
    details = result.details

    # Complexity summary
    summary = f"""# Complexity Analysis Report

## Summary
- **Overall Grade**: {details.get("overall_grade", "N/A")}
- **Average Complexity**: {details.get("average_complexity", 0):.1f}
- **Max Complexity**: {details.get("max_complexity", 0)}
- **Total Functions**: {details.get("total_functions", 0)}
- **Score**: {result.score:.1f}%

## Grade Breakdown
"""

    if "grade_breakdown" in details:
        for grade, count in details["grade_breakdown"].items():
            if count > 0:
                summary += f"- **Grade {grade}**: {count} functions\n"

    if "most_complex_functions" in details:
        summary += "\n## Most Complex Functions\n"
        for i, func in enumerate(details["most_complex_functions"][:5], 1):
            summary += f"{i}. **{func['name']}** (Complexity: {func['complexity']}, Grade: {func['rank']})\n"
            summary += f"   - File: `{func['file']}:{func['lineno']}`\n\n"

    (output_dir / "complexity_summary.md").write_text(summary)


def generate_documentation_analysis(result: any, output_dir: Path) -> None:
    """Generate detailed documentation analysis."""
    details = result.details

    # Documentation summary
    summary = f"""# Documentation Coverage Report

## Summary
- **Documentation Coverage**: {details.get("total_coverage", 0):.1f}%
- **Grade**: {details.get("grade", "N/A")}
- **Documented Items**: {details.get("covered_count", 0)}
- **Missing Documentation**: {details.get("missing_count", 0)}
- **Total Items**: {details.get("total_count", 0)}

## Status
- **Score**: {result.score:.1f}%

## File Coverage
"""

    if "file_coverage" in details:
        min_coverage = details.get("thresholds", {}).get("min_coverage", 0.0)
        for file_info in details["file_coverage"][:10]:  # Top 10 files
            coverage = file_info["coverage"]
            status_icon = "✅" if coverage >= min_coverage else "⚠️"
            summary += (
                f"- {status_icon} `{file_info['file']}`: {coverage:.1f}% "
                f"({file_info['covered']}/{file_info['covered'] + file_info['missing']})\n"
            )

    (output_dir / "documentation_summary.md").write_text(summary)


def create_artifact_index(results: dict[str, object], reports_dir: Path) -> None:
    """Create a comprehensive artifact index."""
    print("📚 Creating Artifact Index")
    print("=" * 30)

    # Use ArtifactManager to create index
    artifact_manager = ArtifactManager(reports_dir / "artifacts")

    # Generate index
    index_path = artifact_manager.generate_index()
    print(f"  📋 Artifact index: {index_path}")

    # Get disk usage
    usage = artifact_manager.get_disk_usage()
    print(f"  💾 Total artifacts: {usage['total_mb']:.2f} MB")

    # Create summary report
    summary_path = artifact_manager.create_summary_report(results)
    print(f"  📊 Summary report: {summary_path}")

    print()


def create_master_index(reports_dir: Path) -> None:
    """Create master index of all reports."""
    index_content = f"""# Quality Analysis Reports

Generated on: {time.strftime("%Y-%m-%d %H:%M:%S")}

## 📊 Summary Reports
- [HTML Dashboard](summary/dashboard.html) - Interactive overview
- [JSON Report](summary/overall_report.json) - Complete data
- [Markdown Summary](summary/README.md) - Human-readable overview
- [Terminal Output](summary/terminal_output.txt) - CLI-style report


### Coverage Analysis
- [Coverage Report](coverage/coverage_report.json)
- [Coverage Summary](coverage/coverage_summary.md)

### Security Analysis
- [Security Report](security/security_report.json)
- [Security Summary](security/security_summary.md)

### Complexity Analysis
- [Complexity Report](complexity/complexity_report.json)
- [Complexity Summary](complexity/complexity_summary.md)

### Documentation Analysis
- [Documentation Report](documentation/documentation_report.json)
- [Documentation Summary](documentation/documentation_summary.md)

- [Artifact Index](artifacts/index.json)
- [Generated Files](artifacts/)

## 🎯 Quick Links
- View the [HTML Dashboard](summary/dashboard.html) for the best overview
- Check [JSON Report](summary/overall_report.json) for programmatic access
- Browse tool-specific summaries for detailed analysis

---
*Generated by provide-testkit quality module*
"""

    (reports_dir / "index.md").write_text(index_content)
    print(f"📋 Master index created: {reports_dir / 'index.md'}")


def main() -> None:
    """Main demonstration function."""
    print("🚀 Provide-Testkit Quality Module Demonstration")
    print("=" * 60)
    print()

    # Install required tools
    install_quality_tools()

    # Setup reports directory
    reports_dir = setup_reports_directory()
    print()

    # Run quality analysis
    results = run_quality_analysis(reports_dir)

    # Generate comprehensive reports
    generate_comprehensive_reports(results, reports_dir)

    # Create artifact index
    create_artifact_index(results, reports_dir)

    # Create master index
    create_master_index(reports_dir)

    # Final summary
    print("🎉 Quality Analysis Complete!")
    print("=" * 40)
    print(f"🌐 Open {reports_dir / 'summary' / 'dashboard.html'} in your browser")
    print(f"📋 See {reports_dir / 'index.md'} for complete overview")

    # Show final statistics
    total_tools = len(results)
    passed_tools = sum(1 for r in results.values() if r.passed)

    print("\n📊 Final Statistics:")
    print(f"   Tools run: {total_tools}")
    print(f"   Tools passed: {passed_tools}")
    print(f"   Success rate: {(passed_tools / total_tools) * 100:.1f}%")


if __name__ == "__main__":
    main()

# 🧪✅🔚
