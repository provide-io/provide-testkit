"""Report generation for quality analysis results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from provide.foundation.file import atomic_write_text, ensure_dir

from .base import QualityResult


class ReportGenerator:
    """Generates reports from quality analysis results.

    Supports multiple output formats including terminal, JSON, HTML, and Markdown.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize report generator.

        Args:
            config: Configuration for report generation
        """
        self.config = config or {}

    def generate(self, results: dict[str, QualityResult], format: str = "terminal") -> str:
        """Generate a report from quality results.

        Args:
            results: Quality results to report on
            format: Output format (terminal, json, html, markdown)

        Returns:
            Formatted report string
        """
        if format == "terminal":
            return self._generate_terminal_report(results)
        elif format == "json":
            return self._generate_json_report(results)
        elif format == "html":
            return self._generate_html_report(results)
        elif format == "markdown":
            return self._generate_markdown_report(results)
        else:
            raise ValueError(f"Unsupported report format: {format}")

    def _generate_terminal_report(self, results: dict[str, QualityResult]) -> str:
        """Generate terminal-friendly report."""
        lines = []
        lines.append("🔍 Quality Analysis Report")
        lines.append("=" * 50)
        lines.append("")

        # Summary
        total = len(results)
        passed = sum(1 for r in results.values() if r.passed)
        failed = total - passed

        lines.append(f"📊 Summary: {passed}/{total} tools passed")
        if failed > 0:
            lines.append(f"❌ {failed} tools failed")
        lines.append("")

        # Individual results
        for tool_name, result in results.items():
            lines.append(self._format_tool_result(result))

        # Details for failed tools
        failed_results = {name: result for name, result in results.items() if not result.passed}
        if failed_results:
            lines.append("")
            lines.append("🔍 Failure Details:")
            lines.append("-" * 30)
            for tool_name, result in failed_results.items():
                lines.append(f"\n{tool_name}:")
                if "error" in result.details:
                    lines.append(f"  Error: {result.details['error']}")
                for key, value in result.details.items():
                    if key != "error":
                        lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def _format_tool_result(self, result: QualityResult) -> str:
        """Format a single tool result for terminal display."""
        status_icon = "✅" if result.passed else "❌"
        score_text = f" ({result.score:.1f}%)" if result.score is not None else ""
        time_text = f" [{result.execution_time:.2f}s]" if result.execution_time is not None else ""

        return f"{status_icon} {result.tool.title()}{score_text}{time_text}"

    def _generate_json_report(self, results: dict[str, QualityResult]) -> str:
        """Generate JSON report."""
        report_data: dict[str, Any] = {
            "summary": {
                "total_tools": len(results),
                "passed": sum(1 for r in results.values() if r.passed),
                "failed": sum(1 for r in results.values() if not r.passed),
                "overall_score": self._calculate_overall_score(results),
            },
            "results": {},
        }

        for tool_name, result in results.items():
            report_data["results"][tool_name] = {
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "execution_time": result.execution_time,
                "details": result.details,
                "artifacts": [str(path) for path in result.artifacts],
            }

        return json.dumps(report_data, indent=2)

    def _generate_html_report(self, results: dict[str, QualityResult]) -> str:
        """Generate HTML report."""
        overall_score = self._calculate_overall_score(results)
        passed_count = sum(1 for r in results.values() if r.passed)
        total_count = len(results)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Quality Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .tool-result {{ margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .passed {{ background: #d4edda; border-left: 4px solid #28a745; }}
        .failed {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
        .score {{ font-weight: bold; }}
        .details {{ margin-top: 10px; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Quality Analysis Report</h1>
        <div class="summary">
            <p><strong>Overall Score:</strong> {overall_score:.1f}%</p>
            <p><strong>Tools Passed:</strong> {passed_count}/{total_count}</p>
        </div>
    </div>
"""

        for tool_name, result in results.items():
            status_class = "passed" if result.passed else "failed"
            score_text = f" ({result.score:.1f}%)" if result.score is not None else ""

            html += f"""
    <div class="tool-result {status_class}">
        <h3>{result.tool.title()}{score_text}</h3>
        <p class="score">Status: {"✅ PASSED" if result.passed else "❌ FAILED"}</p>
"""

            if result.details:
                html += '<div class="details"><strong>Details:</strong><ul>'
                for key, value in result.details.items():
                    html += f"<li><strong>{key}:</strong> {value}</li>"
                html += "</ul></div>"

            html += "    </div>"

        html += """
</body>
</html>"""

        return html

    def _generate_markdown_report(self, results: dict[str, QualityResult]) -> str:
        """Generate Markdown report."""
        lines = []
        lines.append("# 🔍 Quality Analysis Report")
        lines.append("")

        # Summary
        total = len(results)
        passed = sum(1 for r in results.values() if r.passed)
        overall_score = self._calculate_overall_score(results)

        lines.append("## 📊 Summary")
        lines.append("")
        lines.append(f"- **Overall Score:** {overall_score:.1f}%")
        lines.append(f"- **Tools Passed:** {passed}/{total}")
        lines.append("")

        # Results table
        lines.append("## 📋 Results")
        lines.append("")
        lines.append("| Tool | Status | Score | Time |")
        lines.append("|------|--------|-------|------|")

        for tool_name, result in results.items():
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            score = f"{result.score:.1f}%" if result.score is not None else "N/A"
            time = f"{result.execution_time:.2f}s" if result.execution_time is not None else "N/A"
            lines.append(f"| {result.tool.title()} | {status} | {score} | {time} |")

        # Failed tool details
        failed_results = {name: result for name, result in results.items() if not result.passed}
        if failed_results:
            lines.append("")
            lines.append("## ❌ Failure Details")
            lines.append("")

            for tool_name, result in failed_results.items():
                lines.append(f"### {result.tool.title()}")
                lines.append("")
                for key, value in result.details.items():
                    lines.append(f"- **{key}:** {value}")
                lines.append("")

        return "\n".join(lines)

    def _calculate_overall_score(self, results: dict[str, QualityResult]) -> float:
        """Calculate overall quality score from all results.

        Args:
            results: Quality results

        Returns:
            Overall score (0-100)
        """
        if not results:
            return 0.0

        # Weight passing vs failing (passing gets base score)
        scores = []
        for result in results.values():
            if result.passed:
                # Use tool score if available, otherwise 100 for passing
                scores.append(result.score if result.score is not None else 100.0)
            else:
                # Failing tools get 0
                scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0

    def save_report(
        self, results: dict[str, QualityResult], output_path: Path, format: str | None = None
    ) -> None:
        """Save report to file.

        Args:
            results: Quality results to report on
            output_path: Path to save report to
            format: Output format (auto-detected from extension if None)
        """
        if format is None:
            # Auto-detect format from file extension
            suffix = output_path.suffix.lower()
            if suffix == ".json":
                format = "json"
            elif suffix == ".html":
                format = "html"
            elif suffix == ".md":
                format = "markdown"
            else:
                format = "terminal"

        report_content = self.generate(results, format)
        ensure_dir(output_path.parent)
        atomic_write_text(output_path, report_content)
