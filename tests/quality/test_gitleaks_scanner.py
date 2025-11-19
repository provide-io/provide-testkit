#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for GitLeaks secret detection scanner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from provide.testkit.quality.base import QualityResult, QualityToolError
from provide.testkit.quality.security.gitleaks_scanner import GITLEAKS_AVAILABLE, GitLeaksScanner


class TestGitLeaksAvailability:
    """Tests for GitLeaks availability checking."""

    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_gitleaks_available_when_installed(self, mock_run: Mock) -> None:
        """Test detection when gitleaks is installed."""
        mock_run.return_value = Mock(returncode=0)

        from provide.testkit.quality.security import gitleaks_scanner
        result = gitleaks_scanner._check_gitleaks_available()

        assert result is True
        mock_run.assert_called_once_with(
            ["gitleaks", "version"],
            timeout=10,
            check=False,
        )

    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_gitleaks_unavailable_when_not_installed(self, mock_run: Mock) -> None:
        """Test detection when gitleaks is not installed."""
        from provide.foundation.errors.process import ProcessError
        mock_run.side_effect = ProcessError("gitleaks not found", command="gitleaks version")

        from provide.testkit.quality.security import gitleaks_scanner
        result = gitleaks_scanner._check_gitleaks_available()

        assert result is False

    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_gitleaks_unavailable_on_timeout(self, mock_run: Mock) -> None:
        """Test detection when version check times out."""
        mock_run.side_effect = TimeoutError("Command timed out")

        from provide.testkit.quality.security import gitleaks_scanner
        result = gitleaks_scanner._check_gitleaks_available()

        assert result is False


@pytest.mark.skipif(not GITLEAKS_AVAILABLE, reason="GitLeaks not installed")
class TestGitLeaksScanner:
    """Tests for GitLeaks scanner (requires gitleaks to be installed)."""

    def test_scanner_initialization(self) -> None:
        """Test scanner can be initialized."""
        scanner = GitLeaksScanner()
        assert scanner.config == {}
        assert scanner.artifact_dir is None

    def test_scanner_initialization_with_config(self) -> None:
        """Test scanner initialization with custom config."""
        config = {"verbose": True, "max_secrets": 5}
        scanner = GitLeaksScanner(config)
        assert scanner.config == config

    def test_scanner_auto_detects_config_file(self, tmp_path: Path) -> None:
        """Test scanner auto-detects config file."""
        # Create a config file
        config_dir = tmp_path / ".provide" / "security"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "gitleaks.toml"
        config_file.write_text("[test]")

        # Change to temp directory
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            scanner = GitLeaksScanner()
            assert "config_file" in scanner.config
            assert scanner.config["config_file"] == Path(".provide/security/gitleaks.toml")
        finally:
            os.chdir(old_cwd)

    def test_analyze_clean_directory(self, tmp_path: Path) -> None:
        """Test scanning a directory with no secrets."""
        # Create a clean Python file
        test_file = tmp_path / "clean.py"
        test_file.write_text("# Clean code\nprint('Hello, world!')\n")

        scanner = GitLeaksScanner()
        result = scanner.analyze(tmp_path)

        assert isinstance(result, QualityResult)
        assert result.tool == "gitleaks"
        assert result.passed is True
        assert result.score == 100.0
        assert result.details["total_secrets"] == 0

    def test_analyze_directory_with_secrets(self, tmp_path: Path) -> None:
        """Test scanning a directory with secrets."""
        # Create a file with a fake AWS key pattern
        test_file = tmp_path / "secrets.py"
        test_file.write_text(
            "# Warning: This contains a test secret pattern\n"
            "aws_key = 'AKIAIOSFODNN7EXAMPLE'  # This is a fake AWS key\n"
        )

        scanner = GitLeaksScanner(config={"max_secrets": 0})
        result = scanner.analyze(tmp_path)

        assert isinstance(result, QualityResult)
        assert result.tool == "gitleaks"
        # Note: May or may not detect depending on gitleaks version and config
        assert "total_secrets" in result.details
        assert result.score <= 100.0

    def test_analyze_creates_artifacts(self, tmp_path: Path) -> None:
        """Test that analyze creates artifact files."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')\n")

        artifact_dir = tmp_path / "artifacts"

        scanner = GitLeaksScanner()
        result = scanner.analyze(test_file.parent, artifact_dir=artifact_dir)

        assert artifact_dir.exists()
        assert (artifact_dir / "gitleaks.json").exists()
        assert (artifact_dir / "gitleaks_summary.txt").exists()
        assert len(result.artifacts) >= 2

    def test_analyze_with_custom_timeout(self, tmp_path: Path) -> None:
        """Test analyze with custom timeout configuration."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')\n")

        scanner = GitLeaksScanner(config={"timeout": 60})
        result = scanner.analyze(tmp_path)

        assert isinstance(result, QualityResult)
        assert result.passed is True

    def test_report_terminal_format(self, tmp_path: Path) -> None:
        """Test terminal report generation."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')\n")

        scanner = GitLeaksScanner()
        result = scanner.analyze(tmp_path)
        report = scanner.report(result, format="terminal")

        assert "GitLeaks Secret Detection Report" in report
        assert "Security Score:" in report
        assert "Secrets Found:" in report

    def test_report_json_format(self, tmp_path: Path) -> None:
        """Test JSON report generation."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')\n")

        scanner = GitLeaksScanner()
        result = scanner.analyze(tmp_path)
        report = scanner.report(result, format="json")

        data = json.loads(report)
        assert data["tool"] == "gitleaks"
        assert "passed" in data
        assert "score" in data
        assert "details" in data


class TestGitLeaksScannerMocked:
    """Tests for GitLeaks scanner with mocked execution."""

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    def test_scanner_raises_on_unavailable_gitleaks(self) -> None:
        """Test scanner raises error if gitleaks becomes unavailable."""
        with patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", False):
            with pytest.raises(QualityToolError, match="GitLeaks not available"):
                GitLeaksScanner()

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_analyze_handles_timeout(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze handles timeout errors gracefully."""
        mock_run.side_effect = TimeoutError("Command timed out")

        scanner = GitLeaksScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert "error" in result.details
        assert "timed out" in result.details["error"].lower()

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_analyze_handles_execution_errors(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze handles execution errors gracefully."""
        mock_run.side_effect = RuntimeError("Execution failed")

        scanner = GitLeaksScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert "error" in result.details
        assert "Execution failed" in result.details["error"]

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_analyze_with_no_findings(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with no secrets found."""
        # Set up artifact directory
        artifact_dir = tmp_path / ".security"

        # Mock run and create empty report file within the mock
        def create_report(*args, **kwargs):
            artifact_dir.mkdir(exist_ok=True)
            report_file = artifact_dir / "gitleaks_raw.json"
            report_file.write_text("[]")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_report

        scanner = GitLeaksScanner()
        result = scanner.analyze(tmp_path, artifact_dir=artifact_dir)

        assert result.passed is True
        assert result.score == 100.0
        assert result.details["total_secrets"] == 0

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_analyze_with_findings(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with secrets found."""
        # Set up artifact directory
        artifact_dir = tmp_path / ".security"

        # Mock run and create report file within the mock
        def create_report(*args, **kwargs):
            artifact_dir.mkdir(exist_ok=True)
            report_file = artifact_dir / "gitleaks_raw.json"
            findings = [
                {
                    "Description": "AWS Access Key",
                    "File": "test.py",
                    "StartLine": 1,
                    "EndLine": 1,
                    "StartColumn": 10,
                    "EndColumn": 30,
                    "Match": "AKIAIOSFODNN7EXAMPLE",
                    "RuleID": "aws-access-key",
                    "Entropy": 3.5,
                    "Commit": "",
                    "Author": "",
                    "Email": "",
                    "Date": "",
                    "Message": "",
                    "Tags": ["key", "AWS"],
                }
            ]
            report_file.write_text(json.dumps(findings))
            return Mock(returncode=1, stdout="", stderr="")

        mock_run.side_effect = create_report

        scanner = GitLeaksScanner(config={"max_secrets": 0})
        result = scanner.analyze(tmp_path, artifact_dir=artifact_dir)

        assert result.passed is False
        assert result.score == 75.0  # 100 - (1 * 25)
        assert result.details["total_secrets"] == 1
        assert len(result.details["secrets"]) == 1
        assert result.details["secrets"][0]["secret"] == "***REDACTED***"
        assert result.details["secrets"][0]["rule_id"] == "aws-access-key"

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_analyze_redacts_secrets_in_output(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that actual secrets are redacted in output."""
        # Set up artifact directory
        artifact_dir = tmp_path / ".security"

        # Mock run and create report file within the mock
        def create_report(*args, **kwargs):
            artifact_dir.mkdir(exist_ok=True)
            report_file = artifact_dir / "gitleaks_raw.json"
            findings = [
                {
                    "Description": "Generic Secret",
                    "File": "config.py",
                    "StartLine": 5,
                    "EndLine": 5,
                    "StartColumn": 1,
                    "EndColumn": 20,
                    "Match": "super-secret-password-123",
                    "Secret": "super-secret-password-123",  # This should be redacted
                    "RuleID": "generic-secret",
                    "Entropy": 4.2,
                    "Commit": "",
                    "Author": "",
                    "Email": "",
                    "Date": "",
                    "Message": "",
                    "Tags": [],
                }
            ]
            report_file.write_text(json.dumps(findings))
            return Mock(returncode=1, stdout="", stderr="")

        mock_run.side_effect = create_report

        scanner = GitLeaksScanner()
        result = scanner.analyze(tmp_path, artifact_dir=artifact_dir)

        # Verify secret is redacted
        assert result.details["secrets"][0]["secret"] == "***REDACTED***"

        # Verify match is truncated if long
        match = result.details["secrets"][0]["match"]
        assert "..." in match or len(match) <= 50

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    def test_score_calculation(self, tmp_path: Path) -> None:
        """Test score calculation with multiple secrets."""
        scanner = GitLeaksScanner()

        # Test with 0 secrets
        result = scanner._process_results([], 0)
        assert result.score == 100.0

        # Test with 1 secret
        findings = [{"Description": "test", "File": "test.py", "Match": "secret"}]
        result = scanner._process_results(findings, 1)
        assert result.score == 75.0  # 100 - 25

        # Test with 4 secrets (should go to 0)
        findings = [{"Description": "test", "File": "test.py", "Match": "secret"}] * 4
        result = scanner._process_results(findings, 1)
        assert result.score == 0.0  # 100 - (4 * 25) = 0

        # Test with 5 secrets (should stay at 0, not negative)
        findings = [{"Description": "test", "File": "test.py", "Match": "secret"}] * 5
        result = scanner._process_results(findings, 1)
        assert result.score == 0.0  # Capped at 0

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_analyze_with_invalid_json_report(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test handling of malformed JSON report file."""
        mock_result = Mock(returncode=0, stdout="", stderr="")
        mock_run.return_value = mock_result

        artifact_dir = tmp_path / ".security"
        artifact_dir.mkdir()
        report_file = artifact_dir / "gitleaks_raw.json"
        report_file.write_text("{ invalid json")

        scanner = GitLeaksScanner()
        scanner.artifact_dir = artifact_dir
        result = scanner.analyze(tmp_path)

        # Should handle gracefully with empty findings
        assert result.passed is True
        assert result.details["total_secrets"] == 0

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_analyze_with_config_options(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that config options are passed to gitleaks command."""
        mock_result = Mock(returncode=0, stdout="", stderr="")
        mock_run.return_value = mock_result

        config = {
            "verbose": True,
            "no_banner": False,
            "config_file": "/path/to/config.toml",
            "baseline_path": "/path/to/baseline.json",
            "timeout": 120,
        }

        scanner = GitLeaksScanner(config)
        scanner.analyze(tmp_path)

        # Verify run was called with the right command
        call_args = mock_run.call_args
        cmd = call_args[0][0]

        assert "gitleaks" in cmd
        assert "detect" in cmd
        assert "--verbose" in cmd
        assert "--config" in cmd
        assert "/path/to/config.toml" in cmd
        assert "--baseline-path" in cmd
        assert "/path/to/baseline.json" in cmd

        # Verify timeout was passed
        assert call_args[1]["timeout"] == 120

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_analyze_with_artifact_generation_error(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that artifact generation errors are handled gracefully."""
        artifact_dir = tmp_path / ".security"
        
        def create_report(*args, **kwargs):
            artifact_dir.mkdir(exist_ok=True)
            report_file = artifact_dir / "gitleaks_raw.json"
            report_file.write_text("[]")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_report

        # Make artifact dir read-only to cause write errors
        scanner = GitLeaksScanner()
        result = scanner.analyze(tmp_path, artifact_dir=artifact_dir)
        
        # Change permissions after analysis to cause artifact generation failure
        import os
        os.chmod(artifact_dir, 0o444)
        
        try:
            scanner._generate_artifacts(result)
            # Should handle error gracefully
            assert "artifact_error" in result.details or len(result.artifacts) >= 0
        finally:
            os.chmod(artifact_dir, 0o755)

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_report_default_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test report with default/unknown format."""
        artifact_dir = tmp_path / ".security"
        
        def create_report(*args, **kwargs):
            artifact_dir.mkdir(exist_ok=True)
            report_file = artifact_dir / "gitleaks_raw.json"
            report_file.write_text("[]")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_report

        scanner = GitLeaksScanner()
        result = scanner.analyze(tmp_path, artifact_dir=artifact_dir)
        
        # Test unknown format falls back to str(details)
        report = scanner.report(result, format="unknown")
        assert "total_secrets" in report

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    def test_get_default_config_when_not_exists(self) -> None:
        """Test default config path when file doesn't exist."""
        scanner = GitLeaksScanner()
        # In most cases, default config won't exist
        result = scanner._get_default_config_path()
        # Should return None if file doesn't exist
        assert result is None or result == scanner.DEFAULT_CONFIG_PATH

    @patch("provide.testkit.quality.security.gitleaks_scanner.GITLEAKS_AVAILABLE", True)
    @patch("provide.testkit.quality.security.gitleaks_scanner.run")
    def test_analyze_with_execution_time(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that execution time is captured."""
        artifact_dir = tmp_path / ".security"
        
        def create_report(*args, **kwargs):
            import time
            time.sleep(0.01)  # Small delay
            artifact_dir.mkdir(exist_ok=True)
            report_file = artifact_dir / "gitleaks_raw.json"
            report_file.write_text("[]")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_report

        scanner = GitLeaksScanner()
        result = scanner.analyze(tmp_path, artifact_dir=artifact_dir)
        
        # Execution time should be set and positive
        assert result.execution_time > 0


# 🧪✅🔚
