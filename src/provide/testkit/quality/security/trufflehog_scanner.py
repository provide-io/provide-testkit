#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TruffleHog deep secret detection scanner implementation."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from provide.foundation.errors.process import ProcessError
from provide.foundation.file import atomic_write_text, ensure_dir
from provide.foundation.process import run
from provide.testkit.quality.base import QualityResult, QualityToolError


def _check_trufflehog_available() -> bool:
    """Check if trufflehog is available."""
    try:
        result = run(
            ["trufflehog", "--version"],
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (ProcessError, TimeoutError):
        return False


TRUFFLEHOG_AVAILABLE = _check_trufflehog_available()


class TruffleHogScanner:
    """Deep secret detection scanner using TruffleHog.

    Scans codebases for secrets using entropy analysis and pattern matching.
    Can optionally verify if discovered credentials are still active.

    Note: TruffleHog is a Go binary and must be installed separately.
    Install via: brew install trufflehog (macOS) or download from GitHub releases.
    """

    # Default config file location
    DEFAULT_CONFIG_PATH = Path(".provide/security/trufflehog.yml")

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize TruffleHog scanner.

        Args:
            config: Scanner configuration options. If "config_file" is not specified,
                    will auto-detect .provide/security/trufflehog.yml if it exists.
        """
        if not TRUFFLEHOG_AVAILABLE:
            raise QualityToolError(
                "TruffleHog not available. Install with: brew install trufflehog (macOS) "
                "or download from https://github.com/trufflesecurity/trufflehog/releases",
                tool="trufflehog",
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
        """Run TruffleHog analysis on the given path.

        Args:
            path: Path to scan for secrets
            **kwargs: Additional options including artifact_dir

        Returns:
            QualityResult with secret detection data
        """
        self.artifact_dir = kwargs.get("artifact_dir", Path(".provide/output/security"))
        start_time = time.time()

        try:
            result = self._run_trufflehog_scan(path)
            result.execution_time = time.time() - start_time
            self._generate_artifacts(result)
            return result

        except Exception as e:
            return QualityResult(
                tool="trufflehog",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def _build_trufflehog_command(self, path: Path) -> list[str]:
        """Build TruffleHog command with options."""
        cmd = [
            "trufflehog",
            "filesystem",
            str(path),
            "--json",
        ]

        # Add configuration options
        if self.config.get("only_verified", False):
            cmd.append("--only-verified")

        if self.config.get("no_verification", False):
            cmd.append("--no-verification")

        if self.config.get("concurrency"):
            cmd.extend(["--concurrency", str(self.config["concurrency"])])

        if self.config.get("include_detectors"):
            cmd.extend(["--include-detectors", ",".join(self.config["include_detectors"])])

        if self.config.get("exclude_detectors"):
            cmd.extend(["--exclude-detectors", ",".join(self.config["exclude_detectors"])])

        if self.config.get("exclude_paths"):
            for exclude_path in self.config["exclude_paths"]:
                cmd.extend(["--exclude-paths", str(exclude_path)])

        return cmd

    def _run_trufflehog_scan(self, path: Path) -> QualityResult:
        """Run TruffleHog scan."""
        try:
            cmd = self._build_trufflehog_command(path)

            result = run(
                cmd,
                timeout=self.config.get("timeout", 600),  # TruffleHog can be slow
                check=False,
            )

            # TruffleHog outputs JSON lines (one per finding)
            findings: list[dict[str, Any]] = []
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        try:
                            findings.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

            return self._process_results(findings, result.returncode)

        except TimeoutError as e:
            raise QualityToolError(f"TruffleHog scan timed out: {e!s}", tool="trufflehog") from e
        except Exception as e:
            raise QualityToolError(f"TruffleHog scan failed: {e!s}", tool="trufflehog") from e

    def _process_results(self, findings: list[dict[str, Any]], returncode: int) -> QualityResult:
        """Process TruffleHog results into QualityResult."""
        secrets: list[dict[str, Any]] = []

        for finding in findings:
            source_metadata = finding.get("SourceMetadata", {})
            data = source_metadata.get("Data", {})
            filesystem_data = data.get("Filesystem", {})

            secrets.append(
                {
                    "detector_type": finding.get("DetectorType", ""),
                    "detector_name": finding.get("DetectorName", ""),
                    "verified": finding.get("Verified", False),
                    "file": filesystem_data.get("file", ""),
                    "line": filesystem_data.get("line", 0),
                    "raw": "***REDACTED***",  # Never expose actual secrets
                    "redacted": finding.get("Redacted", ""),
                    "extra_data": finding.get("ExtraData", {}),
                }
            )

        total_secrets = len(secrets)
        verified_secrets = sum(1 for s in secrets if s.get("verified", False))
        max_secrets = self.config.get("max_secrets", 0)

        # Calculate score - verified secrets are more critical
        score = 100.0
        score -= verified_secrets * 50  # -50 points per verified secret
        score -= (total_secrets - verified_secrets) * 15  # -15 points per unverified
        score = max(0.0, score)

        passed = total_secrets <= max_secrets

        details = {
            "total_secrets": total_secrets,
            "verified_secrets": verified_secrets,
            "unverified_secrets": total_secrets - verified_secrets,
            "score": score,
            "secrets": secrets[:20],
            "returncode": returncode,
        }

        return QualityResult(
            tool="trufflehog",
            passed=passed,
            score=score,
            details=details,
        )

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate TruffleHog analysis artifacts."""
        if not self.artifact_dir:
            return

        ensure_dir(self.artifact_dir)

        try:
            json_file = self.artifact_dir / "trufflehog.json"
            json_data = {
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
                "execution_time": result.execution_time,
            }
            atomic_write_text(json_file, json.dumps(json_data, indent=2))
            result.artifacts.append(json_file)

            summary_file = self.artifact_dir / "trufflehog_summary.txt"
            summary_report = self._generate_text_report(result)
            atomic_write_text(summary_file, summary_report)
            result.artifacts.append(summary_file)

        except Exception as e:
            result.details["artifact_error"] = str(e)

    def _generate_text_report(self, result: QualityResult) -> str:
        """Generate text summary report."""
        status_text = "✅ PASSED" if result.passed else "❌ FAILED"
        lines = [
            f"TruffleHog Deep Secret Detection Report - {result.tool}",
            "=" * 50,
            f"Status: {status_text}",
            f"Security Score: {result.score}%",
            f"Total Secrets Found: {result.details.get('total_secrets', 0)}",
            f"  Verified (Active): {result.details.get('verified_secrets', 0)}",
            f"  Unverified: {result.details.get('unverified_secrets', 0)}",
            "",
        ]

        secrets = result.details.get("secrets", [])
        if secrets:
            lines.append("⚠️  SECRETS DETECTED (redacted):")
            for secret in secrets[:10]:
                verified_marker = "🔴 VERIFIED" if secret.get("verified") else "⚪ unverified"
                lines.extend(
                    [
                        f"  - {secret['file']}:{secret['line']}",
                        f"    Detector: {secret['detector_name']} ({secret['detector_type']})",
                        f"    Status: {verified_marker}",
                        f"    Redacted: {secret['redacted'][:50]}..."
                        if len(secret.get("redacted", "")) > 50
                        else f"    Redacted: {secret.get('redacted', '')}",
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
