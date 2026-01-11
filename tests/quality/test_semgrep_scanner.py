#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for Semgrep pattern-based static analysis security scanner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from provide.testkit.quality.base import QualityToolError
from provide.testkit.quality.security.semgrep_scanner import SEMGREP_AVAILABLE, SemgrepScanner


class TestSemgrepAvailability:
    """Tests for Semgrep availability checking."""

    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_semgrep_available_when_installed(self, mock_run: Mock) -> None:
        """Test detection when semgrep is installed."""
        mock_run.return_value = Mock(returncode=0)

        from provide.testkit.quality.security import semgrep_scanner

        result = semgrep_scanner._check_semgrep_available()

        assert result is True

    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_semgrep_unavailable_when_not_installed(self, mock_run: Mock) -> None:
        """Test detection when semgrep is not installed."""
        from provide.foundation.errors.process import ProcessError

        mock_run.side_effect = ProcessError("semgrep not found", command="semgrep --version")

        from provide.testkit.quality.security import semgrep_scanner

        result = semgrep_scanner._check_semgrep_available()

        assert result is False

    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_semgrep_unavailable_on_timeout(self, mock_run: Mock) -> None:
        """Test detection when version check times out."""
        mock_run.side_effect = TimeoutError("Command timed out")

        from provide.testkit.quality.security import semgrep_scanner

        result = semgrep_scanner._check_semgrep_available()

        assert result is False


@pytest.mark.skipif(not SEMGREP_AVAILABLE, reason="Semgrep not installed")
class TestSemgrepScanner:
    """Tests for Semgrep scanner (requires semgrep to be installed)."""

    def test_scanner_initialization(self) -> None:
        """Test scanner can be initialized."""
        scanner = SemgrepScanner()
        assert scanner.config == {} or "config" in scanner.config

    def test_scanner_initialization_with_config(self) -> None:
        """Test scanner initialization with custom config."""
        config = {"max_findings": 10, "config": ["p/python"]}
        scanner = SemgrepScanner(config)
        assert scanner.config["max_findings"] == 10


class TestSemgrepScannerMocked:
    """Tests for Semgrep scanner with mocked execution."""

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", False)
    def test_scanner_raises_on_unavailable_semgrep(self) -> None:
        """Test scanner raises error if semgrep is unavailable."""
        with pytest.raises(QualityToolError, match="Semgrep not available"):
            SemgrepScanner()

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_analyze_with_no_findings(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with no findings."""
        semgrep_output = {"results": [], "errors": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(semgrep_output),
            stderr="",
        )

        scanner = SemgrepScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is True
        assert result.score == 100.0
        assert result.details["total_findings"] == 0

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_analyze_with_findings(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with security findings."""
        semgrep_output = {
            "results": [
                {
                    "check_id": "python.security.injection.sql.sql-injection",
                    "path": "test.py",
                    "start": {"line": 10},
                    "end": {"line": 12},
                    "extra": {
                        "message": "Potential SQL injection detected",
                        "severity": "ERROR",
                        "metadata": {},
                        "lines": 'query = f"SELECT * FROM users WHERE id={user_id}"',
                    },
                }
            ],
            "errors": [],
        }
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(semgrep_output),
            stderr="",
        )

        scanner = SemgrepScanner(config={"max_findings": 0})
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert result.score == 85.0  # 100 - (1 * 15 for ERROR)
        assert result.details["total_findings"] == 1
        assert result.details["severity_breakdown"]["ERROR"] == 1
        assert result.details["findings"][0]["check_id"] == "python.security.injection.sql.sql-injection"

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_analyze_with_multiple_severities(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with multiple severity levels."""
        semgrep_output = {
            "results": [
                {
                    "check_id": "rule1",
                    "path": "test.py",
                    "start": {"line": 1},
                    "end": {"line": 1},
                    "extra": {"message": "Error", "severity": "ERROR", "metadata": {}, "lines": ""},
                },
                {
                    "check_id": "rule2",
                    "path": "test.py",
                    "start": {"line": 2},
                    "end": {"line": 2},
                    "extra": {"message": "Warning", "severity": "WARNING", "metadata": {}, "lines": ""},
                },
                {
                    "check_id": "rule3",
                    "path": "test.py",
                    "start": {"line": 3},
                    "end": {"line": 3},
                    "extra": {"message": "Info", "severity": "INFO", "metadata": {}, "lines": ""},
                },
            ],
            "errors": [],
        }
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(semgrep_output),
            stderr="",
        )

        scanner = SemgrepScanner()
        result = scanner.analyze(tmp_path)

        assert result.details["total_findings"] == 3
        assert result.details["severity_breakdown"]["ERROR"] == 1
        assert result.details["severity_breakdown"]["WARNING"] == 1
        assert result.details["severity_breakdown"]["INFO"] == 1
        # Score: 100 - (1*15 + 1*5 + 1*1) = 79
        assert result.score == 79.0

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_score_calculation(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test score calculation with various findings."""
        mock_run.return_value = Mock(returncode=0, stdout="{}", stderr="")

        scanner = SemgrepScanner()

        # Test with 0 findings
        result = scanner._process_results({"results": [], "errors": []}, 0)
        assert result.score == 100.0

        # Test with ERROR finding (15 points each)
        semgrep_data = {
            "results": [
                {
                    "check_id": "test",
                    "path": "test.py",
                    "start": {"line": 1},
                    "end": {"line": 1},
                    "extra": {"message": "test", "severity": "ERROR", "metadata": {}, "lines": ""},
                }
            ],
            "errors": [],
        }
        result = scanner._process_results(semgrep_data, 1)
        assert result.score == 85.0

        # Test score floor at 0
        semgrep_data = {
            "results": [
                {
                    "check_id": f"test{i}",
                    "path": "test.py",
                    "start": {"line": i},
                    "end": {"line": i},
                    "extra": {"message": "test", "severity": "ERROR", "metadata": {}, "lines": ""},
                }
                for i in range(10)
            ],
            "errors": [],
        }
        result = scanner._process_results(semgrep_data, 1)
        assert result.score == 0.0  # 100 - (10 * 15) = -50, capped at 0

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_analyze_limits_findings_list(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that findings list is limited to first 20."""
        semgrep_output = {
            "results": [
                {
                    "check_id": f"rule{i}",
                    "path": "test.py",
                    "start": {"line": i},
                    "end": {"line": i},
                    "extra": {"message": f"Finding {i}", "severity": "WARNING", "metadata": {}, "lines": ""},
                }
                for i in range(25)
            ],
            "errors": [],
        }
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(semgrep_output),
            stderr="",
        )

        scanner = SemgrepScanner()
        result = scanner.analyze(tmp_path)

        assert result.details["total_findings"] == 25
        assert len(result.details["findings"]) == 20  # Limited to 20

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_report_generation(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test report generation."""
        semgrep_output = {"results": [], "errors": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(semgrep_output),
            stderr="",
        )

        scanner = SemgrepScanner()
        result = scanner.analyze(tmp_path)
        report = scanner.report(result, format="terminal")

        assert "Semgrep Security Analysis Report" in report
        assert "Security Score:" in report
        assert "Total Findings:" in report

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    def test_build_command_with_options(self, tmp_path: Path) -> None:
        """Test command building with various options."""
        config = {
            "config": ["p/python", "p/security-audit"],
            "severity": ["ERROR", "WARNING"],
            "exclude": ["**/tests/**"],
            "include": ["**/*.py"],
            "max_memory": 4096,
            "timeout_per_rule": 30,
        }
        scanner = SemgrepScanner(config)
        cmd = scanner._build_semgrep_command(tmp_path)

        assert "semgrep" in cmd
        assert "--json" in cmd
        assert "--config" in cmd
        assert "p/python" in cmd
        assert "p/security-audit" in cmd
        assert "--severity" in cmd
        assert "ERROR,WARNING" in cmd
        assert "--exclude" in cmd
        assert "**/tests/**" in cmd
        assert "--include" in cmd
        assert "**/*.py" in cmd
        assert "--max-memory" in cmd
        assert "4096" in cmd
        assert "--timeout" in cmd
        assert "30" in cmd

    # 🧪✅🔚

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_analyze_with_non_json_output(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test handling of non-JSON output."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="Error: Invalid config",  # Non-JSON
            stderr="",
        )

        scanner = SemgrepScanner()
        result = scanner.analyze(tmp_path)

        # Should handle gracefully with empty data
        assert result.details["total_findings"] == 0

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_report_unknown_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test report with unknown format."""
        semgrep_output = {"results": [], "errors": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(semgrep_output),
            stderr="",
        )

        scanner = SemgrepScanner()
        result = scanner.analyze(tmp_path)
        report = scanner.report(result, format="csv")

        # Should fall back to str(details)
        assert "total_findings" in report

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_analyze_with_semgrep_errors(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test handling of semgrep errors in output."""
        semgrep_output = {
            "results": [],
            "errors": [
                {
                    "message": "Failed to parse file",
                    "path": "broken.py",
                    "type": "ParseError",
                }
            ],
        }
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(semgrep_output),
            stderr="",
        )

        scanner = SemgrepScanner()
        result = scanner.analyze(tmp_path)

        assert result.details["total_findings"] == 0
        assert len(result.details["errors"]) == 1

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    def test_get_default_config_when_not_exists(self) -> None:
        """Test default config path when file doesn't exist."""
        scanner = SemgrepScanner()
        result = scanner._get_default_config_path()
        assert result is None or result == scanner.DEFAULT_CONFIG_PATH

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_build_command_with_default_excludes(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that default excludes are applied."""
        mock_run.return_value = Mock(returncode=0, stdout="{}", stderr="")

        scanner = SemgrepScanner()  # No custom exclude config
        cmd = scanner._build_semgrep_command(tmp_path)

        # Should have default excludes
        assert "--exclude" in cmd
        assert any("test_" in str(item) or ".venv" in str(item) for item in cmd)

    @patch("provide.testkit.quality.security.semgrep_scanner.SEMGREP_AVAILABLE", True)
    @patch("provide.testkit.quality.security.semgrep_scanner.run")
    def test_analyze_with_empty_stdout(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test handling of empty stdout."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",  # Empty
            stderr="",
        )

        scanner = SemgrepScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is True
        assert result.details["total_findings"] == 0


# 🧪✅🔚
