#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for TruffleHog secret detection scanner."""

import json
from pathlib import Path

import pytest

from provide.testkit.mocking import Mock, patch  # type: ignore[import-untyped]


class TestTruffleHogAvailability:
    """Test TruffleHog availability checking."""

    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_trufflehog_available_when_installed(self, mock_run: Mock) -> None:
        """Test detection when trufflehog is installed."""
        mock_run.return_value = Mock(returncode=0, stdout="3.0.0", stderr="")

        from provide.testkit.quality.security import trufflehog_scanner

        result = trufflehog_scanner._check_trufflehog_available()

        assert result is True
        mock_run.assert_called_once()

    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_trufflehog_unavailable_when_not_installed(self, mock_run: Mock) -> None:
        """Test detection when trufflehog is not installed."""
        from provide.foundation.errors.process import ProcessError

        mock_run.side_effect = ProcessError("trufflehog not found", command="trufflehog --version")

        from provide.testkit.quality.security import trufflehog_scanner

        result = trufflehog_scanner._check_trufflehog_available()

        assert result is False

    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_trufflehog_unavailable_on_timeout(self, mock_run: Mock) -> None:
        """Test detection when command times out."""
        mock_run.side_effect = TimeoutError("Command timed out")

        from provide.testkit.quality.security import trufflehog_scanner

        result = trufflehog_scanner._check_trufflehog_available()

        assert result is False


@pytest.mark.skipif(
    not pytest.importorskip("provide.testkit.quality.security.trufflehog_scanner", reason="Module not available").TRUFFLEHOG_AVAILABLE,
    reason="TruffleHog not installed",
)
class TestTruffleHogScanner:
    """Test TruffleHog scanner with real binary (if available)."""

    def test_scanner_initialization(self) -> None:
        """Test scanner initialization."""
        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        assert scanner.config == {}
        assert scanner.artifact_dir is None

    def test_scanner_initialization_with_config(self) -> None:
        """Test scanner initialization with custom config."""
        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        config = {"only_verified": True, "max_secrets": 0}
        scanner = TruffleHogScanner(config)
        assert scanner.config == config


class TestTruffleHogScannerMocked:
    """Test TruffleHog scanner with mocked execution."""

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", False)  # type: ignore[misc]
    def test_scanner_raises_on_unavailable_trufflehog(self) -> None:
        """Test that scanner raises QualityToolError when TruffleHog is unavailable."""
        from provide.testkit.quality.base import QualityToolError
        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        with pytest.raises(QualityToolError) as exc_info:
            TruffleHogScanner()

        assert "TruffleHog not available" in str(exc_info.value)

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_analyze_handles_timeout(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze timeout handling."""
        mock_run.side_effect = TimeoutError("Command timed out")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert "error" in result.details
        assert "timed out" in result.details["error"].lower()

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_analyze_handles_execution_errors(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze handles execution errors."""
        from provide.foundation.errors.process import ProcessError

        mock_run.side_effect = ProcessError("Execution failed", command="trufflehog filesystem")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert "error" in result.details

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_analyze_with_no_secrets(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with no secrets found."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner({"max_secrets": 0})
        result = scanner.analyze(tmp_path)

        assert result.passed is True
        assert result.score == 100.0
        assert result.details["total_secrets"] == 0
        assert result.details["verified_secrets"] == 0

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_analyze_with_unverified_secrets(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with unverified secrets found."""
        # TruffleHog outputs JSON lines
        finding = {
            "DetectorType": "PrivateKey",
            "DetectorName": "SSH",
            "Verified": False,
            "Redacted": "-----BEGIN PRIVATE KEY-----",
            "SourceMetadata": {
                "Data": {"Filesystem": {"file": "test.key", "line": 1}}
            },
            "ExtraData": {},
        }
        mock_run.return_value = Mock(returncode=1, stdout=json.dumps(finding) + "\n", stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner({"max_secrets": 0})
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert result.score == 85.0  # 100 - (1 * 15) for unverified
        assert result.details["total_secrets"] == 1
        assert result.details["verified_secrets"] == 0
        assert result.details["unverified_secrets"] == 1
        assert result.details["secrets"][0]["raw"] == "***REDACTED***"

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_analyze_with_verified_secrets(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze with verified (active) secrets found."""
        finding = {
            "DetectorType": "AWS",
            "DetectorName": "AWS Access Key",
            "Verified": True,
            "Redacted": "AKIA****************",
            "SourceMetadata": {
                "Data": {"Filesystem": {"file": "config.py", "line": 10}}
            },
            "ExtraData": {"account": "123456789"},
        }
        mock_run.return_value = Mock(returncode=1, stdout=json.dumps(finding) + "\n", stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner({"max_secrets": 0})
        result = scanner.analyze(tmp_path)

        assert result.passed is False
        assert result.score == 50.0  # 100 - (1 * 50) for verified
        assert result.details["total_secrets"] == 1
        assert result.details["verified_secrets"] == 1
        assert result.details["secrets"][0]["verified"] is True

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_score_calculation_mixed_secrets(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test score calculation with mix of verified and unverified secrets."""
        findings = [
            {
                "DetectorType": "AWS",
                "DetectorName": "AWS",
                "Verified": True,
                "Redacted": "AKIA****",
                "SourceMetadata": {"Data": {"Filesystem": {"file": "f1", "line": 1}}},
                "ExtraData": {},
            },
            {
                "DetectorType": "Generic",
                "DetectorName": "Generic Secret",
                "Verified": False,
                "Redacted": "secret",
                "SourceMetadata": {"Data": {"Filesystem": {"file": "f2", "line": 2}}},
                "ExtraData": {},
            },
        ]
        output = "\n".join(json.dumps(f) for f in findings)
        mock_run.return_value = Mock(returncode=1, stdout=output, stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path)

        # 1 verified (-50) + 1 unverified (-15) = 100 - 65 = 35
        assert result.score == 35.0
        assert result.details["total_secrets"] == 2
        assert result.details["verified_secrets"] == 1
        assert result.details["unverified_secrets"] == 1

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_analyze_with_invalid_json_lines(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test analyze handles invalid JSON lines gracefully."""
        # Mix of valid and invalid JSON
        output = "invalid json\n" + json.dumps({
            "DetectorType": "Generic",
            "DetectorName": "Secret",
            "Verified": False,
            "Redacted": "xxx",
            "SourceMetadata": {"Data": {"Filesystem": {"file": "f", "line": 1}}},
            "ExtraData": {},
        })
        mock_run.return_value = Mock(returncode=1, stdout=output, stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path)

        # Should only parse the valid JSON
        assert result.details["total_secrets"] == 1

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.atomic_write_text")  # type: ignore[misc]
    def test_analyze_with_artifact_generation_error(
        self,
        mock_write: Mock,
        mock_run: Mock,
        tmp_path: Path,
    ) -> None:
        """Test artifact generation error handling."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        mock_write.side_effect = OSError("Permission denied")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path, artifact_dir=tmp_path / "artifacts")

        # Should still pass the scan, but record artifact error
        assert result.passed is True
        assert "artifact_error" in result.details

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_report_terminal_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test terminal report generation."""
        finding = {
            "DetectorType": "Generic",
            "DetectorName": "Generic Secret",
            "Verified": False,
            "Redacted": "secret123",
            "SourceMetadata": {"Data": {"Filesystem": {"file": "test.py", "line": 5}}},
            "ExtraData": {},
        }
        mock_run.return_value = Mock(returncode=1, stdout=json.dumps(finding), stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path)

        report = scanner.report(result, "terminal")
        assert "TruffleHog Deep Secret Detection Report" in report
        assert "Total Secrets Found: 1" in report
        assert "Generic Secret" in report

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_report_json_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test JSON report generation."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path)

        json_report = scanner.report(result, "json")
        data = json.loads(json_report)
        assert data["tool"] == "trufflehog"
        assert data["passed"] is True
        assert data["score"] == 100.0

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_report_unknown_format(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test report with unknown format."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path)

        report = scanner.report(result, "unknown")
        # Should fall back to string representation
        assert "total_secrets" in report

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    def test_build_command_with_only_verified(self, tmp_path: Path) -> None:
        """Test command building with only_verified option."""
        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner({"only_verified": True})
        cmd = scanner._build_trufflehog_command(tmp_path)

        assert "--only-verified" in cmd

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    def test_build_command_with_no_verification(self, tmp_path: Path) -> None:
        """Test command building with no_verification option."""
        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner({"no_verification": True})
        cmd = scanner._build_trufflehog_command(tmp_path)

        assert "--no-verification" in cmd

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    def test_build_command_with_concurrency(self, tmp_path: Path) -> None:
        """Test command building with concurrency option."""
        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner({"concurrency": 4})
        cmd = scanner._build_trufflehog_command(tmp_path)

        assert "--concurrency" in cmd
        assert "4" in cmd

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    def test_build_command_with_include_detectors(self, tmp_path: Path) -> None:
        """Test command building with include_detectors option."""
        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner({"include_detectors": ["aws", "github"]})
        cmd = scanner._build_trufflehog_command(tmp_path)

        assert "--include-detectors" in cmd
        assert "aws,github" in cmd

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    def test_build_command_with_exclude_detectors(self, tmp_path: Path) -> None:
        """Test command building with exclude_detectors option."""
        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner({"exclude_detectors": ["generic"]})
        cmd = scanner._build_trufflehog_command(tmp_path)

        assert "--exclude-detectors" in cmd
        assert "generic" in cmd

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    def test_build_command_with_exclude_paths(self, tmp_path: Path) -> None:
        """Test command building with exclude_paths option."""
        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner({"exclude_paths": ["*.test", "vendor/*"]})
        cmd = scanner._build_trufflehog_command(tmp_path)

        assert cmd.count("--exclude-paths") == 2
        assert "*.test" in cmd
        assert "vendor/*" in cmd

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    def test_get_default_config_path(self, tmp_path: Path) -> None:
        """Test default config path detection."""
        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        # Should return Path or None
        default_config = scanner._get_default_config_path()
        assert default_config is None or isinstance(default_config, Path)

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_analyze_with_execution_time(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that execution time is recorded."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path)

        assert result.execution_time is not None
        assert result.execution_time >= 0

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_analyze_limits_secrets_list(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that secrets list is limited to 20 entries."""
        # Create 25 findings
        findings = []
        for i in range(25):
            findings.append(
                {
                    "DetectorType": "Generic",
                    "DetectorName": f"Secret{i}",
                    "Verified": False,
                    "Redacted": f"secret{i}",
                    "SourceMetadata": {"Data": {"Filesystem": {"file": f"f{i}", "line": i}}},
                    "ExtraData": {},
                }
            )
        output = "\n".join(json.dumps(f) for f in findings)
        mock_run.return_value = Mock(returncode=1, stdout=output, stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path)

        assert result.details["total_secrets"] == 25
        assert len(result.details["secrets"]) == 20  # Limited to 20

    @patch("provide.testkit.quality.security.trufflehog_scanner.TRUFFLEHOG_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.security.trufflehog_scanner.run")  # type: ignore[misc]
    def test_analyze_score_floor(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that score doesn't go below 0."""
        # Create many verified secrets to drive score below 0
        findings = []
        for i in range(10):
            findings.append(
                {
                    "DetectorType": "AWS",
                    "DetectorName": f"AWS{i}",
                    "Verified": True,
                    "Redacted": f"AKIA{i}",
                    "SourceMetadata": {"Data": {"Filesystem": {"file": f"f{i}", "line": i}}},
                    "ExtraData": {},
                }
            )
        output = "\n".join(json.dumps(f) for f in findings)
        mock_run.return_value = Mock(returncode=1, stdout=output, stderr="")

        from provide.testkit.quality.security.trufflehog_scanner import TruffleHogScanner

        scanner = TruffleHogScanner()
        result = scanner.analyze(tmp_path)

        # 10 verified = 100 - (10 * 50) = -400, but should floor at 0
        assert result.score == 0.0
        assert result.passed is False


# 🧪✅🔚
