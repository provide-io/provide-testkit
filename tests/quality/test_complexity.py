#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for complexity analysis functionality."""

import json
from pathlib import Path

import pytest

from provide.testkit.mocking import Mock, patch  # type: ignore[import-untyped]
from provide.testkit.quality.base import QualityResult  # type: ignore[import-untyped]
from provide.testkit.quality.complexity.analyzer import (  # type: ignore[import-untyped]
    RADON_AVAILABLE,
    ComplexityAnalyzer,
)
from provide.testkit.quality.complexity.fixture import ComplexityFixture  # type: ignore[import-untyped]


@pytest.mark.skipif(not RADON_AVAILABLE, reason="radon not available")
class TestComplexityAnalyzer:
    """Test ComplexityAnalyzer functionality."""

    def test_initialization_default_config(self) -> None:
        """Test analyzer initialization with default config."""
        analyzer = ComplexityAnalyzer()
        assert analyzer.config == {}
        assert analyzer.artifact_dir is None

    def test_initialization_custom_config(self) -> None:
        """Test analyzer initialization with custom config."""
        config = {"min_grade": "A", "max_complexity": 10, "min_score": 95.0}
        analyzer = ComplexityAnalyzer(config)
        assert analyzer.config == config

    @patch("provide.testkit.quality.complexity.analyzer.cc_visit")  # type: ignore[misc]
    @patch("provide.testkit.quality.complexity.analyzer.cc_rank")  # type: ignore[misc]
    @patch("provide.testkit.quality.complexity.analyzer.analyze")  # type: ignore[misc]
    def test_analyze_success(
        self,
        mock_analyze: Mock,
        mock_cc_rank: Mock,
        mock_cc_visit: Mock,
        tmp_path: Path,
    ) -> None:
        """Test successful complexity analysis."""
        # Mock radon components
        mock_function = Mock()
        mock_function.name = "test_function"
        mock_function.complexity = 3
        mock_function.lineno = 10
        mock_cc_visit.return_value = [mock_function]
        mock_cc_rank.return_value = "A"

        mock_raw = Mock()
        mock_raw.loc = 50
        mock_raw.lloc = 30
        mock_raw.sloc = 25
        mock_raw.comments = 5
        mock_raw.multi = 2
        mock_raw.blank = 8
        mock_analyze.return_value = mock_raw

        analyzer = ComplexityAnalyzer({"min_grade": "C", "max_complexity": 20})

        # Create test Python file
        test_file = tmp_path / "test.py"
        test_file.write_text("def test_function():\n    return True")

        result = analyzer.analyze(test_file, artifact_dir=tmp_path / "artifacts")

        assert result.tool == "complexity"
        assert result.passed is True
        assert result.score == 100.0
        assert result.details["overall_grade"] == "A"
        assert result.details["total_functions"] == 1
        assert result.details["average_complexity"] == 3.0
        assert result.execution_time is not None

    @patch("provide.testkit.quality.complexity.analyzer.cc_visit")  # type: ignore[misc]
    @patch("provide.testkit.quality.complexity.analyzer.cc_rank")  # type: ignore[misc]
    def test_analyze_high_complexity(
        self,
        mock_cc_rank: Mock,
        mock_cc_visit: Mock,
        tmp_path: Path,
    ) -> None:
        """Test analysis with high complexity functions."""
        # Mock high complexity function
        mock_function = Mock()
        mock_function.name = "complex_function"
        mock_function.complexity = 25
        mock_function.lineno = 10
        mock_cc_visit.return_value = [mock_function]
        mock_cc_rank.return_value = "F"

        analyzer = ComplexityAnalyzer({"min_grade": "C", "max_complexity": 20})

        test_file = tmp_path / "test.py"
        test_file.write_text("def complex_function():\n    return True")

        result = analyzer.analyze(test_file, artifact_dir=tmp_path / "artifacts")

        assert result.tool == "complexity"
        assert result.passed is False  # Should fail due to max_complexity: 20 < 25
        assert result.score == 55.0  # D grade = 55% (complexity 25 is in 20-30 range)
        assert result.details["overall_grade"] == "D"
        assert result.details["max_complexity"] == 25

    def test_discover_python_files(self, tmp_path: Path) -> None:
        """Test Python file discovery."""
        analyzer = ComplexityAnalyzer()

        # Create test structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('main')")
        (tmp_path / "src" / "utils.py").write_text("print('utils')")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("print('test')")

        files = analyzer._discover_python_files(tmp_path)

        # Should include src files but exclude test files by default
        assert any("main.py" in str(f) for f in files)
        assert any("utils.py" in str(f) for f in files)
        assert not any("test_main.py" in str(f) for f in files)

    def test_discover_python_files_custom_excludes(self, tmp_path: Path) -> None:
        """Test Python file discovery with custom excludes."""
        config = {"exclude": ["*/private/*"]}
        analyzer = ComplexityAnalyzer(config)

        # Create test structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('main')")
        (tmp_path / "private").mkdir()
        (tmp_path / "private" / "secret.py").write_text("print('secret')")

        files = analyzer._discover_python_files(tmp_path)

        assert any("main.py" in str(f) for f in files)
        assert not any("secret.py" in str(f) for f in files)

    def test_grade_calculation(self) -> None:
        """Test complexity grade calculation."""
        analyzer = ComplexityAnalyzer()

        # Test grade boundaries
        test_cases = [
            (3, "A", 100.0),  # avg_complexity <= 5
            (8, "B", 85.0),  # avg_complexity <= 10
            (15, "C", 70.0),  # avg_complexity <= 20
            (25, "D", 55.0),  # avg_complexity <= 30
            (40, "F", 40.0),  # avg_complexity > 30
        ]

        for avg_complexity, expected_grade, expected_score in test_cases:
            # Mock data for testing
            result = analyzer._process_complexity_results(
                [{"complexity": avg_complexity, "rank": expected_grade}],
                [{"loc": 100, "lloc": 80, "comments": 10}],
                [],
            )
            assert result.details["overall_grade"] == expected_grade
            assert result.score == expected_score

    def test_generate_text_report(self) -> None:
        """Test text report generation."""
        analyzer = ComplexityAnalyzer()

        result = QualityResult(
            tool="complexity",
            passed=True,
            score=85.0,
            details={
                "total_files": 5,
                "total_functions": 20,
                "average_complexity": 7.5,
                "max_complexity": 15,
                "overall_grade": "B",
                "grade_breakdown": {"A": 15, "B": 4, "C": 1, "D": 0, "E": 0, "F": 0},
                "lines_of_code": 500,
                "logical_lines": 350,
                "comment_lines": 50,
            },
        )

        report = analyzer._generate_text_report(result)

        assert "Complexity Analysis Report" in report
        assert "85.0%" in report
        assert "Overall Grade: B" in report
        assert "Files Analyzed: 5" in report
        assert "Average Complexity: 7.5" in report
        assert "A: 15 functions" in report

    def test_report_protocol_implementation(self) -> None:
        """Test QualityTool protocol implementation."""
        analyzer = ComplexityAnalyzer()

        result = QualityResult(
            tool="complexity",
            passed=False,
            score=55.0,
            details={"overall_grade": "D", "total_functions": 10, "average_complexity": 25.0},
        )

        report = analyzer.report(result, "terminal")
        assert "Complexity Analysis Report" in report
        assert "❌ FAILED" in report
        assert "55.0%" in report
        assert "Overall Grade: D" in report

        json_report = analyzer.report(result, "json")
        data = json.loads(json_report)
        assert data["tool"] == "complexity"
        assert data["passed"] is False
        assert data["score"] == 55.0


class TestComplexityFixture:
    """Test ComplexityFixture functionality."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test fixture initialization."""
        config = {"min_grade": "A"}
        fixture = ComplexityFixture(config=config, artifact_dir=tmp_path)

        assert fixture.config == config
        assert fixture.artifact_dir == tmp_path
        assert fixture.analyzer is None

    @patch("provide.testkit.quality.complexity.fixture.RADON_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.complexity.fixture.ComplexityAnalyzer")  # type: ignore[misc]
    def test_setup_success(self, mock_analyzer_class: Mock) -> None:
        """Test successful fixture setup."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        fixture = ComplexityFixture()
        fixture.setup()

        assert fixture.analyzer == mock_analyzer
        mock_analyzer_class.assert_called_once_with({})

    @patch("provide.testkit.quality.complexity.fixture.RADON_AVAILABLE", False)  # type: ignore[misc]
    def test_setup_radon_unavailable(self) -> None:
        """Test setup when radon is unavailable."""
        fixture = ComplexityFixture()

        with pytest.raises(pytest.skip.Exception):
            fixture.setup()

    @patch("provide.testkit.quality.complexity.fixture.RADON_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.complexity.fixture.ComplexityAnalyzer")  # type: ignore[misc]
    def test_analyze_functionality(self, mock_analyzer_class: Mock, tmp_path: Path) -> None:
        """Test analysis functionality."""
        mock_analyzer = Mock()
        mock_result = QualityResult(
            tool="complexity",
            passed=True,
            score=85.0,
            details={"overall_grade": "B", "average_complexity": 7.5, "max_complexity": 12},
        )
        mock_analyzer.analyze.return_value = mock_result
        mock_analyzer_class.return_value = mock_analyzer

        fixture = ComplexityFixture(artifact_dir=tmp_path)
        fixture.setup()

        result = fixture.analyze(Path("./test"))

        assert result["passed"] is True
        assert result["score"] == 85.0
        assert result["grade"] == "B"
        assert result["average_complexity"] == 7.5
        assert result["max_complexity"] == 12
        mock_analyzer.analyze.assert_called_once()

    def test_analyze_no_analyzer(self) -> None:
        """Test analysis when no analyzer is available."""
        fixture = ComplexityFixture()
        fixture._setup_complete = True  # Skip setup but analyzer is None
        result = fixture.analyze(Path("./test"))

        assert "error" in result
        assert result["error"] == "Analyzer not available"

    def test_generate_report_no_analyzer(self) -> None:
        """Test report generation when no analyzer exists."""
        fixture = ComplexityFixture()
        report = fixture.generate_report()

        assert report == "No complexity analyzer available"

    @patch("provide.testkit.quality.complexity.fixture.RADON_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.complexity.fixture.ComplexityAnalyzer")  # type: ignore[misc]
    def test_generate_report_success(self, mock_analyzer_class: Mock) -> None:
        """Test successful report generation."""
        mock_analyzer = Mock()
        mock_analyzer.report.return_value = "Complexity Report"
        mock_analyzer_class.return_value = mock_analyzer

        fixture = ComplexityFixture()
        fixture.setup()

        # Add a mock result
        mock_result = QualityResult(tool="complexity", passed=True)
        fixture.add_result(mock_result)

        report = fixture.generate_report("terminal")

        assert report == "Complexity Report"
        mock_analyzer.report.assert_called_once_with(mock_result, "terminal")


# Integration tests would go here if we had actual radon
# For now, we'll test the mocked behavior


@pytest.mark.integration
@pytest.mark.skipif(not RADON_AVAILABLE, reason="radon not available")
def test_real_complexity_integration(tmp_path: Path) -> None:
    """Integration test with real radon (if available)."""
    # Create Python files with varying complexity
    simple_file = tmp_path / "simple.py"
    simple_file.write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
""")

    complex_file = tmp_path / "complex.py"
    complex_file.write_text("""
def complex_function(data):
    result = []
    for item in data:
        if item is None:
            continue
        elif isinstance(item, str):
            if item.startswith('prefix'):
                result.append(item.upper())
            elif item.endswith('suffix'):
                result.append(item.lower())
            else:
                result.append(item.title())
        elif isinstance(item, int):
            if item > 0:
                if item % 2 == 0:
                    result.append(item * 2)
                else:
                    result.append(item * 3)
            else:
                result.append(0)
        else:
            result.append(str(item))
    return result
""")

    # Create complexity analyzer
    config = {"min_grade": "B", "max_complexity": 15, "min_score": 80.0}

    analyzer = ComplexityAnalyzer(config)
    analyzer.artifact_dir = tmp_path / "artifacts"

    # Run complexity analysis
    result = analyzer.analyze(tmp_path)

    # Should find functions with varying complexity
    assert result.tool == "complexity"
    assert result.details["total_functions"] >= 3
    assert result.details["average_complexity"] > 0
    assert "grade_breakdown" in result.details

    # Generate reports
    terminal_report = analyzer.report(result, "terminal")
    assert "Complexity Analysis Report" in terminal_report

    json_report = analyzer.report(result, "json")
    data = json.loads(json_report)
    assert data["tool"] == "complexity"


# 🧪✅🔚
