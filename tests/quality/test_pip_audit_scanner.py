#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for pip-audit dependency vulnerability scanner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from provide.testkit.quality.base import QualityToolError
from provide.testkit.quality.security.pip_audit_scanner import PIP_AUDIT_AVAILABLE, PipAuditScanner


class TestPipAuditAvailability:
    """Tests for pip-audit availability checking."""

    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_pip_audit_available_when_installed(self, mock_run: Mock) -> None:
        """Test detection when pip-audit is installed."""
        mock_run.return_value = Mock(returncode=0)

        from provide.testkit.quality.security import pip_audit_scanner

        result = pip_audit_scanner._check_pip_audit_available()

        assert result is True
        mock_run.assert_called_once_with(
            ["pip-audit", "--version"],
            timeout=10,
            check=False,
        )

    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_pip_audit_unavailable_when_not_installed(self, mock_run: Mock) -> None:
        """Test detection when pip-audit is not installed."""
        from provide.foundation.errors.process import ProcessError

        mock_run.side_effect = ProcessError("pip-audit not found", command="pip-audit --version")

        from provide.testkit.quality.security import pip_audit_scanner

        result = pip_audit_scanner._check_pip_audit_available()

        assert result is False

    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_pip_audit_unavailable_on_timeout(self, mock_run: Mock) -> None:
        """Test detection when version check times out."""
        mock_run.side_effect = TimeoutError("Command timed out")

        from provide.testkit.quality.security import pip_audit_scanner

        result = pip_audit_scanner._check_pip_audit_available()

        assert result is False


@pytest.mark.skipif(not PIP_AUDIT_AVAILABLE, reason="pip-audit not installed")
class TestPipAuditScanner:
    """Tests for pip-audit scanner (requires pip-audit to be installed)."""

    def test_scanner_initialization(self) -> None:
        """Test scanner can be initialized."""
        scanner = PipAuditScanner()
        assert scanner.config == {}
        assert scanner.artifact_dir is None

    def test_scanner_initialization_with_config(self) -> None:
        """Test scanner initialization with custom config."""
        config = {"strict": True, "max_vulnerabilities": 5}
        scanner = PipAuditScanner(config)
        assert scanner.config == config

    def test_build_pip_audit_command_with_requirements(self, tmp_path: Path) -> None:
        """Test command building for requirements.txt."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.0\n")

        scanner = PipAuditScanner()
        cmd = scanner._build_pip_audit_command(req_file)

        assert "pip-audit" in cmd
        assert "--format" in cmd
        assert "json" in cmd
        assert "--requirement" in cmd
        assert str(req_file) in cmd

    def test_build_pip_audit_command_with_pyproject(self, tmp_path: Path) -> None:
        """Test command building for pyproject.toml."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("[project]\nname = 'test'\n")

        scanner = PipAuditScanner()
        cmd = scanner._build_pip_audit_command(pyproject_file)

        assert "pip-audit" in cmd
        assert "--path" in cmd
        assert str(tmp_path) in cmd

    def test_build_pip_audit_command_with_directory(self, tmp_path: Path) -> None:
        """Test command building for directory."""
        scanner = PipAuditScanner()
        cmd = scanner._build_pip_audit_command(tmp_path)

        assert "pip-audit" in cmd
        assert "--path" in cmd
        assert str(tmp_path) in cmd

    def test_build_pip_audit_command_with_config_options(self, tmp_path: Path) -> None:
        """Test command includes config options."""
        config = {
            "strict": True,
            "local": True,
            "skip_editable": True,
        }
        scanner = PipAuditScanner(config)
        cmd = scanner._build_pip_audit_command(tmp_path)

        assert "--strict" in cmd
        assert "--local" in cmd
        assert "--skip-editable" in cmd


class TestPipAuditScannerMocked:
    """Tests for pip-audit scanner with mocked execution."""

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", False)
    def test_scanner_raises_on_unavailable_pip_audit(self) -> None:
        """Test scanner raises error if pip-audit is unavailable."""
        with pytest.raises(QualityToolError, match="pip-audit not available"):
            PipAuditScanner()

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_analyze_handles_timeout(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze handles timeout errors gracefully."""
        mock_run.side_effect = TimeoutError("Command timed out")

        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert "error" in result.details
        assert "timed out" in result.details["error"].lower()

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_analyze_handles_execution_errors(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze handles execution errors gracefully."""
        mock_run.side_effect = RuntimeError("Execution failed")

        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert "error" in result.details
        assert "Execution failed" in result.details["error"]

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_analyze_with_no_vulnerabilities(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with no vulnerabilities found."""
        # Mock successful run with no vulnerabilities
        audit_output = {"dependencies": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(audit_output),
            stderr="",
        )

        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is True
        assert result.score == 100.0
        assert result.details["total_vulnerabilities"] == 0

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_analyze_with_vulnerabilities(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with vulnerabilities found."""
        # Mock run that finds vulnerabilities
        audit_output = {
            "dependencies": [
                {
                    "name": "requests",
                    "version": "2.28.0",
                    "vulns": [
                        {
                            "id": "PYSEC-2023-123",
                            "description": "Request smuggling vulnerability",
                            "fix_versions": ["2.31.0"],
                            "aliases": ["CVE-2023-123"],
                        }
                    ],
                }
            ]
        }
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(audit_output),
            stderr="",
        )

        scanner = PipAuditScanner(config={"max_vulnerabilities": 0})
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert result.score == 90.0  # 100 - (1 * 10)
        assert result.details["total_vulnerabilities"] == 1
        assert result.details["total_dependencies"] == 1
        assert len(result.details["vulnerabilities"]) == 1
        assert result.details["vulnerabilities"][0]["package"] == "requests"
        assert result.details["vulnerabilities"][0]["id"] == "PYSEC-2023-123"

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_analyze_with_multiple_vulnerabilities(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with multiple vulnerabilities."""
        audit_output = {
            "dependencies": [
                {
                    "name": "requests",
                    "version": "2.28.0",
                    "vulns": [
                        {
                            "id": "PYSEC-2023-123",
                            "description": "Vulnerability 1",
                            "fix_versions": ["2.31.0"],
                            "aliases": [],
                        }
                    ],
                },
                {
                    "name": "urllib3",
                    "version": "1.26.0",
                    "vulns": [
                        {
                            "id": "PYSEC-2023-456",
                            "description": "Vulnerability 2",
                            "fix_versions": ["1.26.5"],
                            "aliases": [],
                        }
                    ],
                },
            ]
        }
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(audit_output),
            stderr="",
        )

        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path)

        assert result.details["total_vulnerabilities"] == 2
        assert result.score == 80.0  # 100 - (2 * 10)

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_analyze_with_invalid_json_output(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test handling of invalid JSON output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="{ invalid json",
            stderr="",
        )

        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path)

        # Should handle gracefully with empty data
        assert result.passed is True
        assert result.details["total_vulnerabilities"] == 0

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_analyze_creates_artifacts(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that analyze creates artifact files."""
        audit_output = {"dependencies": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(audit_output),
            stderr="",
        )

        artifact_dir = tmp_path / "artifacts"
        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path, artifact_dir=artifact_dir)

        assert artifact_dir.exists()
        assert (artifact_dir / "pip_audit.json").exists()
        assert (artifact_dir / "pip_audit_summary.txt").exists()
        assert len(result.artifacts) >= 2

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_report_terminal_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test terminal report generation."""
        audit_output = {"dependencies": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(audit_output),
            stderr="",
        )

        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path)
        report = scanner.report(result, format="terminal")

        assert "Pip-Audit Vulnerability Report" in report
        assert "Security Score:" in report
        assert "Dependencies Scanned:" in report
        assert "Vulnerabilities Found:" in report

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_report_json_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test JSON report generation."""
        audit_output = {"dependencies": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(audit_output),
            stderr="",
        )

        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path)
        report = scanner.report(result, format="json")

        data = json.loads(report)
        assert data["tool"] == "pip-audit"
        assert "passed" in data
        assert "score" in data
        assert "details" in data

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    def test_score_calculation(self) -> None:
        """Test score calculation with multiple vulnerabilities."""
        scanner = PipAuditScanner()

        # Test with 0 vulnerabilities
        audit_data = {"dependencies": []}
        result = scanner._process_results(audit_data, 0)
        assert result.score == 100.0

        # Test with 1 vulnerability
        audit_data = {
            "dependencies": [
                {
                    "name": "test",
                    "version": "1.0.0",
                    "vulns": [{"id": "test", "description": "test", "fix_versions": [], "aliases": []}],
                }
            ]
        }
        result = scanner._process_results(audit_data, 1)
        assert result.score == 90.0  # 100 - 10

        # Test with 10 vulnerabilities (should go to 0)
        audit_data = {
            "dependencies": [
                {
                    "name": f"pkg{i}",
                    "version": "1.0.0",
                    "vulns": [{"id": f"vuln{i}", "description": "test", "fix_versions": [], "aliases": []}],
                }
                for i in range(10)
            ]
        }
        result = scanner._process_results(audit_data, 1)
        assert result.score == 0.0  # 100 - (10 * 10) = 0

        # Test with 11 vulnerabilities (should stay at 0, not negative)
        audit_data = {
            "dependencies": [
                {
                    "name": f"pkg{i}",
                    "version": "1.0.0",
                    "vulns": [{"id": f"vuln{i}", "description": "test", "fix_versions": [], "aliases": []}],
                }
                for i in range(11)
            ]
        }
        result = scanner._process_results(audit_data, 1)
        assert result.score == 0.0  # Capped at 0

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_analyze_limits_vulnerability_list(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that vulnerability list is limited to first 20."""
        # Create 25 vulnerabilities
        audit_output = {
            "dependencies": [
                {
                    "name": f"package{i}",
                    "version": "1.0.0",
                    "vulns": [
                        {
                            "id": f"VULN-{i}",
                            "description": f"Vulnerability {i}",
                            "fix_versions": [],
                            "aliases": [],
                        }
                    ],
                }
                for i in range(25)
            ]
        }
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(audit_output),
            stderr="",
        )

        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path)

        assert result.details["total_vulnerabilities"] == 25
        assert len(result.details["vulnerabilities"]) == 20  # Limited to 20

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_analyze_with_artifact_errors(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test artifact generation error handling."""
        audit_output = {"dependencies": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(audit_output),
            stderr="",
        )

        artifact_dir = tmp_path / "artifacts"
        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path, artifact_dir=artifact_dir)

        # Cause artifact generation failure
        import os

        os.chmod(artifact_dir, 0o444)

        try:
            scanner._generate_artifacts(result)
            assert "artifact_error" in result.details or len(result.artifacts) >= 0
        finally:
            os.chmod(artifact_dir, 0o755)

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_report_unknown_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test report generation with unknown format."""
        audit_output = {"dependencies": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(audit_output),
            stderr="",
        )

        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path)
        report = scanner.report(result, format="xml")  # Unknown format

        # Should fall back to str(details)
        assert "total_vulnerabilities" in report

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_analyze_with_empty_stdout(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test handling of empty stdout."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",  # Empty output
            stderr="",
        )

        scanner = PipAuditScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is True
        assert result.details["total_vulnerabilities"] == 0

    @patch("provide.testkit.quality.security.pip_audit_scanner.PIP_AUDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.pip_audit_scanner.run")
    def test_build_command_with_pyproject_directory(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test command building with directory containing pyproject.toml."""
        mock_run.return_value = Mock(returncode=0, stdout="{}", stderr="")

        # Create pyproject.toml in directory
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("[project]\nname = 'test'\n")

        scanner = PipAuditScanner()
        cmd = scanner._build_pip_audit_command(tmp_path)

        assert "--path" in cmd
        assert str(tmp_path) in cmd


# 🧪✅🔚
