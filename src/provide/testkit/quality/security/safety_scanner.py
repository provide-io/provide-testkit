#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Safety dependency vulnerability scanner implementation."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from provide.foundation.errors.process import ProcessError
from provide.foundation.file import atomic_write_text, ensure_dir
from provide.foundation.process import run
from provide.testkit.quality.base import QualityResult, QualityToolError


def _check_safety_available() -> bool:
    """Check if safety is available."""
    try:
        result = run(
            ["safety", "--version"],
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (ProcessError, TimeoutError):
        return False


SAFETY_AVAILABLE = _check_safety_available()


class SafetyScanner:
    """Dependency vulnerability scanner using Safety.

    Scans Python dependencies against the PyUp Safety database
    for known security vulnerabilities.
    """

    # Default config file location
    DEFAULT_CONFIG_PATH = Path(".provide/security/safety-policy.yml")

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize safety scanner.

        Args:
            config: Scanner configuration options. If "policy_file" is not specified,
                    will auto-detect .provide/security/safety-policy.yml if it exists.
        """
        if not SAFETY_AVAILABLE:
            raise QualityToolError(
                "Safety not available. Install with: uv tool install safety",
                tool="safety",
            )

        self.config = config or {}
        self.artifact_dir: Path | None = None

        # Auto-detect policy file if not explicitly specified
        if "policy_file" not in self.config:
            default_config = self._get_default_config_path()
            if default_config:
                self.config["policy_file"] = default_config

    def _get_default_config_path(self) -> Path | None:
        """Get default config file path if it exists."""
        if self.DEFAULT_CONFIG_PATH.exists():
            return self.DEFAULT_CONFIG_PATH
        return None

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        """Run safety analysis on the given path.

        Args:
            path: Path to analyze (directory with requirements or pyproject.toml)
            **kwargs: Additional options including artifact_dir

        Returns:
            QualityResult with vulnerability analysis data
        """
        self.artifact_dir = kwargs.get("artifact_dir", Path(".provide/output/security"))
        start_time = time.time()

        try:
            result = self._run_safety_scan(path)
            result.execution_time = time.time() - start_time
            self._generate_artifacts(result)
            return result

        except Exception as e:
            return QualityResult(
                tool="safety",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def _build_safety_command(self, path: Path) -> list[str]:
        """Build Safety command with options."""
        cmd = ["safety", "check", "--output", "json"]

        # Add policy file if configured
        if self.config.get("policy_file"):
            policy_path = Path(self.config["policy_file"])
            if policy_path.exists():
                cmd.extend(["--policy-file", str(policy_path)])

        # Add path-specific options
        if path.is_file() and path.name == "requirements.txt":
            cmd.extend(["--file", str(path)])
        elif path.is_dir():
            req_file = path / "requirements.txt"
            if req_file.exists():
                cmd.extend(["--file", str(req_file)])

        # Add configuration options
        if self.config.get("full_report", False):
            cmd.append("--full-report")

        if self.config.get("ignore_vulns"):
            for vuln_id in self.config["ignore_vulns"]:
                cmd.extend(["--ignore", str(vuln_id)])

        return cmd

    def _run_safety_scan(self, path: Path) -> QualityResult:
        """Run safety scan."""
        try:
            cmd = self._build_safety_command(path)

            result = run(
                cmd,
                timeout=self.config.get("timeout", 120),
                cwd=path if path.is_dir() else path.parent,
                check=False,
            )

            # Parse JSON output
            try:
                safety_data = json.loads(result.stdout) if result.stdout else {}
            except json.JSONDecodeError:
                # Safety may output non-JSON for some errors
                safety_data = {"error": result.stderr or result.stdout}

            return self._process_results(safety_data, result.returncode)

        except TimeoutError as e:
            raise QualityToolError(f"Safety scan timed out: {e!s}", tool="safety") from e
        except Exception as e:
            raise QualityToolError(f"Safety scan failed: {e!s}", tool="safety") from e

    def _process_results(self, safety_data: dict[str, Any], returncode: int) -> QualityResult:
        """Process safety results into QualityResult."""
        vulnerabilities: list[dict[str, Any]] = []

        # Safety 3.x uses different output format
        if "vulnerabilities" in safety_data:
            for vuln in safety_data["vulnerabilities"]:
                vulnerabilities.append(
                    {
                        "package": vuln.get("package_name", "unknown"),
                        "installed_version": vuln.get("analyzed_version", "unknown"),
                        "vulnerable_versions": vuln.get("vulnerable_versions", ""),
                        "id": vuln.get("vulnerability_id", ""),
                        "cve": vuln.get("CVE", ""),
                        "advisory": vuln.get("advisory", ""),
                        "severity": vuln.get("severity", "unknown"),
                    }
                )
        elif "scan_results" in safety_data:
            # Newer Safety format
            results = safety_data.get("scan_results", {}).get("results", [])
            for result_item in results:
                vulnerabilities.append(
                    {
                        "package": result_item.get("package", "unknown"),
                        "installed_version": result_item.get("version", "unknown"),
                        "vulnerable_versions": result_item.get("specs", ""),
                        "id": str(result_item.get("id", "")),
                        "cve": result_item.get("cve", ""),
                        "advisory": result_item.get("advisory", ""),
                        "severity": "unknown",
                    }
                )

        total_vulnerabilities = len(vulnerabilities)
        max_vulns = self.config.get("max_vulnerabilities", 0)

        # Calculate score
        score = 100.0
        score -= total_vulnerabilities * 10
        score = max(0.0, score)

        passed = total_vulnerabilities <= max_vulns

        details = {
            "total_vulnerabilities": total_vulnerabilities,
            "score": score,
            "vulnerabilities": vulnerabilities[:20],
            "returncode": returncode,
        }

        return QualityResult(
            tool="safety",
            passed=passed,
            score=score,
            details=details,
        )

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate safety analysis artifacts."""
        if not self.artifact_dir:
            return

        ensure_dir(self.artifact_dir)

        try:
            json_file = self.artifact_dir / "safety.json"
            json_data = {
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
                "execution_time": result.execution_time,
            }
            atomic_write_text(json_file, json.dumps(json_data, indent=2))
            result.artifacts.append(json_file)

            summary_file = self.artifact_dir / "safety_summary.txt"
            summary_report = self._generate_text_report(result)
            atomic_write_text(summary_file, summary_report)
            result.artifacts.append(summary_file)

        except Exception as e:
            result.details["artifact_error"] = str(e)

    def _generate_text_report(self, result: QualityResult) -> str:
        """Generate text summary report."""
        status_text = "✅ PASSED" if result.passed else "❌ FAILED"
        lines = [
            f"Safety Vulnerability Report - {result.tool}",
            "=" * 50,
            f"Status: {status_text}",
            f"Security Score: {result.score}%",
            f"Vulnerabilities Found: {result.details.get('total_vulnerabilities', 0)}",
            "",
        ]

        vulns = result.details.get("vulnerabilities", [])
        if vulns:
            lines.append("Vulnerabilities:")
            for vuln in vulns[:10]:
                lines.extend(
                    [
                        f"  - {vuln['package']} {vuln['installed_version']}",
                        f"    ID: {vuln['id']} | CVE: {vuln.get('cve', 'N/A')}",
                        f"    Vulnerable: {vuln['vulnerable_versions']}",
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
