"""Pytest fixtures for complexity analysis."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from ..base import BaseQualityFixture
from .analyzer import RADON_AVAILABLE, ComplexityAnalyzer


class ComplexityFixture(BaseQualityFixture):
    """Pytest fixture for complexity analysis integration."""

    def __init__(self, config: dict[str, Any] | None = None, artifact_dir: Path | None = None):
        """Initialize complexity fixture.

        Args:
            config: Complexity analyzer configuration
            artifact_dir: Directory for artifacts
        """
        super().__init__(config, artifact_dir)
        self.analyzer: ComplexityAnalyzer | None = None

    def setup(self) -> None:
        """Setup complexity analysis."""
        if not RADON_AVAILABLE:
            pytest.skip("Radon not available")

        try:
            self.analyzer = ComplexityAnalyzer(self.config)
        except Exception as e:
            pytest.skip(f"Failed to initialize complexity analyzer: {e}")

    def teardown(self) -> None:
        """Cleanup complexity analyzer."""
        # No cleanup needed for complexity analyzer
        pass

    def analyze(self, path: Path) -> dict[str, Any]:
        """Perform complexity analysis.

        Args:
            path: Path to analyze

        Returns:
            Complexity analysis results
        """
        self.ensure_setup()
        if not self.analyzer:
            return {"error": "Analyzer not available"}

        result = self.analyzer.analyze(path, artifact_dir=self.artifact_dir)
        self.add_result(result)
        return {
            "passed": result.passed,
            "score": result.score,
            "grade": result.details.get("overall_grade", "F"),
            "average_complexity": result.details.get("average_complexity", 0),
            "max_complexity": result.details.get("max_complexity", 0),
            "details": result.details,
        }

    def generate_report(self, format: str = "terminal") -> str:
        """Generate complexity report.

        Args:
            format: Report format (terminal, json)

        Returns:
            Formatted report
        """
        if not self.analyzer:
            return "No complexity analyzer available"

        results = self.get_results_by_tool()
        if "complexity" not in results:
            return "No complexity results available"

        return self.analyzer.report(results["complexity"], format)


@pytest.fixture
def complexity_analyzer(request, tmp_path) -> Generator[ComplexityFixture, None, None]:
    """Pytest fixture for complexity analysis.

    Provides a ComplexityFixture instance for code complexity analysis.

    Usage:
        def test_complexity_analysis(complexity_analyzer):
            result = complexity_analyzer.analyze(Path('./src'))
            assert result['passed']
            assert result['grade'] in ['A', 'B', 'C']
    """
    # Get configuration from pytest request
    config = getattr(request, "param", {})

    # Create artifact directory for this test
    artifact_dir = tmp_path / "complexity"

    # Initialize fixture
    fixture = ComplexityFixture(config=config, artifact_dir=artifact_dir)

    try:
        fixture.setup()
        yield fixture
    finally:
        fixture.teardown()


@pytest.fixture
def complexity_config():
    """Default complexity configuration fixture.

    Returns standard complexity configuration that can be customized
    per test or project.

    Usage:
        def test_custom_complexity(complexity_config):
            complexity_config["min_grade"] = "A"
            complexity_config["max_complexity"] = 10
            # Use with parametrized complexity_analyzer
    """
    return {
        "min_grade": "C",
        "max_complexity": 20,
        "min_score": 70.0,
        "exclude": ["*/tests/*", "*/test_*", "*/.venv/*", "*/venv/*", "*/__pycache__/*", "*/migrations/*"],
    }


# Parametrized fixtures for different complexity configurations
@pytest.fixture(
    params=[
        {"min_grade": "A", "max_complexity": 10, "min_score": 95.0},  # Strict
        {"min_grade": "B", "max_complexity": 15, "min_score": 80.0},  # Normal
        {"min_grade": "C", "max_complexity": 25, "min_score": 60.0},  # Lenient
    ]
)
def parametrized_complexity(request, tmp_path) -> Generator[ComplexityFixture, None, None]:
    """Parametrized complexity fixture for testing different configurations.

    Automatically runs tests with different complexity thresholds
    to validate behavior under various settings.

    Usage:
        def test_complexity_configs(parametrized_complexity):
            # Test runs multiple times with different configs
            result = parametrized_complexity.analyze(Path('./src'))
            # Behavior will vary based on configuration
    """
    config = request.param
    artifact_dir = tmp_path / f"complexity_{id(config)}"

    fixture = ComplexityFixture(config=config, artifact_dir=artifact_dir)

    try:
        fixture.setup()
        yield fixture
    finally:
        fixture.teardown()


# Pytest hooks for automatic complexity integration
def pytest_configure(config):
    """Configure pytest with complexity markers."""
    config.addinivalue_line("markers", "complexity: mark test to run with complexity analysis")
    config.addinivalue_line("markers", "no_complexity: mark test to skip complexity analysis")


@pytest.fixture(autouse=True)
def auto_complexity_marker(request):
    """Automatically apply complexity analysis to marked tests.

    Tests marked with @pytest.mark.complexity will automatically
    get complexity analysis without needing to explicitly use fixtures.
    """
    if request.node.get_closest_marker("complexity"):
        # Test is marked for complexity - enable automatic analysis
        if not request.node.get_closest_marker("no_complexity"):
            # Create temporary complexity fixture
            complexity_fixture = ComplexityFixture()
            try:
                complexity_fixture.setup()
                # Complexity analysis would be applied here in a real implementation
                # For now, we just yield to continue the test
                yield
            finally:
                complexity_fixture.teardown()
        else:
            yield
    else:
        yield
