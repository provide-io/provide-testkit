#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Semgrep pattern-based static analysis security scanner implementation."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from provide.foundation.errors.process import ProcessError
from provide.foundation.file import atomic_write_text, ensure_dir
from provide.foundation.process import run
from provide.testkit.quality.base import QualityResult, QualityToolError


def _check_semgrep_available() -> bool:
    """Check if semgrep is available."""
    try:
        result = run(
            ["semgrep", "--version"],
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (ProcessError, TimeoutError):
        return False


SEMGREP_AVAILABLE = _check_semgrep_available()


class SemgrepScanner:
    """Pattern-based static analysis security scanner using Semgrep.

    Scans code for security vulnerabilities, bugs, and anti-patterns
    using customizable pattern rules. Supports many languages including
    Python, JavaScript, Go, Java, and more.
    """

    # Default config file location
    DEFAULT_CONFIG_PATH = Path(".provide/security/semgrep.yml")

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize Semgrep scanner.

        Args:
            config: Scanner configuration options. If "config" is not specified,
                    will auto-detect .provide/security/semgrep.yml if it exists.
        """
        if not SEMGREP_AVAILABLE:
            raise QualityToolError(
                "Semgrep not available. Install with: uv tool install semgrep",
                tool="semgrep",
            )

        self.config = config or {}
        self.artifact_dir: Path | None = None

        # Auto-detect config file if not explicitly specified
        if "config" not in self.config:
            default_config = self._get_default_config_path()
            if default_config:
                self.config["config"] = [str(default_config)]

    def _get_default_config_path(self) -> Path | None:
        """Get default config file path if it exists."""
        if self.DEFAULT_CONFIG_PATH.exists():
            return self.DEFAULT_CONFIG_PATH
        return None

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        """Run Semgrep analysis on the given path.

        Args:
            path: Path to scan
            **kwargs: Additional options including artifact_dir

        Returns:
            QualityResult with security analysis data
        """
        self.artifact_dir = kwargs.get("artifact_dir", Path(".provide/output/security"))
        start_time = time.time()

        try:
            result = self._run_semgrep_scan(path)
            result.execution_time = time.time() - start_time
            self._generate_artifacts(result)
            return result

        except Exception as e:
            return QualityResult(
                tool="semgrep",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def _add_semgrep_config_options(self, cmd: list[str]) -> None:
        """Add configuration options to semgrep command."""
        if self.config.get("config"):
            for config_item in self.config["config"]:
                cmd.extend(["--config", str(config_item)])
        else:
            cmd.extend(["--config", "auto"])

        if self.config.get("severity"):
            cmd.extend(["--severity", ",".join(self.config["severity"])])

    def _add_semgrep_path_filters(self, cmd: list[str]) -> None:
        """Add path include/exclude filters to semgrep command."""
        if self.config.get("exclude"):
            for pattern in self.config["exclude"]:
                cmd.extend(["--exclude", str(pattern)])
        else:
            for exclude in ["**/test_*", "**/.venv/**", "**/venv/**", "**/__pycache__/**"]:
                cmd.extend(["--exclude", exclude])

        if self.config.get("include"):
            for pattern in self.config["include"]:
                cmd.extend(["--include", str(pattern)])

    def _build_semgrep_command(self, path: Path) -> list[str]:
        """Build Semgrep command with options."""
        cmd = [
            "semgrep",
            "--json",
            "--quiet",
        ]

        self._add_semgrep_config_options(cmd)
        self._add_semgrep_path_filters(cmd)

        if self.config.get("max_memory"):
            cmd.extend(["--max-memory", str(self.config["max_memory"])])

        if self.config.get("timeout_per_rule"):
            cmd.extend(["--timeout", str(self.config["timeout_per_rule"])])

        cmd.append(str(path))

        return cmd

    def _run_semgrep_scan(self, path: Path) -> QualityResult:
        """Run Semgrep scan."""
        try:
            cmd = self._build_semgrep_command(path)

            result = run(
                cmd,
                timeout=self.config.get("timeout", 600),
                check=False,
            )

            # Parse JSON output
            try:
                semgrep_data = json.loads(result.stdout) if result.stdout else {}
            except json.JSONDecodeError:
                semgrep_data = {}

            return self._process_results(semgrep_data, result.returncode)

        except TimeoutError as e:
            raise QualityToolError(f"Semgrep scan timed out: {e!s}", tool="semgrep") from e
        except Exception as e:
            raise QualityToolError(f"Semgrep scan failed: {e!s}", tool="semgrep") from e

    def _process_results(self, semgrep_data: dict[str, Any], returncode: int) -> QualityResult:
        """Process Semgrep results into QualityResult."""
        findings: list[dict[str, Any]] = []

        results = semgrep_data.get("results", [])
        for result_item in results:
            extra = result_item.get("extra", {})
            findings.append(
                {
                    "check_id": result_item.get("check_id", ""),
                    "path": result_item.get("path", ""),
                    "start_line": result_item.get("start", {}).get("line", 0),
                    "end_line": result_item.get("end", {}).get("line", 0),
                    "message": extra.get("message", ""),
                    "severity": extra.get("severity", "INFO"),
                    "metadata": extra.get("metadata", {}),
                    "lines": extra.get("lines", ""),
                }
            )

        total_findings = len(findings)
        max_findings = self.config.get("max_findings", 0)

        # Categorize by severity
        severity_counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        for finding in findings:
            severity = finding.get("severity", "INFO")
            if severity in severity_counts:
                severity_counts[severity] += 1
            else:
                severity_counts["INFO"] += 1

        # Calculate score
        score = 100.0
        score -= severity_counts["ERROR"] * 15
        score -= severity_counts["WARNING"] * 5
        score -= severity_counts["INFO"] * 1
        score = max(0.0, score)

        passed = total_findings <= max_findings

        # Extract errors from semgrep output
        errors = semgrep_data.get("errors", [])

        details = {
            "total_findings": total_findings,
            "severity_breakdown": severity_counts,
            "score": score,
            "findings": findings[:20],
            "errors": errors[:5],
            "returncode": returncode,
        }

        return QualityResult(
            tool="semgrep",
            passed=passed,
            score=score,
            details=details,
        )

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate Semgrep analysis artifacts."""
        if not self.artifact_dir:
            return

        ensure_dir(self.artifact_dir)

        try:
            json_file = self.artifact_dir / "semgrep.json"
            json_data = {
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
                "execution_time": result.execution_time,
            }
            atomic_write_text(json_file, json.dumps(json_data, indent=2))
            result.artifacts.append(json_file)

            summary_file = self.artifact_dir / "semgrep_summary.txt"
            summary_report = self._generate_text_report(result)
            atomic_write_text(summary_file, summary_report)
            result.artifacts.append(summary_file)

        except Exception as e:
            result.details["artifact_error"] = str(e)

    def _generate_text_report(self, result: QualityResult) -> str:
        """Generate text summary report."""
        status_text = "✅ PASSED" if result.passed else "❌ FAILED"
        lines = [
            f"Semgrep Security Analysis Report - {result.tool}",
            "=" * 50,
            f"Status: {status_text}",
            f"Security Score: {result.score}%",
            f"Total Findings: {result.details.get('total_findings', 0)}",
            "",
            "Severity Breakdown:",
        ]

        severity = result.details.get("severity_breakdown", {})
        for level, count in severity.items():
            if count > 0:
                lines.append(f"  {level}: {count}")

        lines.append("")

        findings = result.details.get("findings", [])
        if findings:
            lines.append("Findings:")
            for finding in findings[:10]:
                lines.extend(
                    [
                        f"  - {finding['check_id']}",
                        f"    File: {finding['path']}:{finding['start_line']}",
                        f"    Severity: {finding['severity']}",
                        f"    Message: {finding['message'][:100]}..."
                        if len(finding.get("message", "")) > 100
                        else f"    Message: {finding.get('message', '')}",
                        "",
                    ]
                )

        if result.execution_time:
            lines.append(f"Execution Time: {result.execution_time:.2f}s")

        return "\n".join(lines)

    def report(self, result: QualityResult, format: str = "terminal") -> str:
        """Generate report from QualityResult."""
        if format == "terminal":
            return self._generate_text_report(result)
        elif format == "json":
            return json.dumps(
                {
                    "tool": result.tool,
                    "passed": result.passed,
                    "score": result.score,
                    "details": result.details,
                },
                indent=2,
            )
        else:
            return str(result.details)


# 🧪✅🔚
