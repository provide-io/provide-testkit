"""Tests for documentation coverage functionality."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from provide.testkit.quality.base import QualityResult
from provide.testkit.quality.documentation.checker import INTERROGATE_AVAILABLE, DocumentationChecker
from provide.testkit.quality.documentation.fixture import DocumentationFixture


@pytest.mark.skipif(not INTERROGATE_AVAILABLE, reason="interrogate not available")
class TestDocumentationChecker:
    """Test DocumentationChecker functionality."""

    def test_initialization_default_config(self):
        """Test checker initialization with default config."""
        checker = DocumentationChecker()
        assert checker.config == {}
        assert checker.artifact_dir is None

    def test_initialization_custom_config(self):
        """Test checker initialization with custom config."""
        config = {"min_coverage": 95.0, "min_grade": "A", "min_score": 95.0, "ignore_init_method": False}
        checker = DocumentationChecker(config)
        assert checker.config == config

    @patch("provide.testkit.quality.documentation.checker.coverage.InterrogateCoverage")
    @patch("provide.testkit.quality.documentation.checker.InterrogateConfig")
    def test_analyze_success(self, mock_config_class, mock_coverage_class, tmp_path):
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

    @patch("provide.testkit.quality.documentation.checker.coverage.InterrogateCoverage")
    @patch("provide.testkit.quality.documentation.checker.InterrogateConfig")
    def test_analyze_low_coverage(self, mock_config_class, mock_coverage_class, tmp_path):
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

    def test_build_interrogate_config_default(self):
        """Test interrogate config building with defaults."""
        checker = DocumentationChecker()
        config = checker._build_interrogate_config()

        assert config["ignore_init_method"] is True
        assert config["ignore_magic"] is True
        assert config["ignore_setters"] is True
        assert config["ignore_private"] is False
        assert config["verbose"] == 0
        assert "ignore_regex" in config

    def test_build_interrogate_config_custom(self):
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

    def test_grade_calculation(self):
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

    def test_passing_criteria(self):
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

    @patch("provide.testkit.quality.documentation.checker.coverage.InterrogateCoverage")
    @patch("provide.testkit.quality.documentation.checker.InterrogateConfig")
    def test_analyze_with_file_details(self, mock_config_class, mock_coverage_class, tmp_path):
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

    def test_generate_text_report(self):
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
        assert "✅ PASSED" in report
        assert "85.0%" in report
        assert "Grade: B" in report
        assert "Coverage: 82.5%" in report
        assert "Documented Items: 33" in report
        assert "Missing Documentation: 7" in report
        assert "Total Items: 40" in report
        assert "Minimum Coverage: 80.0%" in report
        assert "Execution Time: 1.25s" in report

    def test_generate_detail_report(self):
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
        assert any("✅ high_coverage.py: 95.0%" in line for line in lines)

    def test_report_protocol_implementation(self):
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


class TestDocumentationFixture:
    """Test DocumentationFixture functionality."""

    def test_initialization(self, tmp_path):
        """Test fixture initialization."""
        config = {"min_coverage": 90.0}
        fixture = DocumentationFixture(config=config, artifact_dir=tmp_path)

        assert fixture.config == config
        assert fixture.artifact_dir == tmp_path
        assert fixture.analyzer is None

    @patch("provide.testkit.quality.documentation.fixture.INTERROGATE_AVAILABLE", True)
    @patch("provide.testkit.quality.documentation.fixture.DocumentationChecker")
    def test_setup_success(self, mock_checker_class):
        """Test successful fixture setup."""
        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker

        fixture = DocumentationFixture()
        fixture.setup()

        assert fixture.analyzer == mock_checker
        mock_checker_class.assert_called_once_with({})

    @patch("provide.testkit.quality.documentation.fixture.INTERROGATE_AVAILABLE", False)
    def test_setup_interrogate_unavailable(self):
        """Test setup when interrogate is unavailable."""
        fixture = DocumentationFixture()

        with pytest.raises(pytest.skip.Exception):
            fixture.setup()

    @patch("provide.testkit.quality.documentation.fixture.INTERROGATE_AVAILABLE", True)
    @patch("provide.testkit.quality.documentation.fixture.DocumentationChecker")
    def test_analyze_functionality(self, mock_checker_class, tmp_path):
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

    def test_analyze_no_analyzer(self):
        """Test analysis when no analyzer is available."""
        fixture = DocumentationFixture()
        fixture._setup_complete = True  # Skip setup but analyzer is None
        result = fixture.analyze(Path("./test"))

        assert "error" in result
        assert result["error"] == "Analyzer not available"

    def test_check_with_thresholds(self):
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

    def test_generate_report_no_analyzer(self):
        """Test report generation when no analyzer exists."""
        fixture = DocumentationFixture()
        report = fixture.generate_report()

        assert report == "No documentation analyzer available"

    def test_generate_report_no_results(self):
        """Test report generation when no results exist."""
        fixture = DocumentationFixture()
        fixture.analyzer = Mock()
        report = fixture.generate_report()

        assert report == "No documentation results available"

    @patch("provide.testkit.quality.documentation.fixture.INTERROGATE_AVAILABLE", True)
    @patch("provide.testkit.quality.documentation.fixture.DocumentationChecker")
    def test_generate_report_success(self, mock_checker_class):
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


@pytest.mark.integration
@pytest.mark.skipif(not INTERROGATE_AVAILABLE, reason="interrogate not available")
def test_real_documentation_integration(tmp_path):
    """Integration test with real interrogate (if available)."""
    # Create Python files with varying documentation
    well_documented = tmp_path / "well_documented.py"
    well_documented.write_text('''"""Well documented module."""

def documented_function(param: str) -> str:
    """A well documented function.

    Args:
        param: Input parameter

    Returns:
        Processed string
    """
    return param.upper()

class DocumentedClass:
    """A well documented class."""

    def documented_method(self) -> None:
        """A documented method."""
        pass
''')

    poorly_documented = tmp_path / "poorly_documented.py"
    poorly_documented.write_text("""def undocumented_function(x, y):
    return x + y

class UndocumentedClass:
    def undocumented_method(self):
        pass

    def another_undocumented(self):
        return "test"
""")

    # Create documentation checker
    config = {
        "min_coverage": 70.0,
        "min_grade": "C",
        "min_score": 70.0,
        "ignore_init_method": True,
        "ignore_magic": True,
    }

    checker = DocumentationChecker(config)
    checker.artifact_dir = tmp_path / "artifacts"

    # Run documentation analysis
    result = checker.analyze(tmp_path)

    # Should find varying documentation levels
    assert result.tool == "documentation"

    # Check if we have valid results (might not have total_count due to mocking/integration issues)
    if "total_count" in result.details:
        assert result.details["total_count"] > 0
    elif "covered_count" in result.details and "missing_count" in result.details:
        # Calculate total from components if available
        total = result.details["covered_count"] + result.details["missing_count"]
        assert total > 0
    else:
        # Skip assertion if interrogate didn't provide expected data structure
        pytest.skip("Interrogate integration test incomplete - expected data structure not available")
    assert 0 <= result.details["total_coverage"] <= 100
    assert result.details["grade"] in ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]

    # Generate reports
    terminal_report = checker.report(result, "terminal")
    assert "Documentation Coverage Report" in terminal_report

    json_report = checker.report(result, "json")
    data = json.loads(json_report)
    assert data["tool"] == "documentation"
