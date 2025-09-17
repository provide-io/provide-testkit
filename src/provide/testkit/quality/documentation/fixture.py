"""Documentation coverage fixture for pytest integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ..base import BaseQualityFixture

try:
    from .checker import INTERROGATE_AVAILABLE, DocumentationChecker
except ImportError:
    DocumentationChecker = None
    INTERROGATE_AVAILABLE = False


class DocumentationFixture(BaseQualityFixture):
    """Pytest fixture for documentation coverage analysis.

    Provides easy access to documentation coverage checking with automatic
    setup and teardown. Integrates with the quality framework fixtures.
    """

    def __init__(self, config: dict[str, Any] | None = None, artifact_dir: Path | None = None):
        """Initialize documentation fixture.

        Args:
            config: Documentation checker configuration
            artifact_dir: Directory for artifacts
        """
        super().__init__(config or {}, artifact_dir)
        self.analyzer: DocumentationChecker | None = None

    def setup(self) -> None:
        """Set up documentation analyzer."""
        if not INTERROGATE_AVAILABLE:
            pytest.skip("interrogate not available")

        self.analyzer = DocumentationChecker(self.config)
        self._setup_complete = True

    def teardown(self) -> None:
        """Clean up documentation analyzer."""
        self.analyzer = None
        self._setup_complete = False

    def analyze(self, path: Path) -> dict[str, Any]:
        """Run documentation coverage analysis.

        Args:
            path: Path to analyze

        Returns:
            Analysis results as dict
        """
        if not self.analyzer:
            return {"error": "Analyzer not available"}

        result = self.analyzer.analyze(path, artifact_dir=self.artifact_dir)
        self.add_result(result)

        return {
            "passed": result.passed,
            "score": result.score,
            "grade": result.details.get("grade"),
            "total_coverage": result.details.get("total_coverage"),
            "covered_count": result.details.get("covered_count"),
            "missing_count": result.details.get("missing_count"),
            "total_count": result.details.get("total_count"),
            "file_coverage": result.details.get("file_coverage", []),
            "thresholds": result.details.get("thresholds", {}),
            "execution_time": result.execution_time,
        }

    def check(
        self,
        path: Path,
        min_coverage: float | None = None,
        min_grade: str | None = None,
        min_score: float | None = None,
    ) -> dict[str, Any]:
        """Check documentation coverage with optional thresholds.

        Args:
            path: Path to check
            min_coverage: Minimum coverage percentage required
            min_grade: Minimum grade required (A, B, C, D, F)
            min_score: Minimum score required

        Returns:
            Check results including pass/fail status
        """
        if not self._setup_complete:
            self.setup()

        # Update config with provided thresholds
        if min_coverage is not None:
            self.config["min_coverage"] = min_coverage
        if min_grade is not None:
            self.config["min_grade"] = min_grade
        if min_score is not None:
            self.config["min_score"] = min_score

        # Recreate analyzer with updated config
        if self.analyzer and any(x is not None for x in [min_coverage, min_grade, min_score]):
            self.analyzer = DocumentationChecker(self.config)

        return self.analyze(path)

    def generate_report(self, format: str = "terminal") -> str:
        """Generate documentation report.

        Args:
            format: Report format (terminal, json)

        Returns:
            Formatted report
        """
        if not self.analyzer:
            return "No documentation analyzer available"

        if not self.results:
            return "No documentation results available"

        # Use the most recent result
        latest_result = self.results[-1]
        return self.analyzer.report(latest_result, format)


@pytest.fixture
def documentation_checker() -> DocumentationFixture:
    """Provide documentation coverage checker fixture.

    Returns:
        DocumentationFixture instance
    """
    fixture = DocumentationFixture()
    fixture.setup()
    yield fixture
    fixture.teardown()


@pytest.fixture
def documentation_config() -> dict[str, Any]:
    """Provide default documentation configuration.

    Returns:
        Default configuration for documentation checking
    """
    return {
        "min_coverage": 80.0,
        "min_grade": "C",
        "min_score": 70.0,
        "ignore_init_method": True,
        "ignore_magic": True,
        "ignore_setters": True,
        "ignore": ["__pycache__", "*.pyc", "test_*", "tests/*", "*/.venv/*", "*/venv/*"],
    }


@pytest.fixture
def documentation_checker_strict(documentation_config: dict[str, Any]) -> DocumentationFixture:
    """Provide strict documentation checker fixture.

    Args:
        documentation_config: Base configuration

    Returns:
        DocumentationFixture with strict requirements
    """
    config = documentation_config.copy()
    config.update(
        {
            "min_coverage": 95.0,
            "min_grade": "A",
            "min_score": 95.0,
            "ignore_init_method": False,
            "ignore_magic": False,
        }
    )

    fixture = DocumentationFixture(config)
    fixture.setup()
    yield fixture
    fixture.teardown()
