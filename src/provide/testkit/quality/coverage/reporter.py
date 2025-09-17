"""Coverage reporting utilities."""

from __future__ import annotations

from typing import Any

from ..base import QualityResult


class CoverageReporter:
    """Specialized reporter for coverage results."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize coverage reporter.

        Args:
            config: Reporter configuration
        """
        self.config = config or {}

    def format_terminal_report(self, result: QualityResult) -> str:
        """Format coverage result for terminal output.

        Args:
            result: Coverage result to format

        Returns:
            Formatted terminal report
        """
        lines = [
            f"Coverage Report - {result.tool}",
            "=" * 40,
            f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}",
        ]

        if result.score is not None:
            lines.append(f"Coverage: {result.score}%")

        details = result.details
        if "total_statements" in details:
            lines.extend(
                [
                    f"Total Statements: {details.get('total_statements', 0)}",
                    f"Missing Statements: {details.get('missing_statements', 0)}",
                ]
            )

        if "branch_coverage" in details and details["branch_coverage"] is not None:
            lines.append(f"Branch Coverage: {details['branch_coverage']}%")

        if "threshold" in details:
            lines.append(f"Threshold: {details['threshold']}%")

        if result.execution_time:
            lines.append(f"Execution Time: {result.execution_time:.2f}s")

        return "\n".join(lines)

    def format_json_report(self, result: QualityResult) -> dict[str, Any]:
        """Format coverage result as JSON data.

        Args:
            result: Coverage result to format

        Returns:
            JSON-serializable report data
        """
        return {
            "tool": result.tool,
            "passed": result.passed,
            "score": result.score,
            "details": result.details,
            "execution_time": result.execution_time,
            "artifacts": [str(p) for p in result.artifacts],
        }

    def format_html_summary(self, result: QualityResult) -> str:
        """Format coverage result as HTML summary.

        Args:
            result: Coverage result to format

        Returns:
            HTML summary
        """
        status_color = "green" if result.passed else "red"
        status_text = "PASSED" if result.passed else "FAILED"

        html_parts = [
            '<div class="coverage-summary">',
            "<h3>Coverage Report</h3>",
            f'<p><span style="color: {status_color}">Status: {status_text}</span></p>',
        ]

        if result.score is not None:
            html_parts.append(f"<p>Coverage: <strong>{result.score}%</strong></p>")

        details = result.details
        if "total_statements" in details:
            html_parts.extend(
                [
                    f"<p>Total Statements: {details.get('total_statements', 0)}</p>",
                    f"<p>Missing Statements: {details.get('missing_statements', 0)}</p>",
                ]
            )

        html_parts.append("</div>")
        return "\n".join(html_parts)

    def generate_dashboard_data(self, result: QualityResult) -> dict[str, Any]:
        """Generate data for coverage dashboard.

        Args:
            result: Coverage result

        Returns:
            Dashboard data structure
        """
        dashboard_data: dict[str, Any] = {
            "title": "Code Coverage",
            "status": "passed" if result.passed else "failed",
            "primary_metric": {
                "label": "Coverage",
                "value": result.score,
                "unit": "%",
                "threshold": result.details.get("threshold", 0),
            },
            "secondary_metrics": [],
        }

        details = result.details
        secondary_metrics = dashboard_data["secondary_metrics"]
        if "total_statements" in details and isinstance(secondary_metrics, list):
            secondary_metrics.extend(
                [
                    {"label": "Total Statements", "value": details.get("total_statements", 0)},
                    {"label": "Missing Statements", "value": details.get("missing_statements", 0)},
                ]
            )

        if (
            "branch_coverage" in details
            and details["branch_coverage"] is not None
            and isinstance(secondary_metrics, list)
        ):
            secondary_metrics.append(
                {"label": "Branch Coverage", "value": details["branch_coverage"], "unit": "%"}
            )

        return dashboard_data
