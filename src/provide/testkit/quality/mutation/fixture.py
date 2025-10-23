"""Pytest fixtures for mutation testing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ..base import BaseQualityFixture, QualityResult
from .runner import MutationRunner
from .tracker import MutationTracker


class MutationFixture(BaseQualityFixture):
    """Pytest fixture for mutation testing.

    Provides mutation testing capabilities to pytest tests with
    automatic configuration loading and result tracking.
    """

    def __init__(self, config: dict[str, Any] | None = None, artifact_dir: Path | None = None) -> None:
        """Initialize mutation fixture.

        Args:
            config: Mutation testing configuration
            artifact_dir: Directory for artifacts (default: .quality-artifacts/mutation)
        """
        super().__init__(config, artifact_dir)

        self.runner = MutationRunner(config)
        self.tracker = MutationTracker(self.artifact_dir / ".mutation-scores.json")
        self._results: list[QualityResult] = []

    def analyze(self, path: Path | str, **kwargs: Any) -> QualityResult:
        """Run mutation analysis on path.

        Args:
            path: Path to analyze
            **kwargs: Additional options for mutation runner

        Returns:
            QualityResult from mutation testing
        """
        if isinstance(path, str):
            path = Path(path)

        result = self.runner.analyze(path, **kwargs)
        self._results.append(result)

        # Track the score
        if result.passed or result.score > 0:
            self.tracker.record_score(
                module=str(path),
                score=result.score,
                total_mutants=result.details.get("total_mutants", 0),
                killed=result.details.get("killed", 0),
                survived=result.details.get("survived", 0),
            )

        return result

    def analyze_module(self, module_path: str | Path, target_score: float | None = None) -> QualityResult:
        """Analyze specific module.

        Args:
            module_path: Path to module
            target_score: Override target score

        Returns:
            QualityResult for module
        """
        return self.runner.run_module(module_path, target_score)

    def analyze_changed(self, base_branch: str = "main") -> QualityResult:
        """Analyze only changed files.

        Args:
            base_branch: Branch to compare against

        Returns:
            QualityResult for changed files
        """
        return self.runner.run_changed_files(base_branch)

    def get_history(self, module: str, limit: int | None = None) -> list[Any]:
        """Get mutation score history for module.

        Args:
            module: Module path
            limit: Maximum records to return

        Returns:
            List of historical scores
        """
        return self.tracker.get_history(module, limit)

    def check_regression(self, module: str, threshold: float = 5.0) -> tuple[bool, float]:
        """Check for score regression.

        Args:
            module: Module path
            threshold: Regression threshold percentage

        Returns:
            Tuple of (is_regression, score_diff)
        """
        latest = self.tracker.get_latest_score(module)
        if not latest:
            return (False, 0.0)

        # Find current score from results
        current_result = next((r for r in self._results if module in str(r.details)), None)
        if not current_result:
            return (False, 0.0)

        return self.tracker.check_regression(module, current_result.score, threshold)

    @property
    def results(self) -> list[QualityResult]:
        """Get all mutation test results from this session."""
        return self._results


@pytest.fixture
def mutation_runner(request: pytest.FixtureRequest, tmp_path: Path) -> MutationFixture:
    """Provide mutation testing runner for individual tests.

    Args:
        request: Pytest request fixture
        tmp_path: Pytest tmp_path fixture

    Returns:
        MutationFixture instance

    Example:
        def test_my_mutations(mutation_runner):
            result = mutation_runner.analyze(Path("src/mymodule.py"))
            assert result.score >= 80
    """
    # Load config from pytest config if available
    config = {}
    if hasattr(request.config, "inicfg"):
        # Try to load from pyproject.toml or similar
        config = getattr(request.config, "_mutation_config", {})

    artifact_dir = tmp_path / ".mutation-artifacts"
    return MutationFixture(config=config, artifact_dir=artifact_dir)


@pytest.fixture(scope="session")
def session_mutation(tmp_path_factory: pytest.TempPathFactory) -> MutationFixture:
    """Provide session-wide mutation testing tracker.

    Args:
        tmp_path_factory: Pytest temp path factory

    Returns:
        MutationFixture instance shared across session

    Example:
        def test_accumulate_scores(session_mutation):
            # Scores tracked across all tests in session
            result1 = session_mutation.analyze(Path("src/module1.py"))
            result2 = session_mutation.analyze(Path("src/module2.py"))

            # Check overall trend
            assert len(session_mutation.results) == 2
    """
    tmp_path = tmp_path_factory.mktemp("mutation")
    artifact_dir = tmp_path / ".mutation-artifacts"

    return MutationFixture(artifact_dir=artifact_dir)
