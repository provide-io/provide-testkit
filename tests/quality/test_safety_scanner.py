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

from provide.testkit.quality.base import QualityResult, QualityToolError
from provide.testkit.quality.security.safety_scanner import SAFETY_AVAILABLE, SafetyScanner


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
