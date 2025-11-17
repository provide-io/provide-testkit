#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Checkov Infrastructure as Code security scanner implementation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time
from typing import Any

from provide.foundation.file import atomic_write_text, ensure_dir

from ..base import QualityResult, QualityToolError


def _check_checkov_available() -> bool:
    """Check if checkov is available."""
    try:
        result = subprocess.run(
            ["checkov", "--version"],
            capture_output=True,
            text=True,
            timeout=30,  # Checkov can be slow to start
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


CHECKOV_AVAILABLE = _check_checkov_available()


class CheckovScanner:
    """Infrastructure as Code security scanner using Checkov.

    Scans Terraform, CloudFormation, Kubernetes, Dockerfile,
    Python, and other IaC configurations for misconfigurations
    and security issues.
    """

    # Default config file location
    DEFAULT_CONFIG_PATH = Path(".provide/security/checkov.yml")

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize Checkov scanner.

        Args:
            config: Scanner configuration options. If "config_file" is not specified,
                    will auto-detect .provide/security/checkov.yml if it exists.
        """
        if not CHECKOV_AVAILABLE:
            raise QualityToolError(
                "Checkov not available. Install with: pip install checkov",
                tool="checkov",
            )

        self.config = config or {}
        self.artifact_dir: Path | None = None

        # Auto-detect config file if not explicitly specified
        if "config_file" not in self.config:
            default_config = self._get_default_config_path()
            if default_config:
                self.config["config_file"] = default_config

    def _get_default_config_path(self) -> Path | None:
        """Get default config file path if it exists."""
        if self.DEFAULT_CONFIG_PATH.exists():
            return self.DEFAULT_CONFIG_PATH
        return None

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        """Run Checkov analysis on the given path.

        Args:
            path: Path to scan for IaC misconfigurations
            **kwargs: Additional options including artifact_dir

        Returns:
            QualityResult with IaC security analysis data
        """
        self.artifact_dir = kwargs.get("artifact_dir", Path(".provide/output/security"))
        start_time = time.time()

        try:
            result = self._run_checkov_scan(path)
            result.execution_time = time.time() - start_time
            self._generate_artifacts(result)
            return result

        except Exception as e:
            return QualityResult(
                tool="checkov",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def _build_checkov_command(self, path: Path) -> list[str]:
        """Build Checkov command with options."""
        cmd = [
            "checkov",
            "--directory" if path.is_dir() else "--file",
            str(path),
            "--output",
            "json",
            "--compact",
        ]

        # Add config file if specified
        if self.config.get("config_file"):
            config_path = Path(self.config["config_file"])
            if config_path.exists():
                cmd.extend(["--config-file", str(config_path)])

        # Add framework filters
        if self.config.get("framework"):
            cmd.extend(["--framework", ",".join(self.config["framework"])])
        else:
            # Default to common frameworks
            cmd.extend(["--framework", "all"])

        # Add check filters
        if self.config.get("check"):
            cmd.extend(["--check", ",".join(self.config["check"])])

        if self.config.get("skip_check"):
            cmd.extend(["--skip-check", ",".join(self.config["skip_check"])])

        # Add path exclusions
        if self.config.get("skip_path"):
            for skip in self.config["skip_path"]:
                cmd.extend(["--skip-path", str(skip)])

        # Soft fail option
        if self.config.get("soft_fail", False):
            cmd.append("--soft-fail")

        # Quiet mode
        if self.config.get("quiet", True):
            cmd.append("--quiet")

        return cmd

    def _run_checkov_scan(self, path: Path) -> QualityResult:
        """Run Checkov scan."""
        try:
            cmd = self._build_checkov_command(path)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.get("timeout", 600),  # Checkov can be slow
                check=False,
            )

            # Parse JSON output
            try:
                checkov_data = json.loads(result.stdout) if result.stdout else {}
            except json.JSONDecodeError:
                checkov_data = {}

            return self._process_results(checkov_data, result.returncode)

        except subprocess.TimeoutExpired as e:
            raise QualityToolError(f"Checkov scan timed out: {e!s}", tool="checkov") from e
        except Exception as e:
            raise QualityToolError(f"Checkov scan failed: {e!s}", tool="checkov") from e

    def _process_results(self, checkov_data: dict[str, Any] | list[Any], returncode: int) -> QualityResult:
        """Process Checkov results into QualityResult."""
        failed_checks: list[dict[str, Any]] = []
        passed_checks = 0
        skipped_checks = 0

        # Handle both single and multi-framework results
        results_list = checkov_data if isinstance(checkov_data, list) else [checkov_data]

        for framework_result in results_list:
            if not isinstance(framework_result, dict):
                continue

            check_type = framework_result.get("check_type", "unknown")

            # Process failed checks
            for failed in framework_result.get("results", {}).get("failed_checks", []):
                failed_checks.append(
                    {
                        "check_type": check_type,
                        "check_id": failed.get("check_id", ""),
                        "check_name": failed.get("check", {}).get("name", ""),
                        "file_path": failed.get("file_path", ""),
                        "resource": failed.get("resource", ""),
                        "guideline": failed.get("guideline", ""),
                        "severity": failed.get("severity", "UNKNOWN"),
                    }
                )

            # Count passed and skipped
            passed_checks += len(framework_result.get("results", {}).get("passed_checks", []))
            skipped_checks += len(framework_result.get("results", {}).get("skipped_checks", []))

        total_failed = len(failed_checks)
        max_failed = self.config.get("max_failed_checks", 0)

        # Categorize by severity
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
        for check in failed_checks:
            severity = check.get("severity", "UNKNOWN")
            if severity in severity_counts:
                severity_counts[severity] += 1
            else:
                severity_counts["UNKNOWN"] += 1

        # Calculate score
        score = 100.0
        score -= severity_counts["CRITICAL"] * 20
        score -= severity_counts["HIGH"] * 10
        score -= severity_counts["MEDIUM"] * 5
        score -= severity_counts["LOW"] * 2
        score = max(0.0, score)

        passed = total_failed <= max_failed

        details = {
            "total_passed": passed_checks,
            "total_failed": total_failed,
            "total_skipped": skipped_checks,
            "severity_breakdown": severity_counts,
            "score": score,
            "failed_checks": failed_checks[:20],
            "returncode": returncode,
        }

        return QualityResult(
            tool="checkov",
            passed=passed,
            score=score,
            details=details,
        )

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate Checkov analysis artifacts."""
        if not self.artifact_dir:
            return

        ensure_dir(self.artifact_dir)

        try:
            json_file = self.artifact_dir / "checkov.json"
            json_data = {
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
                "execution_time": result.execution_time,
            }
            atomic_write_text(json_file, json.dumps(json_data, indent=2))
            result.artifacts.append(json_file)

            summary_file = self.artifact_dir / "checkov_summary.txt"
            summary_report = self._generate_text_report(result)
            atomic_write_text(summary_file, summary_report)
            result.artifacts.append(summary_file)

        except Exception as e:
            result.details["artifact_error"] = str(e)

    def _generate_text_report(self, result: QualityResult) -> str:
        """Generate text summary report."""
        status_text = "✅ PASSED" if result.passed else "❌ FAILED"
        lines = [
            f"Checkov IaC Security Report - {result.tool}",
            "=" * 50,
            f"Status: {status_text}",
            f"Security Score: {result.score}%",
            f"Checks Passed: {result.details.get('total_passed', 0)}",
            f"Checks Failed: {result.details.get('total_failed', 0)}",
            f"Checks Skipped: {result.details.get('total_skipped', 0)}",
            "",
            "Severity Breakdown:",
        ]

        severity = result.details.get("severity_breakdown", {})
        for level, count in severity.items():
            if count > 0:
                lines.append(f"  {level}: {count}")

        lines.append("")

        failed = result.details.get("failed_checks", [])
        if failed:
            lines.append("Failed Checks:")
            for check in failed[:10]:
                lines.extend(
                    [
                        f"  - {check['check_id']}: {check['check_name']}",
                        f"    File: {check['file_path']}",
                        f"    Resource: {check['resource']}",
                        f"    Severity: {check['severity']}",
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
