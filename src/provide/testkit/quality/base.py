"""Base classes and protocols for quality analysis tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass
class QualityResult:
    """Result from a quality analysis tool.

    Attributes:
        tool: Name of the tool that generated this result
        passed: Whether the quality check passed
        score: Numeric score (0-100) if applicable
        details: Tool-specific details and metrics
        artifacts: List of artifact files created
        execution_time: Time taken to run the analysis in seconds
    """

    tool: str
    passed: bool
    score: float | None = None
    details: dict[str, Any] = field(default_factory=dict)
    artifacts: list[Path] = field(default_factory=list)
    execution_time: float | None = None

    @property
    def summary(self) -> str:
        """Human-readable summary of the result."""
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        score_text = f" ({self.score}%)" if self.score is not None else ""
        return f"{self.tool}: {status}{score_text}"


@runtime_checkable
class QualityTool(Protocol):
    """Protocol for quality analysis tools."""

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        """Run analysis on the given path.

        Args:
            path: Path to analyze (file or directory)
            **kwargs: Tool-specific options

        Returns:
            QualityResult containing analysis results
        """
        ...

    def report(self, result: QualityResult, format: str = "terminal") -> str:
        """Generate a report from analysis result.

        Args:
            result: Result to generate report for
            format: Output format (terminal, json, html, markdown)

        Returns:
            Formatted report string
        """
        ...


class BaseQualityFixture(ABC):
    """Base class for pytest quality fixtures.

    Provides common functionality for quality analysis fixtures including
    configuration management, artifact handling, and result tracking.
    """

    def __init__(self, config: dict[str, Any] | None = None, artifact_dir: Path | None = None):
        """Initialize the fixture.

        Args:
            config: Tool-specific configuration
            artifact_dir: Directory to store artifacts
        """
        self.config = config or {}
        self.artifact_dir = artifact_dir or Path(".quality")
        self.results: list[QualityResult] = []
        self._setup_complete = False

    @abstractmethod
    def setup(self) -> None:
        """Setup the quality tool."""
        pass

    @abstractmethod
    def teardown(self) -> None:
        """Cleanup after quality check."""
        pass

    def add_result(self, result: QualityResult) -> None:
        """Add a result to the tracked results."""
        self.results.append(result)

    def get_results(self) -> list[QualityResult]:
        """Get all tracked results."""
        return self.results.copy()

    def get_results_by_tool(self) -> dict[str, QualityResult]:
        """Get results indexed by tool name."""
        return {result.tool: result for result in self.results}

    def ensure_setup(self) -> None:
        """Ensure setup has been called."""
        if not self._setup_complete:
            self.setup()
            self._setup_complete = True

    def create_artifact_dir(self, subdir: str | None = None) -> Path:
        """Create and return artifact directory.

        Args:
            subdir: Optional subdirectory name

        Returns:
            Path to the artifact directory
        """
        if subdir:
            artifact_path = self.artifact_dir / subdir
        else:
            artifact_path = self.artifact_dir

        artifact_path.mkdir(parents=True, exist_ok=True)
        return artifact_path


class QualityError(Exception):
    """Base exception for quality analysis errors."""

    def __init__(self, message: str, tool: str | None = None, details: dict[str, Any] | None = None):
        """Initialize quality error.

        Args:
            message: Error message
            tool: Name of tool that caused the error
            details: Additional error details
        """
        super().__init__(message)
        self.tool = tool
        self.details = details or {}


class QualityConfigError(QualityError):
    """Exception for configuration errors."""

    pass


class QualityToolError(QualityError):
    """Exception for tool execution errors."""

    pass
