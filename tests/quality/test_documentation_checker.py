#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for DocumentationChecker functionality."""

import json
from pathlib import Path

import pytest

from provide.testkit.mocking import Mock, patch  # type: ignore[import-untyped]
from provide.testkit.quality.base import QualityResult  # type: ignore[import-untyped]
from provide.testkit.quality.documentation.checker import (  # type: ignore[import-untyped]
    INTERROGATE_AVAILABLE,
    DocumentationChecker,
)


@pytest.mark.skipif(not INTERROGATE_AVAILABLE, reason="interrogate not available")
class TestDocumentationChecker:
    """Test DocumentationChecker functionality."""

    def test_initialization_default_config(self) -> None:
        """Test checker initialization with default config."""
        checker = DocumentationChecker()
        assert checker.config == {}
        assert checker.artifact_dir is None

    def test_initialization_custom_config(self) -> None:
        """Test checker initialization with custom config."""
        config = {"min_coverage": 95.0, "min_grade": "A", "min_score": 95.0, "ignore_init_method": False}
        checker = DocumentationChecker(config)
        assert checker.config == config

    @patch("provide.testkit.quality.documentation.checker.coverage.InterrogateCoverage")  # type: ignore[misc]
    @patch("provide.testkit.quality.documentation.checker.InterrogateConfig")  # type: ignore[misc]
    def test_analyze_success(
        self,
        mock_config_class: Mock,
        mock_coverage_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test successful documentation analysis."""
        # Mock interrogate components
        mock_results = Mock()
        mock_results.perc_covered = 85.0
        mock_results.missing_count = 3
        mock_results.covered_count = 17

        mock_coverage = Mock()
        mock_coverage.get_coverage.return_value = mock_results
        mock_coverage_class.return_value = mock_coverage

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        checker = DocumentationChecker({"min_coverage": 80.0, "min_grade": "B", "min_score": 80.0})

        # Create test Python file
        test_file = tmp_path / "test.py"
        test_file.write_text(
            '"""Module docstring."""\n\ndef documented_function():\n    """Function docstring."""\n    return True'
        )

        result = checker.analyze(test_file, artifact_dir=tmp_path / "artifacts")

        assert result.tool == "documentation"
        assert result.passed is True
        assert result.score == 90.0  # 85% coverage = B+ = 90 score
        assert result.details["total_coverage"] == 85.0
        assert result.details["covered_count"] == 17
        assert result.details["missing_count"] == 3
        assert result.details["total_count"] == 20
        assert result.details["grade"] == "B+"
        assert result.execution_time is not None

    @patch("provide.testkit.quality.documentation.checker.coverage.InterrogateCoverage")  # type: ignore[misc]
    @patch("provide.testkit.quality.documentation.checker.InterrogateConfig")  # type: ignore[misc]
    def test_analyze_low_coverage(
        self,
        mock_config_class: Mock,
        mock_coverage_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test analysis with low documentation coverage."""
        # Mock low coverage results
        mock_results = Mock()
        mock_results.perc_covered = 45.0
        mock_results.missing_count = 11
        mock_results.covered_count = 9

        mock_coverage = Mock()
        mock_coverage.get_coverage.return_value = mock_results
        mock_coverage_class.return_value = mock_coverage

        checker = DocumentationChecker({"min_coverage": 80.0, "min_grade": "C", "min_score": 70.0})

        test_file = tmp_path / "test.py"
        test_file.write_text("def undocumented_function():\n    return True")

        result = checker.analyze(test_file, artifact_dir=tmp_path / "artifacts")

        assert result.tool == "documentation"
        assert result.passed is False  # 45% < 80% required
        assert result.score == 40.0  # F grade = 40 score
        assert result.details["grade"] == "F"
        assert result.details["total_coverage"] == 45.0

    def test_build_interrogate_config_default(self) -> None:
        """Test interrogate config building with defaults."""
        checker = DocumentationChecker()
        config = checker._build_interrogate_config()

        assert config["ignore_init_method"] is True
        assert config["ignore_magic"] is True
        assert config["ignore_setters"] is True
        assert config["ignore_private"] is False
        assert config["verbose"] == 0
        assert "ignore_regex" in config

    def test_build_interrogate_config_custom(self) -> None:
        """Test interrogate config building with custom settings."""
        custom_config = {
            "min_coverage": 95.0,
            "ignore_init_method": False,
            "ignore_magic": False,
            "ignore_private": True,
            "verbose": 2,
            "ignore": ["custom_pattern"],
        }
        checker = DocumentationChecker(custom_config)
        config = checker._build_interrogate_config()

        assert config["ignore_init_method"] is False
        assert config["ignore_magic"] is False
        assert config["ignore_private"] is True
        assert config["verbose"] == 2
        assert config["ignore_regex"] == "custom_pattern"

    def test_grade_calculation(self) -> None:
        """Test documentation coverage grade calculation."""
        checker = DocumentationChecker()

        # Test grade boundaries
        test_cases = [
            (96.0, "A", 100.0),  # >= 95%
            (92.0, "A-", 95.0),  # >= 90%
            (87.0, "B+", 90.0),  # >= 85%
            (82.0, "B", 85.0),  # >= 80%
            (77.0, "B-", 80.0),  # >= 75%
            (72.0, "C+", 75.0),  # >= 70%
            (67.0, "C", 70.0),  # >= 65%
            (62.0, "C-", 65.0),  # >= 60%
            (55.0, "D", 55.0),  # >= 50%
            (45.0, "F", 40.0),  # < 50%
        ]

        for coverage, expected_grade, expected_score in test_cases:
            # Mock results for testing
            mock_results = Mock()
            mock_results.perc_covered = coverage
            mock_results.missing_count = 5
            mock_results.covered_count = 15

            result = checker._process_interrogate_results(mock_results, Mock())
            assert result.details["grade"] == expected_grade
            assert result.score == expected_score

    def test_passing_criteria(self) -> None:
        """Test documentation passing criteria."""
        config = {"min_coverage": 80.0, "min_grade": "B", "min_score": 85.0}
        checker = DocumentationChecker(config)

        # Test cases: (coverage, expected_pass)
        test_cases = [
            (90.0, True),  # Meets all criteria (A- grade, 95 score)
            (85.0, True),  # Meets all criteria (B+ grade, 90 score)
            (82.0, True),  # Meets coverage and grade (B), score = 85
            (79.0, False),  # Fails coverage requirement
            (75.0, False),  # Fails grade requirement (B- < B)
        ]

        for coverage, expected_pass in test_cases:
            mock_results = Mock()
            mock_results.perc_covered = coverage
            mock_results.missing_count = 2
            mock_results.covered_count = 18

            result = checker._process_interrogate_results(mock_results, Mock())
            assert result.passed == expected_pass

    @patch("provide.testkit.quality.documentation.checker.coverage.InterrogateCoverage")  # type: ignore[misc]
    @patch("provide.testkit.quality.documentation.checker.InterrogateConfig")  # type: ignore[misc]
    def test_analyze_with_file_details(
        self,
        mock_config_class: Mock,
        mock_coverage_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test analysis with detailed file coverage."""
        # Mock detailed coverage results
        mock_file_info = Mock()
        mock_file_info.filename = "test.py"
        mock_file_info.perc_covered = 75.0
        mock_file_info.covered_count = 3
        mock_file_info.missing_count = 1

        mock_results = Mock()
        mock_results.perc_covered = 75.0
        mock_results.missing_count = 1
        mock_results.covered_count = 3
        mock_results.detailed_coverage = [mock_file_info]

        mock_coverage = Mock()
        mock_coverage.get_coverage.return_value = mock_results
        mock_coverage_class.return_value = mock_coverage

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        checker = DocumentationChecker()
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")

        result = checker.analyze(test_file)

        assert "file_coverage" in result.details
        file_coverage = result.details["file_coverage"][0]
        assert file_coverage["file"] == "test.py"
        assert file_coverage["coverage"] == 75.0
        assert file_coverage["covered"] == 3
        assert file_coverage["missing"] == 1

    def test_generate_text_report(self) -> None:
        """Test text report generation."""
        checker = DocumentationChecker()

        result = QualityResult(
            tool="documentation",
            passed=True,
            score=85.0,
            details={
                "total_coverage": 82.5,
                "covered_count": 33,
                "missing_count": 7,
                "total_count": 40,
                "grade": "B",
                "thresholds": {"min_coverage": 80.0, "min_grade": "C", "min_score": 70.0},
            },
            execution_time=1.25,
        )

        report = checker._generate_text_report(result)

        assert "Documentation Coverage Report" in report
        assert "85.0%" in report
        assert "Grade: B" in report
        assert "Coverage: 82.5%" in report
        assert "Documented Items: 33" in report
        assert "Missing Documentation: 7" in report
        assert "Total Items: 40" in report
        assert "Minimum Coverage: 80.0%" in report
        assert "Execution Time: 1.25s" in report

    def test_generate_detail_report(self) -> None:
        """Test detailed file coverage report generation."""
        checker = DocumentationChecker()

        result = QualityResult(
            tool="documentation",
            passed=False,
            score=65.0,
            details={
                "file_coverage": [
                    {"file": "high_coverage.py", "coverage": 95.0, "covered": 19, "missing": 1},
                    {"file": "medium_coverage.py", "coverage": 75.0, "covered": 15, "missing": 5},
                    {"file": "low_coverage.py", "coverage": 45.0, "covered": 9, "missing": 11},
                ]
            },
        )

        report = checker._generate_detail_report(result)

        assert "Documentation Coverage by File" in report
        # Should be sorted by coverage (lowest first)
        lines = report.split("\n")
        assert any("❌ low_coverage.py: 45.0%" in line for line in lines)
        assert any("⚠️ medium_coverage.py: 75.0%" in line for line in lines)

    def test_report_protocol_implementation(self) -> None:
        """Test QualityTool protocol implementation."""
        checker = DocumentationChecker()

        result = QualityResult(
            tool="documentation",
            passed=False,
            score=55.0,
            details={"grade": "D", "total_coverage": 55.0, "covered_count": 11, "missing_count": 9},
        )

        # Test terminal format
        terminal_report = checker.report(result, "terminal")
        assert "Documentation Coverage Report" in terminal_report
        assert "❌ FAILED" in terminal_report
        assert "55.0%" in terminal_report
        assert "Grade: D" in terminal_report

        # Test JSON format
        json_report = checker.report(result, "json")
        data = json.loads(json_report)
        assert data["tool"] == "documentation"
        assert data["passed"] is False
        assert data["score"] == 55.0

        # Test other format
        other_report = checker.report(result, "other")
        assert str(result.details) == other_report


# 🧪✅🔚
