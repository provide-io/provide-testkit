"""Documentation coverage checker implementation using interrogate."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from provide.foundation.file import atomic_write_text, ensure_dir

try:
    import interrogate  # type: ignore[import-untyped]
    from interrogate import coverage
    from interrogate.config import InterrogateConfig  # type: ignore[import-untyped]

    INTERROGATE_AVAILABLE = True
except ImportError:
    INTERROGATE_AVAILABLE = False
    interrogate = None
    coverage = None
    InterrogateConfig = None

from ..base import QualityResult, QualityToolError


class DocumentationChecker:
    """Documentation coverage checker using interrogate.

    Provides high-level interface for documentation analysis with automatic
    artifact management and integration with the quality framework.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize documentation checker.

        Args:
            config: Documentation checker configuration options
        """
        if not INTERROGATE_AVAILABLE:
            raise QualityToolError(
                "Interrogate not available. Install with: pip install interrogate", tool="documentation"
            )

        self.config = config or {}
        self.artifact_dir: Path | None = None

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        """Run documentation analysis on the given path.

        Args:
            path: Path to analyze
            **kwargs: Additional options including artifact_dir

        Returns:
            QualityResult with documentation analysis data
        """
        self.artifact_dir = kwargs.get("artifact_dir", Path(".documentation"))
        start_time = time.time()

        try:
            # Run interrogate documentation analysis
            result = self._run_interrogate_analysis(path)
            result.execution_time = time.time() - start_time

            # Generate artifacts
            self._generate_artifacts(result)

            return result

        except Exception as e:
            return QualityResult(
                tool="documentation",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def _run_interrogate_analysis(self, path: Path) -> QualityResult:
        """Run interrogate documentation analysis."""
        if not INTERROGATE_AVAILABLE:
            raise QualityToolError("Interrogate not available", tool="documentation")

        try:
            # Create interrogate configuration
            config_args = self._build_interrogate_config()

            # Create config object - filter out unsupported parameters
            supported_args = {}
            for key, value in config_args.items():
                # Only include basic supported parameters for InterrogateConfig
                if key in [
                    "ignore_init_method",
                    "ignore_magic",
                    "ignore_private",
                    "verbose",
                    "quiet",
                    "paths",
                ]:
                    supported_args[key] = value

            supported_args["paths"] = [str(path)]
            config = InterrogateConfig(**supported_args)

            # Run interrogate analysis
            cov = coverage.InterrogateCoverage(config=config)
            results = cov.get_coverage()

            # Process results
            return self._process_interrogate_results(results, config)

        except Exception as e:
            raise QualityToolError(f"Interrogate analysis failed: {e}", tool="documentation")

    def _build_interrogate_config(self) -> dict[str, Any]:
        """Build interrogate configuration from config."""
        config = {}

        # Set ignore patterns
        ignore_patterns = self.config.get(
            "ignore", ["__pycache__", "*.pyc", "test_*", "tests/*", "*/.venv/*", "*/venv/*"]
        )
        if ignore_patterns:
            # Convert list to regex pattern for interrogate
            pattern_string = "|".join(str(pattern) for pattern in ignore_patterns)
            config["ignore_regex"] = pattern_string

        # Set what to check - these are the keys that tests expect
        config["ignore_init_method"] = self.config.get("ignore_init_method", True)
        config["ignore_magic"] = self.config.get("ignore_magic", True)
        config["ignore_private"] = self.config.get("ignore_private", False)
        config["ignore_setters"] = self.config.get("ignore_setters", True)

        # Verbosity and output
        config["verbose"] = self.config.get("verbose", 0)
        if self.config.get("quiet", False):
            config["quiet"] = True

        return config

    def _process_interrogate_results(self, results: Any, config: Any) -> QualityResult:
        """Process interrogate results into QualityResult."""
        # Extract coverage metrics
        total_coverage = results.perc_covered
        missing_count = results.missing_count
        covered_count = results.covered_count
        total_count = missing_count + covered_count

        # Calculate grade and score
        grade, score = self._calculate_grade_and_score(total_coverage)

        # Check if passed based on configuration
        passed = self._check_documentation_requirements(total_coverage, grade, score)

        # Create detailed results
        details = self._build_documentation_details(
            total_coverage, covered_count, missing_count, total_count, grade
        )

        # Add file-level details if available
        self._add_file_coverage_details(results, details)

        return QualityResult(tool="documentation", passed=passed, score=score, details=details)

    def _calculate_grade_and_score(self, coverage: float) -> tuple[str, float]:
        """Calculate grade and score based on coverage percentage."""
        grade_thresholds = [
            (95, "A", 100.0),
            (90, "A-", 95.0),
            (85, "B+", 90.0),
            (80, "B", 85.0),
            (75, "B-", 80.0),
            (70, "C+", 75.0),
            (65, "C", 70.0),
            (60, "C-", 65.0),
            (50, "D", 55.0),
        ]

        for threshold, grade, score in grade_thresholds:
            if coverage >= threshold:
                return grade, score

        return "F", 40.0

    def _check_documentation_requirements(self, coverage: float, grade: str, score: float) -> bool:
        """Check if documentation meets the configured requirements."""
        min_coverage = self.config.get("min_coverage", 80.0)
        min_grade = self.config.get("min_grade", "C")
        required_score = self.config.get("min_score", 70.0)

        grade_values = {"A": 9, "A-": 8, "B+": 7, "B": 6, "B-": 5, "C+": 4, "C": 3, "C-": 2, "D": 1, "F": 0}

        return (
            coverage >= min_coverage
            and grade_values.get(grade, 0) >= grade_values.get(min_grade, 0)
            and score >= required_score
        )

    def _build_documentation_details(
        self, coverage: float, covered: int, missing: int, total: int, grade: str
    ) -> dict[str, Any]:
        """Build the details dictionary for documentation results."""
        min_coverage = self.config.get("min_coverage", 80.0)
        min_grade = self.config.get("min_grade", "C")
        required_score = self.config.get("min_score", 70.0)

        return {
            "total_coverage": round(coverage, 2),
            "covered_count": covered,
            "missing_count": missing,
            "total_count": total,
            "grade": grade,
            "thresholds": {"min_coverage": min_coverage, "min_grade": min_grade, "min_score": required_score},
        }

    def _add_file_coverage_details(self, results: Any, details: dict[str, Any]) -> None:
        """Add file-level coverage details if available."""
        if not (hasattr(results, "detailed_coverage") and results.detailed_coverage):
            return

        file_details = []
        try:
            for file_info in results.detailed_coverage:
                file_details.append(
                    {
                        "file": str(file_info.filename),
                        "coverage": file_info.perc_covered,
                        "covered": file_info.covered_count,
                        "missing": file_info.missing_count,
                    }
                )
            details["file_coverage"] = file_details
        except (TypeError, AttributeError):
            # Skip file details if not properly formed
            pass

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate documentation analysis artifacts.

        Args:
            result: Result to add artifacts to
        """
        if not self.artifact_dir:
            return

        ensure_dir(self.artifact_dir)

        try:
            # Generate JSON report
            json_file = self.artifact_dir / "documentation.json"
            json_data = {
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
                "execution_time": result.execution_time,
            }
            atomic_write_text(json_file, json.dumps(json_data, indent=2))
            result.artifacts.append(json_file)

            # Generate text summary
            summary_file = self.artifact_dir / "documentation_summary.txt"
            summary_report = self._generate_text_report(result)
            atomic_write_text(summary_file, summary_report)
            result.artifacts.append(summary_file)

            # Generate detailed coverage report if available
            if result.details.get("file_coverage"):
                detail_file = self.artifact_dir / "documentation_details.txt"
                detail_report = self._generate_detail_report(result)
                atomic_write_text(detail_file, detail_report)
                result.artifacts.append(detail_file)

        except Exception as e:
            # Add error to result details but don't fail
            result.details["artifact_error"] = str(e)

    def _generate_text_report(self, result: QualityResult) -> str:
        """Generate text summary report."""
        lines = [
            f"Documentation Coverage Report - {result.tool}",
            "=" * 50,
            f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}",
            f"Grade: {result.details.get('grade', 'N/A')}",
            f"Coverage: {result.details.get('total_coverage', 0)}%",
            f"Score: {result.score}%",
        ]

        details = result.details
        if "covered_count" in details:
            covered = details["covered_count"]
            missing = details["missing_count"]
            total = details.get("total_count", covered + missing)
            lines.extend(
                [
                    "",
                    f"Documented Items: {covered}",
                    f"Missing Documentation: {missing}",
                    f"Total Items: {total}",
                ]
            )

        thresholds = details.get("thresholds", {})
        if thresholds:
            lines.extend(
                [
                    "",
                    "Thresholds:",
                    f"  Minimum Coverage: {thresholds.get('min_coverage', 0)}%",
                    f"  Minimum Grade: {thresholds.get('min_grade', 'N/A')}",
                    f"  Minimum Score: {thresholds.get('min_score', 0)}%",
                ]
            )

        if result.execution_time:
            lines.append(f"\nExecution Time: {result.execution_time:.2f}s")

        return "\n".join(lines)

    def _generate_detail_report(self, result: QualityResult) -> str:
        """Generate detailed file coverage report."""
        lines = ["Documentation Coverage by File", "=" * 50, ""]

        file_coverage = result.details.get("file_coverage", [])

        # Sort by coverage (lowest first to highlight problem files)
        sorted_files = sorted(file_coverage, key=lambda x: x["coverage"])

        for file_info in sorted_files:
            coverage = file_info["coverage"]
            status = "✅" if coverage >= 80 else "⚠️" if coverage >= 60 else "❌"
            lines.append(
                f"{status} {file_info['file']}: {coverage:.1f}% ({file_info['covered']}/{file_info['covered'] + file_info['missing']})"
            )

        return "\n".join(lines)

    def report(self, result: QualityResult, format: str = "terminal") -> str:
        """Generate report from QualityResult (implements QualityTool protocol).

        Args:
            result: Documentation result
            format: Report format

        Returns:
            Formatted report
        """
        if format == "terminal":
            return self._generate_text_report(result)
        elif format == "json":
            return json.dumps(
                {
                    "tool": result.tool,
                    "passed": result.passed,
                    "score": result.score,
                    "details": result.details,
                },
                indent=2,
            )
        else:
            return str(result.details)
