"""Mutation score tracking and history management."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from provide.foundation import logger


@dataclass
class MutationScore:
    """A single mutation score record."""

    module: str
    score: float
    total_mutants: int
    killed: int
    survived: int
    timestamp: str
    commit_hash: str | None = None
    branch: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MutationScore:
        """Create from dictionary."""
        return cls(**data)


class MutationTracker:
    """Tracks mutation scores over time and detects regressions."""

    def __init__(self, scores_file: Path | None = None) -> None:
        """Initialize tracker.

        Args:
            scores_file: Path to scores JSON file (default: .mutation-scores.json)
        """
        self.scores_file = scores_file or Path(".mutation-scores.json")
        self.logger = logger.get_logger(__name__)
        self._scores: dict[str, list[MutationScore]] = {}
        self._load()

    def record_score(
        self,
        module: str,
        score: float,
        total_mutants: int,
        killed: int,
        survived: int,
        commit_hash: str | None = None,
        branch: str | None = None,
    ) -> MutationScore:
        """Record a new mutation score for a module.

        Args:
            module: Module path
            score: Mutation score (0-100)
            total_mutants: Total number of mutants
            killed: Number of killed mutants
            survived: Number of survived mutants
            commit_hash: Git commit hash (optional)
            branch: Git branch name (optional)

        Returns:
            The recorded MutationScore
        """
        timestamp = datetime.utcnow().isoformat()

        score_record = MutationScore(
            module=module,
            score=score,
            total_mutants=total_mutants,
            killed=killed,
            survived=survived,
            timestamp=timestamp,
            commit_hash=commit_hash,
            branch=branch,
        )

        if module not in self._scores:
            self._scores[module] = []

        self._scores[module].append(score_record)
        self._save()

        self.logger.debug(f"Recorded mutation score for {module}: {score:.1f}%")
        return score_record

    def get_history(self, module: str, limit: int | None = None) -> list[MutationScore]:
        """Get historical scores for a module.

        Args:
            module: Module path
            limit: Maximum number of records to return (None for all)

        Returns:
            List of MutationScore records, newest first
        """
        scores = self._scores.get(module, [])
        scores_sorted = sorted(scores, key=lambda s: s.timestamp, reverse=True)

        if limit:
            return scores_sorted[:limit]
        return scores_sorted

    def get_latest_score(self, module: str) -> MutationScore | None:
        """Get the most recent score for a module.

        Args:
            module: Module path

        Returns:
            Latest MutationScore or None if no history
        """
        history = self.get_history(module, limit=1)
        return history[0] if history else None

    def check_regression(
        self, module: str, current_score: float, threshold: float = 5.0
    ) -> tuple[bool, float]:
        """Check if current score represents a regression.

        Args:
            module: Module path
            current_score: Current mutation score
            threshold: Percentage drop to consider a regression (default: 5%)

        Returns:
            Tuple of (is_regression, score_diff)
        """
        latest = self.get_latest_score(module)

        if latest is None:
            # No history, not a regression
            return (False, 0.0)

        score_diff = latest.score - current_score

        is_regression = score_diff > threshold

        if is_regression:
            self.logger.warning(
                f"Mutation score regression detected for {module}: "
                f"{latest.score:.1f}% -> {current_score:.1f}% "
                f"(dropped {score_diff:.1f}%)"
            )

        return (is_regression, score_diff)

    def get_trend(self, module: str, num_records: int = 5) -> str:
        """Get trend direction for a module's scores.

        Args:
            module: Module path
            num_records: Number of recent records to analyze

        Returns:
            Trend direction: "improving", "declining", "stable", or "unknown"
        """
        history = self.get_history(module, limit=num_records)

        if len(history) < 2:
            return "unknown"

        scores = [s.score for s in history]
        scores.reverse()  # Oldest to newest

        # Calculate simple linear trend
        n = len(scores)
        x = list(range(n))
        mean_x = sum(x) / n
        mean_y = sum(scores) / n

        numerator = sum((x[i] - mean_x) * (scores[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if slope > 1.0:
            return "improving"
        elif slope < -1.0:
            return "declining"
        else:
            return "stable"

    def get_all_modules(self) -> list[str]:
        """Get list of all tracked modules.

        Returns:
            List of module paths
        """
        return list(self._scores.keys())

    def _load(self) -> None:
        """Load scores from file."""
        if not self.scores_file.exists():
            return

        try:
            with self.scores_file.open("r") as f:
                data = json.load(f)

            self._scores = {}
            for module, scores_data in data.items():
                self._scores[module] = [MutationScore.from_dict(s) for s in scores_data]

            self.logger.debug(f"Loaded mutation scores from {self.scores_file}")

        except Exception as e:
            self.logger.error(f"Failed to load mutation scores: {e}")

    def _save(self) -> None:
        """Save scores to file."""
        try:
            data = {module: [s.to_dict() for s in scores] for module, scores in self._scores.items()}

            # Ensure parent directory exists
            self.scores_file.parent.mkdir(parents=True, exist_ok=True)

            with self.scores_file.open("w") as f:
                json.dump(data, f, indent=2)

            self.logger.debug(f"Saved mutation scores to {self.scores_file}")

        except Exception as e:
            self.logger.error(f"Failed to save mutation scores: {e}")
