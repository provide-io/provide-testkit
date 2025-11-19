#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""GitLeaks secret detection scanner implementation."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from provide.foundation.errors.process import ProcessError
from provide.foundation.file import atomic_write_text, ensure_dir
from provide.foundation.process import run
from provide.testkit.quality.base import QualityResult, QualityToolError


def _check_gitleaks_available() -> bool:
    """Check if gitleaks is available."""
    try:
        result = run(
            ["gitleaks", "version"],
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (ProcessError, TimeoutError):
        return False


GITLEAKS_AVAILABLE = _check_gitleaks_available()


class GitLeaksScanner:
    """Secret detection scanner using GitLeaks.

    Scans codebases for hardcoded secrets, API keys, passwords,
    and other sensitive information using pattern matching.

    Note: GitLeaks is a Go binary and must be installed separately.
    Install via: brew install gitleaks (macOS) or download from GitHub releases.
    """

    # Default config file location
    DEFAULT_CONFIG_PATH = Path(".provide/security/gitleaks.toml")

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize GitLeaks scanner.

        Args:
            config: Scanner configuration options. If "config_file" is not specified,
                    will auto-detect .provide/security/gitleaks.toml if it exists.
        """
        if not GITLEAKS_AVAILABLE:
            raise QualityToolError(
                "GitLeaks not available. Install with: brew install gitleaks (macOS) "
                "or download from https://github.com/gitleaks/gitleaks/releases",
                tool="gitleaks",
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
        """Run GitLeaks analysis on the given path.

        Args:
            path: Path to scan for secrets
            **kwargs: Additional options including artifact_dir

        Returns:
            QualityResult with secret detection data
        """
        self.artifact_dir = kwargs.get("artifact_dir", Path(".provide/output/security"))
        start_time = time.time()

        try:
            result = self._run_gitleaks_scan(path)
            result.execution_time = time.time() - start_time
            self._generate_artifacts(result)
            return result

        except Exception as e:
            return QualityResult(
                tool="gitleaks",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def _run_gitleaks_scan(self, path: Path) -> QualityResult:
        """Run GitLeaks scan."""
        try:
            ensure_dir(self.artifact_dir or Path(".security"))
            report_file = (self.artifact_dir or Path(".security")) / "gitleaks_raw.json"

            cmd = [
                "gitleaks",
                "detect",
                "--source",
                str(path),
                "--report-format",
                "json",
                "--report-path",
                str(report_file),
                "--no-git",  # Don't require git history
            ]

            # Add configuration options
            if self.config.get("verbose", False):
                cmd.append("--verbose")

            if self.config.get("no_banner", True):
                cmd.append("--no-banner")

            if self.config.get("config_file"):
                cmd.extend(["--config", str(self.config["config_file"])])

            if self.config.get("baseline_path"):
                cmd.extend(["--baseline-path", str(self.config["baseline_path"])])

            result = run(
                cmd,
                timeout=self.config.get("timeout", 300),
                check=False,
            )

            # GitLeaks returns 1 if secrets found, 0 if clean
            # Parse the report file
            findings: list[dict[str, Any]] = []
            if report_file.exists():
                try:
                    with report_file.open() as f:
                        findings = json.load(f)
                except (json.JSONDecodeError, Exception):
                    findings = []

            return self._process_results(findings, result.returncode)

        except TimeoutError as e:
            raise QualityToolError(f"GitLeaks scan timed out: {e!s}", tool="gitleaks") from e
        except Exception as e:
            raise QualityToolError(f"GitLeaks scan failed: {e!s}", tool="gitleaks") from e

    def _process_results(self, findings: list[dict[str, Any]], returncode: int) -> QualityResult:
        """Process GitLeaks results into QualityResult."""
        secrets: list[dict[str, Any]] = []

        for finding in findings:
            secrets.append(
                {
                    "description": finding.get("Description", ""),
                    "file": finding.get("File", ""),
                    "start_line": finding.get("StartLine", 0),
                    "end_line": finding.get("EndLine", 0),
                    "start_column": finding.get("StartColumn", 0),
                    "end_column": finding.get("EndColumn", 0),
                    "match": finding.get("Match", "")[:50] + "..."
                    if len(finding.get("Match", "")) > 50
                    else finding.get("Match", ""),
                    "secret": "***REDACTED***",  # Never expose actual secrets
                    "rule_id": finding.get("RuleID", ""),
                    "entropy": finding.get("Entropy", 0.0),
                    "commit": finding.get("Commit", ""),
                    "author": finding.get("Author", ""),
                    "email": finding.get("Email", ""),
                    "date": finding.get("Date", ""),
                    "message": finding.get("Message", ""),
                    "tags": finding.get("Tags", []),
                }
            )

        total_secrets = len(secrets)
        max_secrets = self.config.get("max_secrets", 0)

        # Calculate score - secrets are critical
        score = 100.0
        score -= total_secrets * 25  # -25 points per secret (critical)
        score = max(0.0, score)

        passed = total_secrets <= max_secrets

        details = {
            "total_secrets": total_secrets,
            "score": score,
            "secrets": secrets[:20],  # Limit to first 20
            "returncode": returncode,
        }

        return QualityResult(
            tool="gitleaks",
            passed=passed,
            score=score,
            details=details,
        )

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate GitLeaks analysis artifacts."""
        if not self.artifact_dir:
            return

        ensure_dir(self.artifact_dir)

        try:
            json_file = self.artifact_dir / "gitleaks.json"
            json_data = {
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
                "execution_time": result.execution_time,
            }
            atomic_write_text(json_file, json.dumps(json_data, indent=2))
            result.artifacts.append(json_file)

            summary_file = self.artifact_dir / "gitleaks_summary.txt"
            summary_report = self._generate_text_report(result)
            atomic_write_text(summary_file, summary_report)
            result.artifacts.append(summary_file)

        except Exception as e:
            result.details["artifact_error"] = str(e)

    def _generate_text_report(self, result: QualityResult) -> str:
        """Generate text summary report."""
        status_text = "✅ PASSED" if result.passed else "❌ FAILED"
        lines = [
            f"GitLeaks Secret Detection Report - {result.tool}",
            "=" * 50,
            f"Status: {status_text}",
            f"Security Score: {result.score}%",
            f"Secrets Found: {result.details.get('total_secrets', 0)}",
            "",
        ]

        secrets = result.details.get("secrets", [])
        if secrets:
            lines.append("⚠️  SECRETS DETECTED (redacted):")
            for secret in secrets[:10]:
                lines.extend(
                    [
                        f"  - {secret['file']}:{secret['start_line']}",
                        f"    Rule: {secret['rule_id']}",
                        f"    Description: {secret['description']}",
                        f"    Match: {secret['match']}",
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
