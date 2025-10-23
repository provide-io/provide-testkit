"""Tests for mutation testing integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from provide.testkit.quality.mutation import (
    ModulePriority,
    MutationConfig,
    MutationRunner,
    MutationTracker,
)


def test_mutation_config_defaults() -> None:
    """Test MutationConfig default values."""
    config = MutationConfig()

    assert config.paths_to_mutate == ["src"]
    assert "*_pb2.py" in config.exclude_patterns
    assert config.max_workers == 4
    assert config.score_thresholds[ModulePriority.CRITICAL] == 100.0
    assert config.score_thresholds[ModulePriority.HIGH] == 80.0


def test_mutation_config_from_dict() -> None:
    """Test creating MutationConfig from dictionary."""
    config_dict = {
        "paths_to_mutate": ["src/myapp"],
        "module_priorities": {"src/security.py": "critical", "src/core.py": "high"},
        "max_workers": 8,
    }

    config = MutationConfig.from_dict(config_dict)

    assert config.paths_to_mutate == ["src/myapp"]
    assert config.module_priorities["src/security.py"] == ModulePriority.CRITICAL
    assert config.module_priorities["src/core.py"] == ModulePriority.HIGH
    assert config.max_workers == 8


def test_mutation_config_get_module_priority() -> None:
    """Test getting module priority."""
    config = MutationConfig(module_priorities={"src/security.py": ModulePriority.CRITICAL})

    assert config.get_module_priority("src/security.py") == ModulePriority.CRITICAL
    assert config.get_module_priority("src/other.py") == ModulePriority.STANDARD


def test_mutation_config_get_target_score() -> None:
    """Test getting target score for module."""
    config = MutationConfig(
        module_priorities={"src/security.py": ModulePriority.CRITICAL},
        score_thresholds={ModulePriority.CRITICAL: 100.0, ModulePriority.STANDARD: 60.0},
    )

    assert config.get_target_score("src/security.py") == 100.0
    assert config.get_target_score("src/other.py") == 60.0


def test_mutation_runner_initialization() -> None:
    """Test MutationRunner initialization."""
    runner = MutationRunner({})

    assert runner.config is not None
    assert isinstance(runner.config, MutationConfig)


@patch("provide.testkit.quality.mutation.runner.subprocess.run")
def test_mutation_runner_parse_results(mock_run) -> None:
    """Test parsing mutmut results."""
    mock_run.return_value = Mock(
        stdout="Survived 🙁: 5\nKilled ⚔️: 120\nTimeout ⏰: 2\nSuspicious 🤔: 1\n"
    )

    runner = MutationRunner({})
    counts = runner._parse_mutmut_results(Path("/tmp"))

    assert counts["killed"] == 120
    assert counts["survived"] == 5
    assert counts["timeout"] == 2
    assert counts["suspicious"] == 1


def test_mutation_tracker_initialization(tmp_path) -> None:
    """Test MutationTracker initialization."""
    scores_file = tmp_path / ".mutation-scores.json"
    tracker = MutationTracker(scores_file)

    assert tracker.scores_file == scores_file
    assert isinstance(tracker._scores, dict)


def test_mutation_tracker_record_score(tmp_path) -> None:
    """Test recording a mutation score."""
    scores_file = tmp_path / ".mutation-scores.json"
    tracker = MutationTracker(scores_file)

    score = tracker.record_score(module="src/test.py", score=85.0, total_mutants=100, killed=85, survived=15)

    assert score.module == "src/test.py"
    assert score.score == 85.0
    assert score.killed == 85
    assert score.survived == 15

    # Verify it was saved
    assert scores_file.exists()


def test_mutation_tracker_get_history(tmp_path) -> None:
    """Test getting mutation score history."""
    scores_file = tmp_path / ".mutation-scores.json"
    tracker = MutationTracker(scores_file)

    # Record multiple scores
    tracker.record_score("src/test.py", 80.0, 100, 80, 20)
    tracker.record_score("src/test.py", 85.0, 100, 85, 15)
    tracker.record_score("src/test.py", 90.0, 100, 90, 10)

    history = tracker.get_history("src/test.py")

    assert len(history) == 3
    # Should be newest first
    assert history[0].score == 90.0
    assert history[1].score == 85.0
    assert history[2].score == 80.0


def test_mutation_tracker_check_regression(tmp_path) -> None:
    """Test regression detection."""
    scores_file = tmp_path / ".mutation-scores.json"
    tracker = MutationTracker(scores_file)

    # Record baseline score
    tracker.record_score("src/test.py", 90.0, 100, 90, 10)

    # Check regression with lower score
    is_regression, diff = tracker.check_regression("src/test.py", 80.0)

    assert is_regression is True
    assert diff == 10.0

    # Check no regression
    is_regression, diff = tracker.check_regression("src/test.py", 89.0, threshold=5.0)

    assert is_regression is False


def test_mutation_tracker_get_trend(tmp_path) -> None:
    """Test trend calculation."""
    scores_file = tmp_path / ".mutation-scores.json"
    tracker = MutationTracker(scores_file)

    # Record improving trend
    tracker.record_score("src/test.py", 70.0, 100, 70, 30)
    tracker.record_score("src/test.py", 75.0, 100, 75, 25)
    tracker.record_score("src/test.py", 80.0, 100, 80, 20)
    tracker.record_score("src/test.py", 85.0, 100, 85, 15)

    trend = tracker.get_trend("src/test.py", num_records=4)

    assert trend == "improving"


@pytest.mark.integration
def test_mutation_fixture_integration(mutation_runner) -> None:
    """Test mutation fixture integration."""
    assert mutation_runner is not None
    assert hasattr(mutation_runner, "analyze")
    assert hasattr(mutation_runner, "runner")
    assert hasattr(mutation_runner, "tracker")
