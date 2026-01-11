#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for security scanning functionality."""

import json
from pathlib import Path

import pytest

from provide.testkit.mocking import Mock, patch  # type: ignore[import-untyped]
from provide.testkit.quality.base import QualityResult  # type: ignore[import-untyped]
from provide.testkit.quality.security.fixture import SecurityFixture  # type: ignore[import-untyped]
from provide.testkit.quality.security.scanner import (  # type: ignore[import-untyped]
    BANDIT_AVAILABLE,
    SecurityScanner,
)


@pytest.mark.skipif(not BANDIT_AVAILABLE, reason="bandit not available")
class TestSecurityScanner:
    """Test SecurityScanner functionality."""

    def test_initialization_default_config(self) -> None:
        """Test scanner initialization with default config."""
        scanner = SecurityScanner()
        assert scanner.config == {}
        assert scanner.artifact_dir is None

    def test_initialization_custom_config(self) -> None:
        """Test scanner initialization with custom config."""
        config = {"confidence": "high", "severity": "medium", "max_high_severity": 0}
        scanner = SecurityScanner(config)
        assert scanner.config == config

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_analyze_success(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
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

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_analyze_with_issues(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
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

    def test_discover_python_files(self, tmp_path: Path) -> None:
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

    def test_discover_python_files_custom_excludes(self, tmp_path: Path) -> None:
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

    def test_generate_text_report(self) -> None:
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

    def test_report_protocol_implementation(self) -> None:
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

    def test_verbosity_quiet_mode(self) -> None:
        """Test scanner with quiet verbosity."""
        scanner = SecurityScanner({"verbosity": "quiet"})
        assert scanner.verbosity == "quiet"

    def test_verbosity_verbose_mode(self) -> None:
        """Test scanner with verbose verbosity."""
        scanner = SecurityScanner({"verbosity": "verbose"})
        assert scanner.verbosity == "verbose"

    def test_verbosity_default(self) -> None:
        """Test scanner with default verbosity."""
        scanner = SecurityScanner()
        assert scanner.verbosity == "normal"

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_analyze_with_verbosity_override(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test analyze with verbosity override."""
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        mock_manager = Mock()
        mock_manager.files_list = ["test.py"]
        mock_manager.get_issue_list.return_value = []
        mock_manager_class.BanditManager.return_value = mock_manager

        scanner = SecurityScanner({"verbosity": "normal"})
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        # Override verbosity for this analysis
        result = scanner.analyze(test_file, verbosity="quiet")

        assert result.passed is True
        # Verbosity should be restored after analysis
        assert scanner.verbosity == "normal"

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_analyze_handles_exception(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test analyze exception handling."""
        mock_config_class.BanditConfig.side_effect = Exception("Bandit configuration failed")

        scanner = SecurityScanner()
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        result = scanner.analyze(test_file)

        assert result.passed is False
        assert "error" in result.details
        assert "Bandit configuration failed" in result.details["error"]
        assert result.execution_time is not None

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_analyze_empty_directory(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test analyze with no Python files."""
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        scanner = SecurityScanner()

        # Create empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = scanner.analyze(empty_dir)

        assert result.passed is True
        assert result.score == 100.0
        assert "No Python files found" in result.details.get("message", "")

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.atomic_write_text")  # type: ignore[misc]
    def test_analyze_artifact_generation_error(
        self,
        mock_write: Mock,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test artifact generation error handling."""
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        mock_manager = Mock()
        mock_manager.files_list = ["test.py"]
        mock_manager.get_issue_list.return_value = []
        mock_manager_class.BanditManager.return_value = mock_manager

        # Make artifact writing fail
        mock_write.side_effect = OSError("Permission denied")

        scanner = SecurityScanner()
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        result = scanner.analyze(test_file, artifact_dir=tmp_path / "artifacts")

        # Should still pass the scan, but record artifact error
        assert result.passed is True
        assert "artifact_error" in result.details
        assert "Permission denied" in result.details["artifact_error"]

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_analyze_with_multiple_severities(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test analyze with issues of multiple severities."""
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        # Create mock issues with different severities
        high_issue = Mock()
        high_issue.fname = "test.py"
        high_issue.lineno = 1
        high_issue.test_id = "B101"
        high_issue.test = "assert_used"
        high_issue.severity = "HIGH"
        high_issue.confidence = "HIGH"
        high_issue.text = "Use of assert detected"
        high_issue.get_code.return_value = "assert True"

        medium_issue = Mock()
        medium_issue.fname = "test.py"
        medium_issue.lineno = 2
        medium_issue.test_id = "B102"
        medium_issue.test = "exec_used"
        medium_issue.severity = "MEDIUM"
        medium_issue.confidence = "MEDIUM"
        medium_issue.text = "Use of exec"
        medium_issue.get_code.return_value = "exec('code')"

        low_issue = Mock()
        low_issue.fname = "test.py"
        low_issue.lineno = 3
        low_issue.test_id = "B103"
        low_issue.test = "weak_random"
        low_issue.severity = "LOW"
        low_issue.confidence = "LOW"
        low_issue.text = "Weak random"
        low_issue.get_code.return_value = "random.random()"

        mock_manager = Mock()
        mock_manager.files_list = ["test.py"]
        mock_manager.get_issue_list.return_value = [high_issue, medium_issue, low_issue]
        mock_manager_class.BanditManager.return_value = mock_manager

        scanner = SecurityScanner({"max_high_severity": 1, "max_medium_severity": 1, "min_score": 80.0})
        test_file = tmp_path / "test.py"
        test_file.write_text("test code")

        result = scanner.analyze(test_file)

        assert result.details["total_issues"] == 3
        assert result.details["severity_breakdown"]["HIGH"] == 1
        assert result.details["severity_breakdown"]["MEDIUM"] == 1
        assert result.details["severity_breakdown"]["LOW"] == 1
        # Score: 100 - (1*10 + 1*5 + 1*1) = 84
        assert result.score == 84.0
        assert result.passed is True  # Meets all thresholds

    def test_format_path_for_display_relative(self, tmp_path: Path) -> None:
        """Test path formatting for relative paths."""
        scanner = SecurityScanner()

        # Create a file in current directory
        test_file = tmp_path / "test.py"
        test_file.write_text("test")

        # Format should convert to relative if possible
        formatted = scanner._format_path_for_display(str(test_file.resolve()))
        # Result should be a valid path string
        assert isinstance(formatted, str)

    def test_format_path_for_display_absolute(self) -> None:
        """Test path formatting for absolute paths that can't be made relative."""
        scanner = SecurityScanner()

        # Use a path that can't be made relative to cwd
        abs_path = "/some/absolute/path/test.py"
        formatted = scanner._format_path_for_display(abs_path)
        assert isinstance(formatted, str)

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_generate_issues_report(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test detailed issues report generation."""
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        mock_issue = Mock()
        mock_issue.fname = str(tmp_path / "test.py")
        mock_issue.lineno = 10
        mock_issue.test_id = "B101"
        mock_issue.test = "assert_used"
        mock_issue.severity = "HIGH"
        mock_issue.confidence = "HIGH"
        mock_issue.text = "Use of assert detected"
        mock_issue.get_code.return_value = "assert True\nassert False"

        mock_manager = Mock()
        mock_manager.files_list = ["test.py"]
        mock_manager.get_issue_list.return_value = [mock_issue]
        mock_manager_class.BanditManager.return_value = mock_manager

        scanner = SecurityScanner()
        test_file = tmp_path / "test.py"
        test_file.write_text("assert True")

        result = scanner.analyze(test_file, artifact_dir=tmp_path / "artifacts")

        # Generate issues report
        issues_report = scanner._generate_issues_report(result)

        assert "Security Issues Report" in issues_report
        assert "Issue #1:" in issues_report
        assert "assert_used" in issues_report
        assert "B101" in issues_report

    def test_report_unknown_format(self) -> None:
        """Test report generation with unknown format."""
        scanner = SecurityScanner()

        result = QualityResult(
            tool="security",
            passed=True,
            score=100.0,
            details={"total_issues": 0},
        )

        report = scanner.report(result, "unknown_format")
        # Should fall back to string representation of details
        assert "total_issues" in report

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_analyze_with_custom_thresholds(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test analyze with custom threshold configuration."""
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        # Create a high severity issue
        mock_issue = Mock()
        mock_issue.fname = "test.py"
        mock_issue.lineno = 1
        mock_issue.test_id = "B101"
        mock_issue.test = "assert_used"
        mock_issue.severity = "HIGH"
        mock_issue.confidence = "HIGH"
        mock_issue.text = "Use of assert"
        mock_issue.get_code.return_value = "assert True"

        mock_manager = Mock()
        mock_manager.files_list = ["test.py"]
        mock_manager.get_issue_list.return_value = [mock_issue]
        mock_manager_class.BanditManager.return_value = mock_manager

        # Allow 1 high severity issue, require score >= 85
        scanner = SecurityScanner({"max_high_severity": 1, "min_score": 85.0})
        test_file = tmp_path / "test.py"
        test_file.write_text("assert True")

        result = scanner.analyze(test_file)

        # Score is 90 (100 - 10), meets min_score 85, and 1 HIGH <= 1 max
        assert result.score == 90.0
        assert result.passed is True
        assert result.details["thresholds"]["max_high_severity"] == 1
        assert result.details["thresholds"]["min_score"] == 85.0

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_analyze_directory_with_excludes(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test analyze with directory and exclude patterns."""
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        mock_manager = Mock()
        mock_manager.files_list = []
        mock_manager.get_issue_list.return_value = []
        mock_manager_class.BanditManager.return_value = mock_manager

        # Create directory structure with files that should be excluded
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('main')")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("print('test')")
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "lib.py").write_text("print('venv')")

        scanner = SecurityScanner({"exclude": ["*/tests/*", "*/.venv/*"]})
        files = scanner._discover_python_files(tmp_path)

        # Should only include src/main.py
        assert any("main.py" in f for f in files)
        assert not any("test_main.py" in f for f in files)
        assert not any("lib.py" in f for f in files)

    def test_apply_bandit_config(self) -> None:
        """Test _apply_bandit_config extension point."""
        scanner = SecurityScanner()

        # Create a mock config object
        mock_conf = Mock()

        # Should not raise exception (currently a no-op extension point)
        scanner._apply_bandit_config(mock_conf)

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_analyze_single_file(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test analyze on a single file."""
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        mock_manager = Mock()
        mock_manager.files_list = ["test.py"]
        mock_manager.get_issue_list.return_value = []
        mock_manager_class.BanditManager.return_value = mock_manager

        scanner = SecurityScanner()
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        result = scanner.analyze(test_file)

        assert result.passed is True
        assert result.score == 100.0
        # When analyzing a single file, it should be passed directly to bandit
        mock_manager.discover_files.assert_called_once()

    @patch("provide.testkit.quality.security.scanner.bandit_manager")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.scanner.bandit_config")  # type: ignore[misc]
    def test_process_results_score_floor(
        self,
        mock_config_class: Mock,
        mock_manager_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test that security score doesn't go below 0."""
        mock_config = Mock()
        mock_config.config = {"bandit": {}}
        mock_config_class.BanditConfig.return_value = mock_config

        # Create many high severity issues to drive score below 0
        issues = []
        for i in range(15):
            mock_issue = Mock()
            mock_issue.fname = "test.py"
            mock_issue.lineno = i
            mock_issue.test_id = f"B{i}"
            mock_issue.test = "security_issue"
            mock_issue.severity = "HIGH"
            mock_issue.confidence = "HIGH"
            mock_issue.text = f"Issue {i}"
            mock_issue.get_code.return_value = "code"
            issues.append(mock_issue)

        mock_manager = Mock()
        mock_manager.files_list = ["test.py"]
        mock_manager.get_issue_list.return_value = issues
        mock_manager_class.BanditManager.return_value = mock_manager

        scanner = SecurityScanner()
        test_file = tmp_path / "test.py"
        test_file.write_text("code with issues")

        result = scanner.analyze(test_file)

        # 15 HIGH issues = 100 - (15 * 10) = -50, but should floor at 0
        assert result.score == 0.0
        assert result.passed is False


class TestSecurityFixture:
    """Test SecurityFixture functionality."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test fixture initialization."""
        config = {"confidence": "high"}
        fixture = SecurityFixture(config=config, artifact_dir=tmp_path)

        assert fixture.config == config
        assert fixture.artifact_dir == tmp_path
        assert fixture.scanner is None

    @patch("provide.testkit.quality.security.fixture.BANDIT_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.fixture.SecurityScanner")  # type: ignore[misc]
    def test_setup_success(self, mock_scanner_class: Mock) -> None:
        """Test successful fixture setup."""
        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner

        fixture = SecurityFixture()
        fixture.setup()

        assert fixture.scanner == mock_scanner
        mock_scanner_class.assert_called_once_with({})

    @patch("provide.testkit.quality.security.fixture.BANDIT_AVAILABLE", False)  # type: ignore[misc]
    def test_setup_bandit_unavailable(self) -> None:
        """Test setup when bandit is unavailable."""
        fixture = SecurityFixture()

        with pytest.raises(pytest.skip.Exception):
            fixture.setup()

    @patch("provide.testkit.quality.security.fixture.BANDIT_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.fixture.SecurityScanner")  # type: ignore[misc]
    def test_scan_functionality(self, mock_scanner_class: Mock, tmp_path: Path) -> None:
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

    def test_scan_no_scanner(self) -> None:
        """Test scanning when no scanner is available."""
        fixture = SecurityFixture()
        # Don't call setup, so scanner remains None
        fixture._setup_complete = True  # Mark as setup but scanner is still None
        result = fixture.scan(Path("./test"))

        assert "error" in result
        assert result["error"] == "Scanner not available"

    def test_generate_report_no_scanner(self) -> None:
        """Test report generation when no scanner exists."""
        fixture = SecurityFixture()
        report = fixture.generate_report()

        assert report == "No security scanner available"

    @patch("provide.testkit.quality.security.fixture.BANDIT_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.fixture.SecurityScanner")  # type: ignore[misc]
    def test_generate_report_success(self, mock_scanner_class: Mock) -> None:
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
def test_real_security_integration(tmp_path: Path) -> None:
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
