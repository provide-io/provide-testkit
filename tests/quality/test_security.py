# 
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for security scanning functionality."""

import json
from pathlib import Path
from provide.testkit.mocking import Mock, patch

import pytest

from provide.testkit.quality.base import QualityResult
from provide.testkit.quality.security.fixture import SecurityFixture
from provide.testkit.quality.security.scanner import BANDIT_AVAILABLE, SecurityScanner


@pytest.mark.skipif(not BANDIT_AVAILABLE, reason="bandit not available")
class TestSecurityScanner:
    """Test SecurityScanner functionality."""

    def test_initialization_default_config(self):
        """Test scanner initialization with default config."""
        scanner = SecurityScanner()
        assert scanner.config == {}
        assert scanner.artifact_dir is None

    def test_initialization_custom_config(self):
        """Test scanner initialization with custom config."""
        config = {"confidence": "high", "severity": "medium", "max_high_severity": 0}
        scanner = SecurityScanner(config)
        assert scanner.config == config

    @patch("provide.testkit.quality.security.scanner.bandit_manager")
    @patch("provide.testkit.quality.security.scanner.bandit_config")
    def test_analyze_success(self, mock_config_class, mock_manager_class, tmp_path):
        """Test successful security analysis."""
        # Mock bandit components
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        mock_manager = Mock()
        mock_manager.files_list = ["file1.py", "file2.py"]
        mock_manager.get_issue_list.return_value = []
        mock_manager_class.BanditManager.return_value = mock_manager

        scanner = SecurityScanner({"max_high_severity": 0})

        # Create test Python file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('Hello World')")

        result = scanner.analyze(test_file, artifact_dir=tmp_path / "artifacts")

        assert result.tool == "security"
        assert result.passed is True
        assert result.score == 100.0
        assert result.execution_time is not None
        assert "total_files" in result.details

    @patch("provide.testkit.quality.security.scanner.bandit_manager")
    @patch("provide.testkit.quality.security.scanner.bandit_config")
    def test_analyze_with_issues(self, mock_config_class, mock_manager_class, tmp_path):
        """Test analysis with security issues found."""
        # Mock bandit components
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        # Create mock security issue
        mock_issue = Mock()
        mock_issue.fname = "test.py"
        mock_issue.lineno = 10
        mock_issue.test_id = "B101"
        mock_issue.test = "assert_used"
        mock_issue.severity = "HIGH"
        mock_issue.confidence = "HIGH"
        mock_issue.text = "Use of assert detected"
        mock_issue.get_code.return_value = "assert True"

        mock_manager = Mock()
        mock_manager.files_list = ["test.py"]
        mock_manager.get_issue_list.return_value = [mock_issue]
        mock_manager_class.BanditManager.return_value = mock_manager

        scanner = SecurityScanner({"max_high_severity": 0})

        test_file = tmp_path / "test.py"
        test_file.write_text("assert True")

        result = scanner.analyze(test_file, artifact_dir=tmp_path / "artifacts")

        assert result.tool == "security"
        assert result.passed is False  # Should fail due to max_high_severity: 0
        assert result.score == 90.0  # 100 - (1 * 10) for high severity issue
        assert result.details["total_issues"] == 1
        assert result.details["severity_breakdown"]["HIGH"] == 1

    def test_discover_python_files(self, tmp_path):
        """Test Python file discovery."""
        scanner = SecurityScanner()

        # Create test structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('main')")
        (tmp_path / "src" / "utils.py").write_text("print('utils')")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("print('test')")

        files = scanner._discover_python_files(tmp_path)

        # Should include src files but exclude test files by default
        assert any("main.py" in f for f in files)
        assert any("utils.py" in f for f in files)
        assert not any("test_main.py" in f for f in files)

    def test_discover_python_files_custom_excludes(self, tmp_path):
        """Test Python file discovery with custom excludes."""
        config = {"exclude": ["*/private/*"]}
        scanner = SecurityScanner(config)

        # Create test structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('main')")
        (tmp_path / "private").mkdir()
        (tmp_path / "private" / "secret.py").write_text("print('secret')")

        files = scanner._discover_python_files(tmp_path)

        assert any("main.py" in f for f in files)
        assert not any("secret.py" in f for f in files)

    def test_generate_text_report(self):
        """Test text report generation."""
        scanner = SecurityScanner()

        result = QualityResult(
            tool="security",
            passed=True,
            score=95.0,
            details={
                "total_files": 10,
                "total_issues": 2,
                "severity_breakdown": {"HIGH": 0, "MEDIUM": 2, "LOW": 0},
                "confidence_breakdown": {"HIGH": 1, "MEDIUM": 1, "LOW": 0},
            },
        )

        report = scanner._generate_text_report(result)

        assert "Security Analysis Report" in report
        assert "95.0%" in report
        assert "Files Scanned: 10" in report
        assert "Total Issues: 2" in report
        assert "MEDIUM: 2" in report

    def test_report_protocol_implementation(self):
        """Test QualityTool protocol implementation."""
        scanner = SecurityScanner()

        result = QualityResult(
            tool="security",
            passed=False,
            score=75.0,
            details={"total_issues": 5, "severity_breakdown": {"HIGH": 1, "MEDIUM": 2, "LOW": 2}},
        )

        report = scanner.report(result, "terminal")
        assert "Security Analysis Report" in report
        assert "❌ FAILED" in report
        assert "75.0%" in report

        json_report = scanner.report(result, "json")
        data = json.loads(json_report)
        assert data["tool"] == "security"
        assert data["passed"] is False
        assert data["score"] == 75.0


class TestSecurityFixture:
    """Test SecurityFixture functionality."""

    def test_initialization(self, tmp_path):
        """Test fixture initialization."""
        config = {"confidence": "high"}
        fixture = SecurityFixture(config=config, artifact_dir=tmp_path)

        assert fixture.config == config
        assert fixture.artifact_dir == tmp_path
        assert fixture.scanner is None

    @patch("provide.testkit.quality.security.fixture.BANDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.fixture.SecurityScanner")
    def test_setup_success(self, mock_scanner_class):
        """Test successful fixture setup."""
        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner

        fixture = SecurityFixture()
        fixture.setup()

        assert fixture.scanner == mock_scanner
        mock_scanner_class.assert_called_once_with({})

    @patch("provide.testkit.quality.security.fixture.BANDIT_AVAILABLE", False)
    def test_setup_bandit_unavailable(self):
        """Test setup when bandit is unavailable."""
        fixture = SecurityFixture()

        with pytest.raises(pytest.skip.Exception):
            fixture.setup()

    @patch("provide.testkit.quality.security.fixture.BANDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.fixture.SecurityScanner")
    def test_scan_functionality(self, mock_scanner_class, tmp_path):
        """Test scanning functionality."""
        mock_scanner = Mock()
        mock_result = QualityResult(tool="security", passed=True, score=95.0, details={"total_issues": 1})
        mock_scanner.analyze.return_value = mock_result
        mock_scanner_class.return_value = mock_scanner

        fixture = SecurityFixture(artifact_dir=tmp_path)
        fixture.setup()

        result = fixture.scan(Path("./test"))

        assert result["passed"] is True
        assert result["score"] == 95.0
        assert result["issues"] == 1
        mock_scanner.analyze.assert_called_once()

    def test_scan_no_scanner(self):
        """Test scanning when no scanner is available."""
        fixture = SecurityFixture()
        # Don't call setup, so scanner remains None
        fixture._setup_complete = True  # Mark as setup but scanner is still None
        result = fixture.scan(Path("./test"))

        assert "error" in result
        assert result["error"] == "Scanner not available"

    def test_generate_report_no_scanner(self):
        """Test report generation when no scanner exists."""
        fixture = SecurityFixture()
        report = fixture.generate_report()

        assert report == "No security scanner available"

    @patch("provide.testkit.quality.security.fixture.BANDIT_AVAILABLE", True)
    @patch("provide.testkit.quality.security.fixture.SecurityScanner")
    def test_generate_report_success(self, mock_scanner_class):
        """Test successful report generation."""
        mock_scanner = Mock()
        mock_scanner.report.return_value = "Security Report"
        mock_scanner_class.return_value = mock_scanner

        fixture = SecurityFixture()
        fixture.setup()

        # Add a mock result
        mock_result = QualityResult(tool="security", passed=True)
        fixture.add_result(mock_result)

        report = fixture.generate_report("terminal")

        assert report == "Security Report"
        mock_scanner.report.assert_called_once_with(mock_result, "terminal")


# Integration tests would go here if we had actual bandit
# For now, we'll test the mocked behavior


@pytest.mark.integration
@pytest.mark.skipif(not BANDIT_AVAILABLE, reason="bandit not available")
def test_real_security_integration(tmp_path):
    """Integration test with real bandit (if available)."""
    # Create a Python file with potential security issue
    test_file = tmp_path / "vulnerable.py"
    test_file.write_text("""
import subprocess

def run_command(user_input):
    # This should trigger a security warning
    subprocess.call(user_input, shell=True)

def safe_function():
    return "This is safe"

def another_unsafe():
    # Another potential issue
    exec("print('executed')")
""")

    # Create security scanner
    config = {
        "confidence": "medium",
        "severity": "medium",
        "max_high_severity": 2,
        "max_medium_severity": 5,
        "min_score": 50.0,
    }

    scanner = SecurityScanner(config)
    scanner.artifact_dir = tmp_path / "artifacts"

    # Run security scan
    result = scanner.analyze(tmp_path)

    # Should find security issues in the vulnerable code
    assert result.tool == "security"
    assert result.score is not None
    assert result.details["total_issues"] > 0
    assert "severity_breakdown" in result.details

    # Generate reports
    terminal_report = scanner.report(result, "terminal")
    assert "Security Analysis Report" in terminal_report

    json_report = scanner.report(result, "json")
    data = json.loads(json_report)
    assert data["tool"] == "security"

# 🧪✅🔚
