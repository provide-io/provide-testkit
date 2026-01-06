#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Pip-audit dependency vulnerability scanner implementation."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from provide.foundation.errors.process import ProcessError
from provide.foundation.file import atomic_write_text, ensure_dir
from provide.foundation.process import run
from provide.testkit.quality.base import QualityResult, QualityToolError


def _check_pip_audit_available() -> bool:
    """Check if pip-audit is available."""
    try:
        result = run(
            ["pip-audit", "--version"],
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (ProcessError, TimeoutError):
        return False


PIP_AUDIT_AVAILABLE = _check_pip_audit_available()


class PipAuditScanner:
    """Dependency vulnerability scanner using pip-audit.

    Scans Python dependencies for known security vulnerabilities
    using the PyPI security advisory database.

    Note: pip-audit does not support config files. All configuration must be
    passed via CLI flags or the config dict. See wrknv.toml for CLI usage.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize pip-audit scanner.

        Args:
            config: Scanner configuration options. Supported keys:
                    - strict: Enable strict mode
                    - local: Only scan locally installed packages
                    - skip_editable: Skip editable installations
                    - timeout: Command timeout in seconds
        """
        if not PIP_AUDIT_AVAILABLE:
            raise QualityToolError(
                "pip-audit not available. Install with: uv tool install pip-audit",
                tool="pip-audit",
            )

        self.config = config or {}
        self.artifact_dir: Path | None = None

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        """Run pip-audit analysis on the given path.

        Args:
            path: Path to analyze (directory with requirements or pyproject.toml)
            **kwargs: Additional options including artifact_dir

        Returns:
            QualityResult with vulnerability analysis data
        """
        self.artifact_dir = kwargs.get("artifact_dir", Path(".provide/output/security"))
        start_time = time.time()

        try:
            result = self._run_pip_audit(path)
            result.execution_time = time.time() - start_time
            self._generate_artifacts(result)
            return result

        except Exception as e:
            return QualityResult(
                tool="pip-audit",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def _build_pip_audit_command(self, path: Path) -> list[str]:
        """Build pip-audit command with options."""
        cmd = ["pip-audit", "--format", "json", "--progress-spinner", "off"]

        # Add path-specific options
        if path.is_file():
            if path.name == "requirements.txt":
                cmd.extend(["--requirement", str(path)])
            elif path.name == "pyproject.toml":
                cmd.extend(["--path", str(path.parent)])
        elif path.is_dir():
            cmd.extend(["--path", str(path)])

        # Add configuration options
        if self.config.get("strict", False):
            cmd.append("--strict")

        if self.config.get("local", False):
            cmd.append("--local")

        if self.config.get("skip_editable", False):
            cmd.append("--skip-editable")

        return cmd

    def _run_pip_audit(self, path: Path) -> QualityResult:
        """Run pip-audit scan."""
        try:
            cmd = self._build_pip_audit_command(path)

            result = run(
                cmd,
                timeout=self.config.get("timeout", 300),
                cwd=path if path.is_dir() else path.parent,
                check=False,
            )

            # Parse JSON output
            try:
                audit_data = json.loads(result.stdout) if result.stdout else {}
            except json.JSONDecodeError:
                audit_data = {}

            return self._process_results(audit_data, result.returncode)

        except TimeoutError as e:
            raise QualityToolError(f"pip-audit timed out: {e!s}", tool="pip-audit") from e
        except Exception as e:
            raise QualityToolError(f"pip-audit scan failed: {e!s}", tool="pip-audit") from e

    def _process_results(self, audit_data: dict[str, Any], returncode: int) -> QualityResult:
        """Process pip-audit results into QualityResult."""
        dependencies = audit_data.get("dependencies", [])
        vulnerabilities: list[dict[str, Any]] = []

        # Extract vulnerabilities
        for dep in dependencies:
            for vuln in dep.get("vulns", []):
                vulnerabilities.append(
                    {
                        "package": dep.get("name", "unknown"),
                        "version": dep.get("version", "unknown"),
                        "id": vuln.get("id", ""),
                        "description": vuln.get("description", ""),
                        "fix_versions": vuln.get("fix_versions", []),
                        "aliases": vuln.get("aliases", []),
                    }
                )

        total_vulnerabilities = len(vulnerabilities)
        max_vulns = self.config.get("max_vulnerabilities", 0)

        # Calculate score
        score = 100.0
        score -= total_vulnerabilities * 10  # -10 points per vulnerability
        score = max(0.0, score)

        passed = total_vulnerabilities <= max_vulns and returncode == 0

        details = {
            "total_dependencies": len(dependencies),
            "total_vulnerabilities": total_vulnerabilities,
            "score": score,
            "vulnerabilities": vulnerabilities[:20],  # Limit to first 20
            "returncode": returncode,
        }

        return QualityResult(
            tool="pip-audit",
            passed=passed,
            score=score,
            details=details,
        )

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate pip-audit analysis artifacts."""
        if not self.artifact_dir:
            return

        ensure_dir(self.artifact_dir)

        try:
            # Generate JSON report
            json_file = self.artifact_dir / "pip_audit.json"
            json_data = {
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
                "execution_time": result.execution_time,
            }
            atomic_write_text(json_file, json.dumps(json_data, indent=2))
            result.artifacts.append(json_file)

            # Generate text summary
            summary_file = self.artifact_dir / "pip_audit_summary.txt"
            summary_report = self._generate_text_report(result)
            atomic_write_text(summary_file, summary_report)
            result.artifacts.append(summary_file)

        except Exception as e:
            result.details["artifact_error"] = str(e)

    def _generate_text_report(self, result: QualityResult) -> str:
        """Generate text summary report."""
        status_text = "✅ PASSED" if result.passed else "❌ FAILED"
        lines = [
            f"Pip-Audit Vulnerability Report - {result.tool}",
            "=" * 50,
            f"Status: {status_text}",
            f"Security Score: {result.score}%",
            f"Dependencies Scanned: {result.details.get('total_dependencies', 0)}",
            f"Vulnerabilities Found: {result.details.get('total_vulnerabilities', 0)}",
            "",
        ]

        vulns = result.details.get("vulnerabilities", [])
        if vulns:
            lines.append("Vulnerabilities:")
            for vuln in vulns[:10]:
                lines.extend(
                    [
                        f"  - {vuln['package']} {vuln['version']}",
                        f"    ID: {vuln['id']}",
                        f"    Fix: {', '.join(vuln['fix_versions']) if vuln['fix_versions'] else 'No fix available'}",
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
