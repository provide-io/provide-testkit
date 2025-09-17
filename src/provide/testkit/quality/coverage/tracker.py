"""Coverage tracking implementation."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

try:
    from coverage import Coverage

    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False
    Coverage = None

from ..base import QualityResult, QualityToolError


class CoverageTracker:
    """Wrapper for coverage.py library with testkit integration.

    Provides high-level interface for coverage tracking with automatic
    artifact management and integration with the quality framework.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize coverage tracker.

        Args:
            config: Coverage configuration options
        """
        if not COVERAGE_AVAILABLE:
            raise QualityToolError(
                "Coverage.py not available. Install with: pip install coverage", tool="coverage"
            )

        self.config = config or {}
        self.coverage: Coverage | None = None
        self.is_running = False
        self.artifact_dir: Path | None = None

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        """Run coverage analysis on the given path.

        Args:
            path: Path to analyze
            **kwargs: Additional options including artifact_dir

        Returns:
            QualityResult with coverage data
        """
        self.artifact_dir = kwargs.get("artifact_dir", Path(".coverage"))
        start_time = time.time()

        try:
            # If coverage is already running, get current data
            if self.is_running and self.coverage:
                self.stop()

            # Start fresh coverage analysis
            self.start()

            # For analysis mode, we need to combine existing coverage data
            # This is typically used when coverage was collected during test runs
            self._load_existing_data()

            # Generate report
            result = self._create_result()
            result.execution_time = time.time() - start_time

            # Generate artifacts
            self._generate_artifacts(result)

            return result

        except Exception as e:
            return QualityResult(
                tool="coverage",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def start(self) -> None:
        """Start coverage tracking."""
        if self.is_running:
            return

        coverage_config = self._build_coverage_config()
        self.coverage = Coverage(**coverage_config)
        self.coverage.start()
        self.is_running = True

    def stop(self) -> None:
        """Stop coverage tracking and save data."""
        if not self.is_running or not self.coverage:
            return

        self.coverage.stop()
        self.coverage.save()
        self.is_running = False

    def get_coverage(self) -> float:
        """Get current coverage percentage.

        Returns:
            Coverage percentage (0-100)
        """
        if not self.coverage:
            return 0.0

        try:
            # Get coverage data
            total = self.coverage.report(file=None, show_missing=False)
            return round(total, 2)
        except Exception:
            return 0.0

    def generate_report(self, format: str = "terminal") -> str:
        """Generate coverage report.

        Args:
            format: Report format (terminal, html, xml, json)

        Returns:
            Report content (for terminal/json) or path (for html/xml)
        """
        if not self.coverage:
            return "No coverage data available"

        if format == "terminal":
            return self._generate_terminal_report()
        elif format == "html" and self.artifact_dir:
            html_dir = self.artifact_dir / "htmlcov"
            self.coverage.html_report(directory=str(html_dir))
            return str(html_dir / "index.html")
        elif format == "xml" and self.artifact_dir:
            xml_file = self.artifact_dir / "coverage.xml"
            self.coverage.xml_report(outfile=str(xml_file))
            return str(xml_file)
        elif format == "json" and self.artifact_dir:
            json_file = self.artifact_dir / "coverage.json"
            self.coverage.json_report(outfile=str(json_file))
            return json_file.read_text()
        else:
            return f"Unsupported format: {format}"

    def report(self, result: QualityResult, format: str = "terminal") -> str:
        """Generate report from QualityResult (implements QualityTool protocol).

        Args:
            result: Coverage result
            format: Report format

        Returns:
            Formatted report
        """
        if format == "terminal":
            lines = [
                f"Coverage Report - {result.tool}",
                "=" * 40,
                f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}",
            ]

            if result.score is not None:
                lines.append(f"Coverage: {result.score}%")

            if "total_statements" in result.details:
                details = result.details
                lines.extend(
                    [
                        f"Total Statements: {details.get('total_statements', 0)}",
                        f"Missing Statements: {details.get('missing_statements', 0)}",
                        f"Branch Coverage: {details.get('branch_coverage', 'N/A')}%",
                    ]
                )

            return "\n".join(lines)

        return str(result.details)

    def _build_coverage_config(self) -> dict[str, Any]:
        """Build coverage.py configuration."""
        config = {
            "branch": self.config.get("branch", True),
            "source": self.config.get("source", ["src"]),
            "omit": self.config.get(
                "omit", ["*/tests/*", "*/test_*", "*/.venv/*", "*/venv/*", "*/__pycache__/*"]
            ),
        }

        # Add data file configuration if artifact directory is set
        if self.artifact_dir:
            config["data_file"] = str(self.artifact_dir / ".coverage")

        return config

    def _load_existing_data(self) -> None:
        """Load existing coverage data if available."""
        if not self.coverage or not self.artifact_dir:
            return

        data_file = self.artifact_dir / ".coverage"
        if data_file.exists():
            try:
                self.coverage.load()
            except Exception:
                # If loading fails, continue with fresh data
                pass

    def _create_result(self) -> QualityResult:
        """Create QualityResult from current coverage data."""
        if not self.coverage:
            return QualityResult(tool="coverage", passed=False, details={"error": "No coverage instance"})

        try:
            # Get coverage percentage
            coverage_percent = self.get_coverage()

            # Get detailed metrics
            total_statements = 0
            missing_statements = 0
            branch_coverage = None

            # Access coverage data for detailed metrics
            data = self.coverage.get_data()
            if data:
                try:
                    # Count statements across all files
                    for filename in data.measured_files():
                        file_data = data.lines(filename)
                        if file_data:
                            total_statements += len(file_data)

                    # Get missing statements
                    if hasattr(self.coverage, "_analyze"):
                        for filename in data.measured_files():
                            try:
                                analysis = self.coverage._analyze(filename)
                                missing_statements += len(analysis.missing)
                            except Exception:
                                continue
                except Exception:
                    # Handle mock objects or other issues gracefully
                    pass

            # Calculate pass/fail based on configured threshold
            threshold = self.config.get("fail_under", 0)
            passed = coverage_percent >= threshold

            return QualityResult(
                tool="coverage",
                passed=passed,
                score=coverage_percent,
                details={
                    "total_statements": total_statements,
                    "missing_statements": missing_statements,
                    "branch_coverage": branch_coverage,
                    "threshold": threshold,
                },
            )

        except Exception as e:
            return QualityResult(tool="coverage", passed=False, details={"error": str(e)})

    def _generate_terminal_report(self) -> str:
        """Generate terminal coverage report."""
        if not self.coverage:
            return "No coverage data available"

        try:
            from io import StringIO

            output = StringIO()
            self.coverage.report(file=output, show_missing=True)
            return output.getvalue()
        except Exception as e:
            return f"Error generating report: {e}"

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate coverage artifacts.

        Args:
            result: Result to add artifacts to
        """
        if not self.artifact_dir:
            return

        self.artifact_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Generate HTML report
            html_dir = self.artifact_dir / "htmlcov"
            self.coverage.html_report(directory=str(html_dir))
            if html_dir.exists():
                result.artifacts.append(html_dir / "index.html")

            # Generate XML report
            xml_file = self.artifact_dir / "coverage.xml"
            self.coverage.xml_report(outfile=str(xml_file))
            if xml_file.exists():
                result.artifacts.append(xml_file)

            # Generate terminal report
            terminal_file = self.artifact_dir / "coverage.txt"
            terminal_report = self._generate_terminal_report()
            terminal_file.write_text(terminal_report)
            result.artifacts.append(terminal_file)

        except Exception as e:
            # Add error to result details but don't fail
            result.details["artifact_error"] = str(e)
