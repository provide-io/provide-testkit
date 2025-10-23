"""Mutation testing report generation."""

from __future__ import annotations

import json

from ..base import QualityResult


class MutationReporter:
    """Generate mutation testing reports in various formats."""

    def generate_terminal(self, result: QualityResult) -> str:
        """Generate terminal-friendly report.

        Args:
            result: Mutation test result

        Returns:
            Formatted terminal output
        """
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("🧬 MUTATION TESTING RESULTS")
        lines.append("=" * 60)

        status_icon = "✅" if result.passed else "❌"
        lines.append(f"\nStatus: {status_icon} {'' if result.passed else 'FAILED'}")
        lines.append(f"Score: {result.score:.1f}%")

        if "target_score" in result.details:
            lines.append(f"Target: {result.details['target_score']:.1f}%")

        lines.append("\nMutation Breakdown:")
        lines.append(f"  Total Mutants: {result.details.get('total_mutants', 0)}")
        lines.append(f"  ⚔️  Killed: {result.details.get('killed', 0)}")
        lines.append(f"  🙁 Survived: {result.details.get('survived', 0)}")
        lines.append(f"  ⏰ Timeout: {result.details.get('timeout', 0)}")
        lines.append(f"  🤔 Suspicious: {result.details.get('suspicious', 0)}")

        if result.execution_time:
            lines.append(f"\nExecution Time: {result.execution_time:.1f}s")

        lines.append("=" * 60 + "\n")

        return "\n".join(lines)

    def generate_json(self, result: QualityResult) -> str:
        """Generate JSON report.

        Args:
            result: Mutation test result

        Returns:
            JSON string
        """
        report = {
            "tool": result.tool,
            "passed": result.passed,
            "score": result.score,
            "details": result.details,
            "execution_time": result.execution_time,
            "artifacts": [str(p) for p in result.artifacts],
        }

        return json.dumps(report, indent=2)

    def generate_markdown(self, result: QualityResult) -> str:
        """Generate Markdown report.

        Args:
            result: Mutation test result

        Returns:
            Markdown string
        """
        lines = []
        lines.append("# 🧬 Mutation Testing Results\n")

        status_badge = (
            "![PASSED](https://img.shields.io/badge/status-passed-success)"
            if result.passed
            else "![FAILED](https://img.shields.io/badge/status-failed-critical)"
        )
        score_badge = f"![Score](https://img.shields.io/badge/score-{result.score:.0f}%25-blue)"

        lines.append(f"{status_badge} {score_badge}\n")

        lines.append("## Summary\n")
        lines.append(f"- **Score**: {result.score:.1f}%")

        if "target_score" in result.details:
            lines.append(f"- **Target**: {result.details['target_score']:.1f}%")

        lines.append(f"- **Status**: {'✅ Passed' if result.passed else '❌ Failed'}\n")

        lines.append("## Mutation Breakdown\n")
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Mutants | {result.details.get('total_mutants', 0)} |")
        lines.append(f"| ⚔️ Killed | {result.details.get('killed', 0)} |")
        lines.append(f"| 🙁 Survived | {result.details.get('survived', 0)} |")
        lines.append(f"| ⏰ Timeout | {result.details.get('timeout', 0)} |")
        lines.append(f"| 🤔 Suspicious | {result.details.get('suspicious', 0)} |\n")

        if result.execution_time:
            lines.append(f"**Execution Time**: {result.details.execution_time:.1f}s\n")

        return "\n".join(lines)

    def generate_html(self, result: QualityResult) -> str:
        """Generate HTML report.

        Args:
            result: Mutation test result

        Returns:
            HTML string
        """
        status_class = "success" if result.passed else "failure"
        status_text = "PASSED" if result.passed else "FAILED"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mutation Testing Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .{status_class} {{ color: {"green" if result.passed else "red"}; }}
        .score {{ font-size: 48px; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧬 Mutation Testing Results</h1>
        <div class="{status_class}">
            <span class="score">{result.score:.1f}%</span>
            <h2>{status_text}</h2>
        </div>
    </div>

    <h2>Mutation Breakdown</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Count</th>
        </tr>
        <tr>
            <td>Total Mutants</td>
            <td>{result.details.get("total_mutants", 0)}</td>
        </tr>
        <tr>
            <td>⚔️ Killed</td>
            <td>{result.details.get("killed", 0)}</td>
        </tr>
        <tr>
            <td>🙁 Survived</td>
            <td>{result.details.get("survived", 0)}</td>
        </tr>
        <tr>
            <td>⏰ Timeout</td>
            <td>{result.details.get("timeout", 0)}</td>
        </tr>
        <tr>
            <td>🤔 Suspicious</td>
            <td>{result.details.get("suspicious", 0)}</td>
        </tr>
    </table>

    <p><strong>Execution Time:</strong> {result.execution_time:.1f}s</p>
</body>
</html>
"""

        return html

    def per_module_report(self, results: dict[str, QualityResult]) -> str:
        """Generate per-module report.

        Args:
            results: Dict mapping module paths to results

        Returns:
            Terminal-formatted per-module report
        """
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("🧬 MUTATION TESTING - PER MODULE REPORT")
        lines.append("=" * 70 + "\n")

        for module, result in sorted(results.items()):
            status_icon = "✅" if result.passed else "❌"
            lines.append(f"{status_icon} {module}")
            lines.append(
                f"   Score: {result.score:.1f}% | Killed: {result.details.get('killed', 0)} | "
                f"Survived: {result.details.get('survived', 0)}"
            )
            lines.append("")

        return "\n".join(lines)
