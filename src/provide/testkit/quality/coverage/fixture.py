"""Pytest fixtures for coverage tracking."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from ..base import BaseQualityFixture
from .tracker import COVERAGE_AVAILABLE, CoverageTracker


class CoverageFixture(BaseQualityFixture):
    """Pytest fixture for coverage tracking integration."""

    def __init__(self, config: dict[str, Any] | None = None, artifact_dir: Path | None = None):
        """Initialize coverage fixture.

        Args:
            config: Coverage configuration
            artifact_dir: Directory for artifacts
        """
        super().__init__(config, artifact_dir)
        self.tracker: CoverageTracker | None = None

    def setup(self) -> None:
        """Setup coverage tracking."""
        if not COVERAGE_AVAILABLE:
            pytest.skip("Coverage.py not available")

        try:
            self.tracker = CoverageTracker(self.config)
        except Exception as e:
            pytest.skip(f"Failed to initialize coverage: {e}")

    def teardown(self) -> None:
        """Stop coverage and generate reports."""
        if self.tracker and self.tracker.is_running:
            self.tracker.stop()

    def start_tracking(self) -> None:
        """Start coverage tracking."""
        self.ensure_setup()
        if self.tracker:
            self.tracker.start()

    def stop_tracking(self) -> None:
        """Stop coverage tracking."""
        if self.tracker:
            self.tracker.stop()

    def get_coverage(self) -> float:
        """Get current coverage percentage."""
        if not self.tracker:
            return 0.0
        return self.tracker.get_coverage()

    def generate_report(self, format: str = "terminal") -> str:
        """Generate coverage report."""
        if not self.tracker:
            return "No coverage data"
        return self.tracker.generate_report(format)


@pytest.fixture
def coverage_tracker(request, tmp_path) -> Generator[CoverageFixture, None, None]:
    """Pytest fixture for coverage tracking.

    Provides a CoverageFixture instance that automatically starts and stops
    coverage tracking around individual tests.

    Usage:
        def test_with_coverage(coverage_tracker):
            coverage_tracker.start_tracking()
            # ... test code
            coverage_tracker.stop_tracking()
            assert coverage_tracker.get_coverage() > 80
    """
    # Get configuration from pytest request
    config = getattr(request, "param", {})

    # Create artifact directory for this test
    artifact_dir = tmp_path / "coverage"

    # Initialize fixture
    fixture = CoverageFixture(config=config, artifact_dir=artifact_dir)

    try:
        fixture.setup()
        yield fixture
    finally:
        fixture.teardown()


@pytest.fixture
def auto_coverage(coverage_tracker) -> Generator[CoverageFixture, None, None]:
    """Automatic coverage tracking fixture.

    Automatically starts coverage at the beginning of the test and stops
    at the end. Ideal for tests that want zero-configuration coverage.

    Usage:
        def test_automatic_coverage(auto_coverage):
            # Coverage automatically tracked
            result = some_function()
            assert result is not None
            # Coverage automatically stopped and saved
    """
    coverage_tracker.start_tracking()
    try:
        yield coverage_tracker
    finally:
        coverage_tracker.stop_tracking()


@pytest.fixture(scope="session")
def session_coverage(tmp_path_factory) -> Generator[CoverageFixture, None, None]:
    """Session-wide coverage tracking.

    Tracks coverage across all tests in the session. Useful for getting
    overall coverage metrics for the entire test suite.

    Usage:
        def test_part_one(session_coverage):
            # Coverage tracked across all tests
            pass

        def test_part_two(session_coverage):
            # Same coverage instance
            pass
    """
    # Create session-wide artifact directory
    artifact_dir = tmp_path_factory.mktemp("session_coverage")

    # Initialize session fixture
    fixture = CoverageFixture(artifact_dir=artifact_dir)

    try:
        fixture.setup()
        fixture.start_tracking()
        yield fixture
    finally:
        fixture.stop_tracking()
        fixture.teardown()


@pytest.fixture
def coverage_config():
    """Default coverage configuration fixture.

    Returns standard coverage configuration that can be customized
    per test or project.

    Usage:
        def test_with_custom_coverage(coverage_config):
            coverage_config["fail_under"] = 95
            # Use with parametrized coverage_tracker
    """
    return {
        "branch": True,
        "source": ["src"],
        "omit": [
            "*/tests/*",
            "*/test_*",
            "*/.venv/*",
            "*/venv/*",
        ],
        "fail_under": 80,
        "show_missing": True,
        "skip_covered": False,
    }


# Parametrized fixtures for different coverage configurations
@pytest.fixture(
    params=[
        {"fail_under": 80, "branch": True},
        {"fail_under": 90, "branch": False},
        {"fail_under": 95, "branch": True, "show_missing": True},
    ]
)
def parametrized_coverage(request, tmp_path) -> Generator[CoverageFixture, None, None]:
    """Parametrized coverage fixture for testing different configurations.

    Automatically runs tests with different coverage configurations
    to validate behavior under various settings.

    Usage:
        def test_coverage_configs(parametrized_coverage):
            # Test runs multiple times with different configs
            pass
    """
    config = request.param
    artifact_dir = tmp_path / f"coverage_{id(config)}"

    fixture = CoverageFixture(config=config, artifact_dir=artifact_dir)

    try:
        fixture.setup()
        yield fixture
    finally:
        fixture.teardown()


# Pytest hooks for automatic coverage integration
def pytest_configure(config):
    """Configure pytest with coverage markers."""
    config.addinivalue_line("markers", "coverage: mark test to run with coverage tracking")
    config.addinivalue_line("markers", "no_coverage: mark test to skip coverage tracking")


@pytest.fixture(autouse=True)
def auto_coverage_marker(request):
    """Automatically apply coverage to marked tests.

    Tests marked with @pytest.mark.coverage will automatically
    get coverage tracking without needing to explicitly use fixtures.
    """
    if request.node.get_closest_marker("coverage"):
        # Test is marked for coverage - enable automatic tracking
        if not request.node.get_closest_marker("no_coverage"):
            # Create temporary coverage fixture
            coverage_fixture = CoverageFixture()
            try:
                coverage_fixture.setup()
                coverage_fixture.start_tracking()
                yield
            finally:
                coverage_fixture.stop_tracking()
                coverage_fixture.teardown()
        else:
            yield
    else:
        yield
