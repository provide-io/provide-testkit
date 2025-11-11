#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for DocumentationFixture functionality."""

from pathlib import Path

import pytest

from provide.testkit.mocking import Mock, patch  # type: ignore[import-untyped]
from provide.testkit.quality.base import QualityResult  # type: ignore[import-untyped]
from provide.testkit.quality.documentation.fixture import DocumentationFixture  # type: ignore[import-untyped]


class TestDocumentationFixture:
    """Test DocumentationFixture functionality."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test fixture initialization."""
        config = {"min_coverage": 90.0}
        fixture = DocumentationFixture(config=config, artifact_dir=tmp_path)

        assert fixture.config == config
        assert fixture.artifact_dir == tmp_path
        assert fixture.analyzer is None

    @patch("provide.testkit.quality.documentation.fixture.INTERROGATE_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.documentation.fixture.DocumentationChecker")  # type: ignore[misc]
    def test_setup_success(self, mock_checker_class: Mock) -> None:
        """Test successful fixture setup."""
        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker

        fixture = DocumentationFixture()
        fixture.setup()

        assert fixture.analyzer == mock_checker
        mock_checker_class.assert_called_once_with({})

    @patch("provide.testkit.quality.documentation.fixture.INTERROGATE_AVAILABLE", False)  # type: ignore[misc]
    def test_setup_interrogate_unavailable(self) -> None:
        """Test setup when interrogate is unavailable."""
        fixture = DocumentationFixture()

        with pytest.raises(pytest.skip.Exception):
            fixture.setup()

    @patch("provide.testkit.quality.documentation.fixture.INTERROGATE_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.documentation.fixture.DocumentationChecker")  # type: ignore[misc]
    def test_analyze_functionality(self, mock_checker_class: Mock, tmp_path: Path) -> None:
        """Test analysis functionality."""
        mock_checker = Mock()
        mock_result = QualityResult(
            tool="documentation",
            passed=True,
            score=90.0,
            details={
                "grade": "A-",
                "total_coverage": 92.0,
                "covered_count": 23,
                "missing_count": 2,
                "total_count": 25,
                "file_coverage": [{"file": "test.py", "coverage": 92.0, "covered": 23, "missing": 2}],
                "thresholds": {"min_coverage": 80.0},
            },
            execution_time=0.75,
        )
        mock_checker.analyze.return_value = mock_result
        mock_checker_class.return_value = mock_checker

        fixture = DocumentationFixture(artifact_dir=tmp_path)
        fixture.setup()

        result = fixture.analyze(Path("./test"))

        assert result["passed"] is True
        assert result["score"] == 90.0
        assert result["grade"] == "A-"
        assert result["total_coverage"] == 92.0
        assert result["covered_count"] == 23
        assert result["missing_count"] == 2
        assert result["total_count"] == 25
        assert len(result["file_coverage"]) == 1
        assert result["execution_time"] == 0.75
        mock_checker.analyze.assert_called_once()

    def test_analyze_no_analyzer(self) -> None:
        """Test analysis when no analyzer is available."""
        fixture = DocumentationFixture()
        fixture._setup_complete = True  # Skip setup but analyzer is None
        result = fixture.analyze(Path("./test"))

        assert "error" in result
        assert result["error"] == "Analyzer not available"

    def test_check_with_thresholds(self) -> None:
        """Test check method with custom thresholds."""
        fixture = DocumentationFixture()

        with patch.object(fixture, "setup") as mock_setup, patch.object(fixture, "analyze") as mock_analyze:
            mock_analyze.return_value = {"passed": True, "score": 95.0}

            result = fixture.check(Path("./test"), min_coverage=95.0, min_grade="A", min_score=95.0)

            mock_setup.assert_called_once()
            assert fixture.config["min_coverage"] == 95.0
            assert fixture.config["min_grade"] == "A"
            assert fixture.config["min_score"] == 95.0
            assert result["passed"] is True

    def test_generate_report_no_analyzer(self) -> None:
        """Test report generation when no analyzer exists."""
        fixture = DocumentationFixture()
        report = fixture.generate_report()

        assert report == "No documentation analyzer available"

    def test_generate_report_no_results(self) -> None:
        """Test report generation when no results exist."""
        fixture = DocumentationFixture()
        fixture.analyzer = Mock()
        report = fixture.generate_report()

        assert report == "No documentation results available"

    @patch("provide.testkit.quality.documentation.fixture.INTERROGATE_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.documentation.fixture.DocumentationChecker")  # type: ignore[misc]
    def test_generate_report_success(self, mock_checker_class: Mock) -> None:
        """Test successful report generation."""
        mock_checker = Mock()
        mock_checker.report.return_value = "Documentation Coverage Report"
        mock_checker_class.return_value = mock_checker

        fixture = DocumentationFixture()
        fixture.setup()

        # Add a mock result
        mock_result = QualityResult(tool="documentation", passed=True)
        fixture.add_result(mock_result)

        report = fixture.generate_report("terminal")

        assert report == "Documentation Coverage Report"
        mock_checker.report.assert_called_once_with(mock_result, "terminal")


# 🧪✅🔚
