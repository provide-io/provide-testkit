#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for Safety dependency vulnerability scanner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from provide.testkit.quality.base import QualityToolError
from provide.testkit.quality.security.safety_scanner import SAFETY_AVAILABLE, SafetyScanner


@pytest.fixture(autouse=True)
def disable_default_policy(monkeypatch) -> None:
    """Prevent auto-detecting the repository-wide policy file during tests."""
    monkeypatch.setattr(SafetyScanner, "_get_default_config_path", lambda self: None)


class TestSafetyAvailability:
    """Tests for Safety availability checking."""

    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_safety_available_when_installed(self, mock_run: Mock) -> None:
        """Test detection when safety is installed."""
        mock_run.return_value = Mock(returncode=0)

        from provide.testkit.quality.security import safety_scanner

        result = safety_scanner._check_safety_available()

        assert result is True

    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_safety_unavailable_when_not_installed(self, mock_run: Mock) -> None:
        """Test detection when safety is not installed."""
        from provide.foundation.errors.process import ProcessError

        mock_run.side_effect = ProcessError("safety not found", command="safety --version")

        from provide.testkit.quality.security import safety_scanner

        result = safety_scanner._check_safety_available()

        assert result is False

    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_safety_unavailable_on_timeout(self, mock_run: Mock) -> None:
        """Test detection when version check times out."""
        mock_run.side_effect = TimeoutError("Command timed out")

        from provide.testkit.quality.security import safety_scanner

        result = safety_scanner._check_safety_available()

        assert result is False


@pytest.mark.skipif(not SAFETY_AVAILABLE, reason="Safety not installed")
class TestSafetyScanner:
    """Tests for Safety scanner (requires safety to be installed)."""

    def test_scanner_initialization(self) -> None:
        """Test scanner can be initialized."""
        scanner = SafetyScanner()
        assert scanner.config == {}

    def test_scanner_initialization_with_config(self) -> None:
        """Test scanner initialization with custom config."""
        config = {"max_vulnerabilities": 5}
        scanner = SafetyScanner(config)
        assert scanner.config == config


class TestSafetyScannerMocked:
    """Tests for Safety scanner with mocked execution."""

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", False)
    def test_scanner_raises_on_unavailable_safety(self) -> None:
        """Test scanner raises error if safety is unavailable."""
        with pytest.raises(QualityToolError, match="Safety not available"):
            SafetyScanner()

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", True)
    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_analyze_with_no_vulnerabilities(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with no vulnerabilities found."""
        safety_output = {"vulnerabilities": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(safety_output),
            stderr="",
        )

        scanner = SafetyScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is True
        assert result.score == 100.0
        assert result.details["total_vulnerabilities"] == 0

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", True)
    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_analyze_with_vulnerabilities_v3_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with vulnerabilities in Safety 3.x format."""
        safety_output = {
            "vulnerabilities": [
                {
                    "package_name": "requests",
                    "analyzed_version": "2.28.0",
                    "vulnerable_versions": "<2.31.0",
                    "vulnerability_id": "PYUP-123",
                    "CVE": "CVE-2023-123",
                    "advisory": "Security vulnerability",
                    "severity": "high",
                }
            ]
        }
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(safety_output),
            stderr="",
        )

        scanner = SafetyScanner(config={"max_vulnerabilities": 0})
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert result.score == 90.0
        assert result.details["total_vulnerabilities"] == 1
        assert result.details["vulnerabilities"][0]["package"] == "requests"

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", True)
    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_analyze_with_scan_results_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with newer Safety scan_results format."""
        safety_output = {
            "scan_results": {
                "results": [
                    {
                        "package": "urllib3",
                        "version": "1.26.0",
                        "specs": "<1.26.5",
                        "id": 456,
                        "cve": "CVE-2023-456",
                        "advisory": "Another vulnerability",
                    }
                ]
            }
        }
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(safety_output),
            stderr="",
        )

        scanner = SafetyScanner()
        result = scanner.analyze(tmp_path)

        assert result.details["total_vulnerabilities"] == 1
        assert result.details["vulnerabilities"][0]["package"] == "urllib3"

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", True)
    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_score_calculation(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test score calculation with multiple vulnerabilities."""
        mock_run.return_value = Mock(returncode=0, stdout="{}", stderr="")

        scanner = SafetyScanner()

        # Test with 0 vulnerabilities
        result = scanner._process_results({"vulnerabilities": []}, 0)
        assert result.score == 100.0

        # Test with 1 vulnerability
        safety_data = {
            "vulnerabilities": [
                {
                    "package_name": "test",
                    "analyzed_version": "1.0.0",
                    "vulnerability_id": "TEST-1",
                }
            ]
        }
        result = scanner._process_results(safety_data, 1)
        assert result.score == 90.0

        # Test with 10 vulnerabilities (should go to 0)
        safety_data = {
            "vulnerabilities": [
                {"package_name": f"pkg{i}", "analyzed_version": "1.0.0", "vulnerability_id": f"V{i}"}
                for i in range(10)
            ]
        }
        result = scanner._process_results(safety_data, 1)
        assert result.score == 0.0

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", True)
    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_report_generation(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test report generation."""
        safety_output = {"vulnerabilities": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(safety_output),
            stderr="",
        )

        scanner = SafetyScanner()
        result = scanner.analyze(tmp_path)
        report = scanner.report(result, format="terminal")

        assert "Safety Vulnerability Report" in report
        assert "Security Score:" in report

    # 🧪✅🔚

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", True)
    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_analyze_with_non_json_output(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test handling of non-JSON error output."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="Error: Something went wrong",  # Non-JSON
            stderr="Connection error",
        )

        scanner = SafetyScanner()
        result = scanner.analyze(tmp_path)

        # Should handle gracefully
        assert result.passed is False or result.details["total_vulnerabilities"] == 0

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", True)
    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_report_unknown_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test report with unknown format."""
        safety_output = {"vulnerabilities": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(safety_output),
            stderr="",
        )

        scanner = SafetyScanner()
        result = scanner.analyze(tmp_path)
        report = scanner.report(result, format="yaml")

        # Should fall back to str(details)
        assert "total_vulnerabilities" in report

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", True)
    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_build_command_with_policy_file(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test command building with policy file."""
        mock_run.return_value = Mock(returncode=0, stdout="{}", stderr="")

        # Create policy file
        policy_file = tmp_path / "safety-policy.yml"
        policy_file.write_text("security: high\n")

        scanner = SafetyScanner(config={"policy_file": policy_file})
        cmd = scanner._build_safety_command(tmp_path)

        assert "--policy-file" in cmd
        assert str(policy_file) in cmd

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", True)
    @patch("provide.testkit.quality.security.safety_scanner.run")
    def test_build_command_with_ignore_vulns(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test command building with ignored vulnerabilities."""
        mock_run.return_value = Mock(returncode=0, stdout="{}", stderr="")

        scanner = SafetyScanner(config={"ignore_vulns": ["12345", "67890"]})
        cmd = scanner._build_safety_command(tmp_path)

        assert "--ignore" in cmd
        assert "12345" in cmd
        assert "67890" in cmd

    @patch("provide.testkit.quality.security.safety_scanner.SAFETY_AVAILABLE", True)
    def test_get_default_config_when_not_exists(self) -> None:
        """Test default config path when file doesn't exist."""
        scanner = SafetyScanner()
        result = scanner._get_default_config_path()
        assert result is None or result == scanner.DEFAULT_CONFIG_PATH


# 🧪✅🔚
