"""Documentation coverage checker implementation using interrogate."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

try:
    import interrogate
    from interrogate import coverage
    from interrogate.config import InterrogateConfig
    INTERROGATE_AVAILABLE = True
except ImportError:
    INTERROGATE_AVAILABLE = False
    interrogate = None
    coverage = None
    InterrogateConfig = None

from ..base import QualityResult, QualityTool, QualityToolError


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
                "Interrogate not available. Install with: pip install interrogate",
                tool="documentation"
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
                execution_time=time.time() - start_time
            )

    def _run_interrogate_analysis(self, path: Path) -> QualityResult:
        """Run interrogate documentation analysis."""
        if not INTERROGATE_AVAILABLE:
            raise QualityToolError("Interrogate not available", tool="documentation")

        try:
            # Create interrogate configuration
            config_args = self._build_interrogate_config()

            # Create config object
            config = InterrogateConfig(
                paths=[str(path)],
                **config_args
            )

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
        ignore_patterns = self.config.get("ignore", [
            "__pycache__",
            "*.pyc",
            "test_*",
            "tests/*",
            "*/.venv/*",
            "*/venv/*"
        ])
        if ignore_patterns:
            config["ignore_regex"] = ignore_patterns

        # Set what to check
        config["ignore_init_method"] = self.config.get("ignore_init_method", True)
        config["ignore_init_module"] = self.config.get("ignore_init_module", False)
        config["ignore_magic"] = self.config.get("ignore_magic", True)
        config["ignore_nested_functions"] = self.config.get("ignore_nested_functions", False)
        config["ignore_private"] = self.config.get("ignore_private", False)
        config["ignore_property_decorators"] = self.config.get("ignore_property_decorators", False)
        config["ignore_semiprivate"] = self.config.get("ignore_semiprivate", False)
        config["ignore_setters"] = self.config.get("ignore_setters", True)

        # Verbosity and output
        config["verbose"] = self.config.get("verbose", 0)
        config["quiet"] = self.config.get("quiet", False)

        return config

    def _process_interrogate_results(self, results: Any, config: Any) -> QualityResult:
        """Process interrogate results into QualityResult."""

        # Extract coverage metrics
        total_coverage = results.perc_covered

        # Get detailed breakdown
        missing_count = results.missing_count
        covered_count = results.covered_count
        total_count = missing_count + covered_count

        # Calculate grade based on coverage
        if total_coverage >= 95:
            grade = "A"
            score = 100.0
        elif total_coverage >= 90:
            grade = "A-"
            score = 95.0
        elif total_coverage >= 85:
            grade = "B+"
            score = 90.0
        elif total_coverage >= 80:
            grade = "B"
            score = 85.0
        elif total_coverage >= 75:
            grade = "B-"
            score = 80.0
        elif total_coverage >= 70:
            grade = "C+"
            score = 75.0
        elif total_coverage >= 65:
            grade = "C"
            score = 70.0
        elif total_coverage >= 60:
            grade = "C-"
            score = 65.0
        elif total_coverage >= 50:
            grade = "D"
            score = 55.0
        else:
            grade = "F"
            score = 40.0

        # Determine if passed based on configuration
        min_coverage = self.config.get("min_coverage", 80.0)
        min_grade = self.config.get("min_grade", "C")
        required_score = self.config.get("min_score", 70.0)

        grade_values = {"A": 9, "A-": 8, "B+": 7, "B": 6, "B-": 5, "C+": 4, "C": 3, "C-": 2, "D": 1, "F": 0}

        passed = (
            total_coverage >= min_coverage and
            grade_values.get(grade, 0) >= grade_values.get(min_grade, 0) and
            score >= required_score
        )

        # Create detailed results
        details = {
            "total_coverage": round(total_coverage, 2),
            "covered_count": covered_count,
            "missing_count": missing_count,
            "total_count": total_count,
            "grade": grade,
            "thresholds": {
                "min_coverage": min_coverage,
                "min_grade": min_grade,
                "min_score": required_score
            }
        }

        # Add file-level details if available
        if hasattr(results, 'detailed_coverage'):
            file_details = []
            for file_info in results.detailed_coverage:
                file_details.append({
                    "file": str(file_info.filename),
                    "coverage": file_info.perc_covered,
                    "covered": file_info.covered_count,
                    "missing": file_info.missing_count
                })
            details["file_coverage"] = file_details

        return QualityResult(
            tool="documentation",
            passed=passed,
            score=score,
            details=details
        )

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate documentation analysis artifacts.

        Args:
            result: Result to add artifacts to
        """
        if not self.artifact_dir:
            return

        self.artifact_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Generate JSON report
            json_file = self.artifact_dir / "documentation.json"
            json_data = {
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
                "execution_time": result.execution_time
            }
            json_file.write_text(json.dumps(json_data, indent=2))
            result.artifacts.append(json_file)

            # Generate text summary
            summary_file = self.artifact_dir / "documentation_summary.txt"
            summary_report = self._generate_text_report(result)
            summary_file.write_text(summary_report)
            result.artifacts.append(summary_file)

            # Generate detailed coverage report if available
            if result.details.get("file_coverage"):
                detail_file = self.artifact_dir / "documentation_details.txt"
                detail_report = self._generate_detail_report(result)
                detail_file.write_text(detail_report)
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
            lines.extend([
                "",
                f"Documented Items: {details['covered_count']}",
                f"Missing Documentation: {details['missing_count']}",
                f"Total Items: {details['total_count']}",
            ])

        thresholds = details.get("thresholds", {})
        if thresholds:
            lines.extend([
                "",
                "Thresholds:",
                f"  Minimum Coverage: {thresholds.get('min_coverage', 0)}%",
                f"  Minimum Grade: {thresholds.get('min_grade', 'N/A')}",
                f"  Minimum Score: {thresholds.get('min_score', 0)}%",
            ])

        if result.execution_time:
            lines.append(f"\nExecution Time: {result.execution_time:.2f}s")

        return "\n".join(lines)

    def _generate_detail_report(self, result: QualityResult) -> str:
        """Generate detailed file coverage report."""
        lines = [
            "Documentation Coverage by File",
            "=" * 50,
            ""
        ]

        file_coverage = result.details.get("file_coverage", [])

        # Sort by coverage (lowest first to highlight problem files)
        sorted_files = sorted(file_coverage, key=lambda x: x["coverage"])

        for file_info in sorted_files:
            coverage = file_info["coverage"]
            status = "✅" if coverage >= 80 else "⚠️" if coverage >= 60 else "❌"
            lines.append(f"{status} {file_info['file']}: {coverage:.1f}% ({file_info['covered']}/{file_info['covered'] + file_info['missing']})")

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
            return json.dumps({
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details
            }, indent=2)
        else:
            return str(result.details)