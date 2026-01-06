#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Security vulnerability scanner implementation.

This module provides a high-level security scanning interface using bandit.
The scanner can be configured with various verbosity levels to control output
noise and is designed for integration with CI/CD pipelines.

Usage:
    Basic usage with default settings:
        >>> scanner = SecurityScanner()
        >>> result = scanner.analyze(Path("./src"))

    With custom verbosity (quiet mode for CI):
        >>> scanner = SecurityScanner(config={'verbosity': 'quiet'})
        >>> result = scanner.analyze(Path("./src"))

    With custom thresholds:
        >>> config = {
        ...     'max_high_severity': 0,
        ...     'max_medium_severity': 5,
        ...     'min_score': 80.0,
        ...     'verbosity': 'normal'
        ... }
        >>> scanner = SecurityScanner(config)
        >>> result = scanner.analyze(Path("./src"))

Verbosity Levels:
    - 'quiet': Only show errors (best for CI/CD)
    - 'normal': Show errors and warnings (default)
    - 'verbose': Show all messages including debug info

Configuration Options:
    - max_high_severity: Maximum allowed high severity issues (default: 0)
    - max_medium_severity: Maximum allowed medium severity issues (default: 5)
    - min_score: Minimum security score to pass (default: 80.0)
    - verbosity: Output verbosity level (default: 'normal')
    - exclude: File patterns to exclude from scanning

Score Calculation:
    The security score starts at 100 and deducts points based on issue severity:
    - High severity: -10 points per issue
    - Medium severity: -5 points per issue
    - Low severity: -1 point per issue

    The score is capped at 0 (cannot go negative).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import time
from typing import Any, Literal

from provide.foundation.file import atomic_write_text, ensure_dir
from provide.testkit.quality.base import QualityResult, QualityToolError

try:
    import bandit  # type: ignore[import-untyped]
    from bandit.core import (  # type: ignore[import-untyped]
        config as bandit_config,
        manager as bandit_manager,
    )

    BANDIT_AVAILABLE = True
except ImportError:
    BANDIT_AVAILABLE = False
    bandit = None
    bandit_config = None
    bandit_manager = None

# Define verbosity levels
VerbosityLevel = Literal["quiet", "normal", "verbose"]


class SecurityScanner:
    """Security vulnerability scanner using bandit and other tools.

    Provides high-level interface for security analysis with automatic
    artifact management and integration with the quality framework.

    Configuration:
        max_high_severity: Maximum allowed high severity issues (default: 0)
        max_medium_severity: Maximum allowed medium severity issues (default: 5)
        min_score: Minimum security score to pass (default: 80.0)
        verbosity: Output verbosity ('quiet', 'normal', 'verbose')
        exclude: List of file patterns to exclude from scanning
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize security scanner.

        Args:
            config: Security scanner configuration options

        Raises:
            QualityToolError: If bandit is not available
        """
        if not BANDIT_AVAILABLE:
            raise QualityToolError("Bandit not available. Install with: uv tool install bandit", tool="security")

        self.config = config or {}
        self.artifact_dir: Path | None = None
        self.verbosity: VerbosityLevel = self.config.get("verbosity", "normal")

        # Configure logging based on verbosity
        self._configure_logging()

    def _configure_logging(self) -> None:
        """Configure bandit and scanner logging based on verbosity level.

        Verbosity levels:
            - quiet: Only errors (ERROR level)
            - normal: Errors and warnings (WARNING level)
            - verbose: All messages (INFO level)
        """
        # Map verbosity to logging levels
        level_map: dict[str, int] = {
            "quiet": logging.ERROR,
            "normal": logging.WARNING,
            "verbose": logging.INFO,
        }

        log_level = level_map.get(self.verbosity, logging.WARNING)

        # Configure bandit's logger to reduce noise
        bandit_logger = logging.getLogger("bandit")
        bandit_logger.setLevel(log_level)

        # Suppress specific noisy loggers from bandit
        if self.verbosity in ("quiet", "normal"):
            # These loggers generate the "nosec encountered" and "Test in comment" messages
            for logger_name in [
                "bandit.core.manager",
                "bandit.core.test_set",
                "bandit.core.issue",
            ]:
                logger = logging.getLogger(logger_name)
                logger.setLevel(logging.ERROR)

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        """Run security analysis on the given path.

        Args:
            path: Path to analyze
            **kwargs: Additional options:
                - artifact_dir: Directory for output artifacts
                - verbosity: Override scanner's verbosity level

        Returns:
            QualityResult with security analysis data
        """
        self.artifact_dir = kwargs.get("artifact_dir", Path(".provide/output/security"))

        # Allow verbosity override for this specific analysis
        old_verbosity = None
        if "verbosity" in kwargs:
            old_verbosity = self.verbosity
            self.verbosity = kwargs["verbosity"]
            self._configure_logging()

        start_time = time.time()

        try:
            # Run bandit security scan
            result = self._run_bandit_scan(path)
            result.execution_time = time.time() - start_time

            # Generate artifacts
            self._generate_artifacts(result)

            return result

        except Exception as e:
            return QualityResult(
                tool="security",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )
        finally:
            # Restore original verbosity if it was overridden
            if old_verbosity is not None:
                self.verbosity = old_verbosity
                self._configure_logging()

    def _run_bandit_scan(self, path: Path) -> QualityResult:
        """Run bandit security scan."""
        if not BANDIT_AVAILABLE:
            raise QualityToolError("Bandit not available", tool="security")

        try:
            # Create bandit configuration
            conf = bandit_config.BanditConfig()

            # Apply custom configuration
            self._apply_bandit_config(conf)

            # Create bandit manager
            b_mgr = bandit_manager.BanditManager(conf, "file")

            # Discover files to scan
            files_list = [str(path)] if path.is_file() else self._discover_python_files(path)

            if not files_list:
                return QualityResult(
                    tool="security",
                    passed=True,
                    score=100.0,
                    details={"message": "No Python files found to scan"},
                )

            # Run the scan
            b_mgr.discover_files(files_list)
            b_mgr.run_tests()

            # Process results
            return self._process_bandit_results(b_mgr)

        except Exception as e:
            raise QualityToolError(f"Bandit scan failed: {e!s}", tool="security") from e

    def _apply_bandit_config(self, conf: Any) -> None:
        """Apply custom configuration to bandit.

        Extension point for future bandit configuration customization.
        Currently uses bandit defaults with post-processing filtering.

        Args:
            conf: Bandit configuration object (currently unused)
        """
        # Extension point: Future versions may customize bandit config here
        # Current implementation relies on defaults + post-scan filtering

    def _discover_python_files(self, path: Path) -> list[str]:
        """Discover Python files to scan."""
        excludes = self.config.get(
            "exclude", ["*/tests/*", "*/test_*", "*/.venv/*", "*/venv/*", "*/__pycache__/*"]
        )

        files = []
        for py_file in path.rglob("*.py"):
            # Check if file should be excluded
            if any(py_file.match(pattern) for pattern in excludes):
                continue
            files.append(str(py_file))

        return files

    def _process_bandit_results(self, manager: Any) -> QualityResult:
        """Process bandit scan results into QualityResult."""
        # Get issues
        issues = manager.get_issue_list()

        # Calculate metrics
        total_files = len(manager.files_list)
        issue_count = len(issues)

        # Categorize by severity
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for issue in issues:
            severity_counts[issue.severity] += 1
            confidence_counts[issue.confidence] += 1

        # Calculate security score (0-100)
        # Start at 100, deduct points based on severity
        score = 100.0
        score -= severity_counts["HIGH"] * 10  # High severity: -10 points each
        score -= severity_counts["MEDIUM"] * 5  # Medium severity: -5 points each
        score -= severity_counts["LOW"] * 1  # Low severity: -1 point each
        score = max(0.0, score)  # Don't go below 0

        # Determine if passed based on configuration
        max_high = self.config.get("max_high_severity", 0)
        max_medium = self.config.get("max_medium_severity", 5)
        min_score = self.config.get("min_score", 80.0)

        passed = (
            severity_counts["HIGH"] <= max_high
            and severity_counts["MEDIUM"] <= max_medium
            and score >= min_score
        )

        # Create detailed results
        details = {
            "total_files": total_files,
            "total_issues": issue_count,
            "severity_breakdown": severity_counts,
            "confidence_breakdown": confidence_counts,
            "score": score,
            "thresholds": {
                "max_high_severity": max_high,
                "max_medium_severity": max_medium,
                "min_score": min_score,
            },
        }

        # Add issue details for reporting
        # Normalize all paths to absolute to avoid path handling issues
        if issues:
            details["issues"] = [
                {
                    "filename": str(Path(issue.fname).resolve()),
                    "line_number": issue.lineno,
                    "test_id": issue.test_id,
                    "test_name": issue.test,
                    "severity": issue.severity,
                    "confidence": issue.confidence,
                    "text": issue.text.strip(),
                    "code": issue.get_code(max_lines=3, tabbed=False),
                }
                for issue in issues[:20]  # Limit to first 20 for readability
            ]

        return QualityResult(tool="security", passed=passed, score=score, details=details)

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate security analysis artifacts.

        Args:
            result: Result to add artifacts to
        """
        if not self.artifact_dir:
            return

        ensure_dir(self.artifact_dir)

        try:
            # Generate JSON report
            json_file = self.artifact_dir / "security.json"
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
            summary_file = self.artifact_dir / "security_summary.txt"
            summary_report = self._generate_text_report(result)
            atomic_write_text(summary_file, summary_report)
            result.artifacts.append(summary_file)

            # Generate detailed issues report if there are issues
            if result.details.get("issues"):
                issues_file = self.artifact_dir / "security_issues.txt"
                issues_report = self._generate_issues_report(result)
                atomic_write_text(issues_file, issues_report)
                result.artifacts.append(issues_file)

        except Exception as e:
            # Add error to result details but don't fail
            result.details["artifact_error"] = str(e)

    def _generate_text_report(self, result: QualityResult) -> str:
        """Generate text summary report."""
        status_text = "✅ PASSED" if result.passed else "❌ FAILED"
        lines = [
            f"Security Analysis Report - {result.tool}",
            "=" * 50,
            f"Status: {status_text}",
            f"Security Score: {result.score}%",
        ]

        details = result.details
        if "total_files" in details:
            lines.extend(
                [
                    f"Files Scanned: {details['total_files']}",
                    f"Total Issues: {details['total_issues']}",
                    "",
                    "Severity Breakdown:",
                ]
            )

            severity = details.get("severity_breakdown", {})
            for level, count in severity.items():
                lines.append(f"  {level}: {count}")

            lines.extend(
                [
                    "",
                    "Confidence Breakdown:",
                ]
            )

            confidence = details.get("confidence_breakdown", {})
            for level, count in confidence.items():
                lines.append(f"  {level}: {count}")

        if result.execution_time:
            lines.append(f"\nExecution Time: {result.execution_time:.2f}s")

        return "\n".join(lines)

    def _format_path_for_display(self, filepath: str) -> str:
        """Format a file path for display, converting to relative if possible.

        Args:
            filepath: Absolute file path

        Returns:
            Relative path if possible, otherwise absolute path
        """
        try:
            abs_path = Path(filepath).resolve()
            cwd = Path.cwd()
            # Try to get relative path
            return str(abs_path.relative_to(cwd))
        except (ValueError, OSError):
            # If relative_to fails, return the absolute path
            return filepath

    def _generate_issues_report(self, result: QualityResult) -> str:
        """Generate detailed issues report."""
        lines = ["Security Issues Report", "=" * 50, ""]

        issues = result.details.get("issues", [])
        for i, issue in enumerate(issues, 1):
            # Format path for display (convert to relative if possible)
            display_path = self._format_path_for_display(issue["filename"])

            lines.extend(
                [
                    f"Issue #{i}:",
                    f"  File: {display_path}:{issue['line_number']}",
                    f"  Test: {issue['test_name']} ({issue['test_id']})",
                    f"  Severity: {issue['severity']} | Confidence: {issue['confidence']}",
                    f"  Description: {issue['text']}",
                    "",
                    "  Code:",
                ]
            )

            # Add code snippet with indentation
            for code_line in issue["code"].split("\n"):
                if code_line.strip():
                    lines.append(f"    {code_line}")

            lines.append("")

        return "\n".join(lines)

    def report(self, result: QualityResult, format: str = "terminal") -> str:
        """Generate report from QualityResult (implements QualityTool protocol).

        Args:
            result: Security result
            format: Report format

        Returns:
            Formatted report
        """
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
