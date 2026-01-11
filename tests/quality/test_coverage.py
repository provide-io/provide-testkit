#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for coverage tracking functionality."""

from pathlib import Path

import pytest

from provide.testkit.mocking import Mock, patch  # type: ignore[import-untyped]
from provide.testkit.quality.base import QualityResult  # type: ignore[import-untyped]
from provide.testkit.quality.coverage.fixture import CoverageFixture  # type: ignore[import-untyped]
from provide.testkit.quality.coverage.tracker import (  # type: ignore[import-untyped]
    COVERAGE_AVAILABLE,
    CoverageTracker,
)


@pytest.mark.skipif(not COVERAGE_AVAILABLE, reason="coverage.py not available")
class TestCoverageTracker:
    """Test CoverageTracker functionality."""

    def test_initialization_default_config(self) -> None:
        """Test tracker initialization with default config."""
        tracker = CoverageTracker()
        assert tracker.config == {}
        assert tracker.coverage is None
        assert tracker.is_running is False

    def test_initialization_custom_config(self) -> None:
        """Test tracker initialization with custom config."""
        config = {"branch": False, "source": ["mycode"]}
        tracker = CoverageTracker(config)
        assert tracker.config == config

    @patch("provide.testkit.quality.coverage.tracker.Coverage")  # type: ignore[misc]
    def test_start_stop_tracking(self, mock_coverage_class: Mock) -> None:
        """Test starting and stopping coverage tracking."""
        mock_coverage = Mock()
        mock_coverage_class.return_value = mock_coverage

        tracker = CoverageTracker()

        # Test start
        tracker.start()
        assert tracker.is_running is True
        assert tracker.coverage == mock_coverage
        mock_coverage.start.assert_called_once()

        # Test stop
        tracker.stop()
        assert tracker.is_running is False
        mock_coverage.stop.assert_called_once()
        mock_coverage.save.assert_called_once()

    @patch("provide.testkit.quality.coverage.tracker.Coverage")  # type: ignore[misc]
    def test_start_when_already_running(self, mock_coverage_class: Mock) -> None:
        """Test starting coverage when already running."""
        mock_coverage = Mock()
        mock_coverage_class.return_value = mock_coverage

        tracker = CoverageTracker()
        tracker.start()
        tracker.start()  # Second start should be ignored

        # Should only be called once
        mock_coverage.start.assert_called_once()

    @patch("provide.testkit.quality.coverage.tracker.Coverage")  # type: ignore[misc]
    def test_get_coverage_percentage(self, mock_coverage_class: Mock) -> None:
        """Test getting coverage percentage."""
        mock_coverage = Mock()
        mock_coverage.report.return_value = 85.7
        mock_coverage_class.return_value = mock_coverage

        tracker = CoverageTracker()
        tracker.start()

        coverage_percent = tracker.get_coverage()
        assert coverage_percent == 85.7

    @patch("provide.testkit.quality.coverage.tracker.Coverage")  # type: ignore[misc]
    def test_get_coverage_no_instance(self, mock_coverage_class: Mock) -> None:
        """Test getting coverage when no instance exists."""
        tracker = CoverageTracker()
        coverage_percent = tracker.get_coverage()
        assert coverage_percent == 0.0

    @patch("provide.testkit.quality.coverage.tracker.Coverage")  # type: ignore[misc]
    def test_analyze_success(self, mock_coverage_class: Mock, tmp_path: Path) -> None:
        """Test successful coverage analysis."""
        mock_coverage = Mock()
        mock_coverage.report.return_value = 92.5

        # Mock coverage data properly
        mock_data = Mock()
        mock_data.measured_files.return_value = []
        mock_coverage.get_data.return_value = mock_data
        mock_coverage_class.return_value = mock_coverage

        tracker = CoverageTracker({"fail_under": 90})

        result = tracker.analyze(tmp_path / "src", artifact_dir=tmp_path / "artifacts")

        assert result.tool == "coverage"
        assert result.passed is True
        assert result.score == 92.5
        assert result.execution_time is not None
        assert "threshold" in result.details

    @patch("provide.testkit.quality.coverage.tracker.Coverage")  # type: ignore[misc]
    def test_analyze_below_threshold(self, mock_coverage_class: Mock, tmp_path: Path) -> None:
        """Test analysis when coverage is below threshold."""
        mock_coverage = Mock()
        mock_coverage.report.return_value = 75.0

        # Mock coverage data properly
        mock_data = Mock()
        mock_data.measured_files.return_value = []
        mock_coverage.get_data.return_value = mock_data
        mock_coverage_class.return_value = mock_coverage

        tracker = CoverageTracker({"fail_under": 80})

        result = tracker.analyze(tmp_path / "src", artifact_dir=tmp_path / "artifacts")

        assert result.tool == "coverage"
        assert result.passed is False  # Below threshold
        assert result.score == 75.0

    @patch("provide.testkit.quality.coverage.tracker.Coverage")  # type: ignore[misc]
    def test_build_coverage_config(self, mock_coverage_class: Mock) -> None:
        """Test building coverage.py configuration."""
        config = {"branch": False, "source": ["myapp"], "omit": ["*/tests/*"], "fail_under": 95}
        tracker = CoverageTracker(config)

        built_config = tracker._build_coverage_config()

        assert built_config["branch"] is False
        assert built_config["source"] == ["myapp"]
        assert built_config["omit"] == ["*/tests/*"]
        # fail_under is not passed to coverage.py
        assert "fail_under" not in built_config

    @patch("provide.testkit.quality.coverage.tracker.Coverage")  # type: ignore[misc]
    def test_generate_html_report(self, mock_coverage_class: Mock, tmp_path: Path) -> None:
        """Test HTML report generation."""
        mock_coverage = Mock()
        mock_coverage_class.return_value = mock_coverage

        tracker = CoverageTracker()
        tracker.coverage = mock_coverage
        tracker.artifact_dir = tmp_path

        result = tracker.generate_report("html")

        mock_coverage.html_report.assert_called_once()
        assert "htmlcov" in result

    @patch("provide.testkit.quality.coverage.tracker.Coverage")  # type: ignore[misc]
    def test_generate_xml_report(self, mock_coverage_class: Mock, tmp_path: Path) -> None:
        """Test XML report generation."""
        mock_coverage = Mock()
        mock_coverage_class.return_value = mock_coverage

        tracker = CoverageTracker()
        tracker.coverage = mock_coverage
        tracker.artifact_dir = tmp_path

        result = tracker.generate_report("xml")

        mock_coverage.xml_report.assert_called_once()
        assert "coverage.xml" in result

    @patch("provide.testkit.quality.coverage.tracker.Coverage")  # type: ignore[misc]
    def test_report_protocol_implementation(self, mock_coverage_class: Mock) -> None:
        """Test QualityTool protocol implementation."""
        mock_coverage = Mock()
        mock_coverage_class.return_value = mock_coverage

        tracker = CoverageTracker()

        result = QualityResult(
            tool="coverage",
            passed=True,
            score=85.5,
            details={"total_statements": 100, "missing_statements": 15},
        )

        report = tracker.report(result, "terminal")

        assert "Coverage Report" in report
        assert "85.5%" in report
        assert "Total Statements: 100" in report


class TestCoverageFixture:
    """Test CoverageFixture functionality."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test fixture initialization."""
        config = {"branch": False}
        fixture = CoverageFixture(config=config, artifact_dir=tmp_path)

        assert fixture.config == config
        assert fixture.artifact_dir == tmp_path
        assert fixture.tracker is None

    @patch("provide.testkit.quality.coverage.fixture.COVERAGE_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.coverage.fixture.CoverageTracker")  # type: ignore[misc]
    def test_setup_success(self, mock_tracker_class: Mock) -> None:
        """Test successful fixture setup."""
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker

        fixture = CoverageFixture()
        fixture.setup()

        assert fixture.tracker == mock_tracker
        mock_tracker_class.assert_called_once_with({})

    @patch("provide.testkit.quality.coverage.fixture.COVERAGE_AVAILABLE", False)  # type: ignore[misc]
    def test_setup_coverage_unavailable(self) -> None:
        """Test setup when coverage is unavailable."""
        fixture = CoverageFixture()

        with pytest.raises(pytest.skip.Exception):
            fixture.setup()

    @patch("provide.testkit.quality.coverage.fixture.COVERAGE_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.coverage.fixture.CoverageTracker")  # type: ignore[misc]
    def test_start_stop_tracking(self, mock_tracker_class: Mock) -> None:
        """Test starting and stopping tracking."""
        mock_tracker = Mock()
        mock_tracker.is_running = False
        mock_tracker_class.return_value = mock_tracker

        fixture = CoverageFixture()
        fixture.setup()

        # Test start
        fixture.start_tracking()
        mock_tracker.start.assert_called_once()

        # Test stop
        mock_tracker.is_running = True
        fixture.stop_tracking()
        mock_tracker.stop.assert_called_once()

    @patch("provide.testkit.quality.coverage.fixture.COVERAGE_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.coverage.fixture.CoverageTracker")  # type: ignore[misc]
    def test_get_coverage(self, mock_tracker_class: Mock) -> None:
        """Test getting coverage percentage."""
        mock_tracker = Mock()
        mock_tracker.get_coverage.return_value = 87.3
        mock_tracker_class.return_value = mock_tracker

        fixture = CoverageFixture()
        fixture.setup()

        coverage = fixture.get_coverage()
        assert coverage == 87.3

    def test_get_coverage_no_tracker(self) -> None:
        """Test getting coverage when no tracker exists."""
        fixture = CoverageFixture()
        coverage = fixture.get_coverage()
        assert coverage == 0.0

    @patch("provide.testkit.quality.coverage.fixture.COVERAGE_AVAILABLE", True)  # type: ignore[misc]
    @patch("provide.testkit.quality.coverage.fixture.CoverageTracker")  # type: ignore[misc]
    def test_teardown_with_running_tracker(self, mock_tracker_class: Mock) -> None:
        """Test teardown when tracker is running."""
        mock_tracker = Mock()
        mock_tracker.is_running = True
        mock_tracker_class.return_value = mock_tracker

        fixture = CoverageFixture()
        fixture.setup()
        fixture.teardown()

        mock_tracker.stop.assert_called_once()


# Integration tests would go here if we had actual coverage.py
# For now, we'll test the mocked behavior


@pytest.mark.integration
@pytest.mark.skipif(not COVERAGE_AVAILABLE, reason="coverage.py not available")
def test_real_coverage_integration(tmp_path: Path) -> None:
    """Integration test with real coverage.py (if available)."""
    # Create a simple Python file to track coverage for
    test_file = tmp_path / "test_module.py"
    test_file.write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    if a > b:
        return a - b
    else:
        return b - a

def multiply(a, b):
    return a * b
""")

    # Create coverage tracker
    config = {"source": [str(tmp_path)], "omit": [], "branch": True}

    tracker = CoverageTracker(config)
    tracker.artifact_dir = tmp_path / "artifacts"

    # Start coverage
    tracker.start()

    # Import and use the module (this would normally be done by tests)
    import sys

    sys.path.insert(0, str(tmp_path))

    try:
        import test_module  # type: ignore[import-not-found]

        # Call some functions (simulating test execution)
        result1 = test_module.add(2, 3)
        result2 = test_module.subtract(5, 3)
        # Note: multiply is not called, so coverage should be partial

        assert result1 == 5
        assert result2 == 2

    finally:
        sys.path.remove(str(tmp_path))

    # Stop coverage and analyze
    tracker.stop()

    # Get coverage percentage
    coverage_percent = tracker.get_coverage()

    # Should have partial coverage (not 100% since multiply wasn't called)
    assert 0 < coverage_percent < 100

    # Generate reports
    terminal_report = tracker.generate_report("terminal")
    assert "test_module.py" in terminal_report

    html_report = tracker.generate_report("html")
    assert "htmlcov" in html_report


# 🧪✅🔚
