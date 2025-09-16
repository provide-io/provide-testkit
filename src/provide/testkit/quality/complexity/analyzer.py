"""Complexity analysis implementation using radon."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from provide.foundation.file import atomic_write_text, ensure_dir

try:
    import radon  # type: ignore[import-untyped]
    from radon.complexity import cc_rank, cc_visit  # type: ignore[import-untyped]
    from radon.metrics import mi_visit  # type: ignore[import-untyped]
    from radon.raw import analyze  # type: ignore[import-untyped]

    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    radon = None
    cc_visit = None
    cc_rank = None
    mi_visit = None
    analyze = None

from ..base import QualityResult, QualityToolError


class ComplexityAnalyzer:
    """Code complexity analyzer using radon and other tools.

    Provides high-level interface for complexity analysis with automatic
    artifact management and integration with the quality framework.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize complexity analyzer.

        Args:
            config: Complexity analyzer configuration options
        """
        if not RADON_AVAILABLE:
            raise QualityToolError("Radon not available. Install with: pip install radon", tool="complexity")

        self.config = config or {}
        self.artifact_dir: Path | None = None

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        """Run complexity analysis on the given path.

        Args:
            path: Path to analyze
            **kwargs: Additional options including artifact_dir

        Returns:
            QualityResult with complexity analysis data
        """
        self.artifact_dir = kwargs.get("artifact_dir", Path(".complexity"))
        start_time = time.time()

        try:
            # Run radon complexity analysis
            result = self._run_radon_analysis(path)
            result.execution_time = time.time() - start_time

            # Generate artifacts
            self._generate_artifacts(result)

            return result

        except Exception as e:
            return QualityResult(
                tool="complexity",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def _run_radon_analysis(self, path: Path) -> QualityResult:
        """Run radon complexity analysis."""
        if not RADON_AVAILABLE:
            raise QualityToolError("Radon not available", tool="complexity")

        try:
            # Discover Python files
            python_files = self._discover_python_files(path)

            if not python_files:
                return QualityResult(
                    tool="complexity",
                    passed=True,
                    score=100.0,
                    details={"message": "No Python files found to analyze", "grade": "A"},
                )

            # Analyze each file
            all_complexity = []
            all_raw_metrics = []
            all_maintainability = []

            for file_path in python_files:
                try:
                    content = file_path.read_text()

                    # Cyclomatic complexity
                    complexity_data = cc_visit(content)
                    for item in complexity_data:
                        all_complexity.append(
                            {
                                "file": str(file_path),
                                "name": item.name,
                                "complexity": item.complexity,
                                "rank": cc_rank(item.complexity),
                                "lineno": item.lineno,
                            }
                        )

                    # Raw metrics
                    raw_data = analyze(content)
                    all_raw_metrics.append(
                        {
                            "file": str(file_path),
                            "loc": raw_data.loc,
                            "lloc": raw_data.lloc,
                            "sloc": raw_data.sloc,
                            "comments": raw_data.comments,
                            "multi": raw_data.multi,
                            "blank": raw_data.blank,
                        }
                    )

                    # Maintainability index
                    try:
                        mi_data = mi_visit(content, multi=True)
                        if hasattr(mi_data, "mi"):
                            all_maintainability.append(
                                {"file": str(file_path), "maintainability_index": mi_data.mi}
                            )
                    except Exception:
                        # MI calculation can fail on some files
                        pass

                except Exception:
                    # Skip files that can't be analyzed
                    continue

            # Process results
            return self._process_complexity_results(all_complexity, all_raw_metrics, all_maintainability)

        except Exception as e:
            raise QualityToolError(f"Radon analysis failed: {e}", tool="complexity")

    def _discover_python_files(self, path: Path) -> list[Path]:
        """Discover Python files to analyze."""
        excludes = self.config.get(
            "exclude", ["*/tests/*", "*/test_*", "*/.venv/*", "*/venv/*", "*/__pycache__/*"]
        )

        files = []
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        else:
            for py_file in path.rglob("*.py"):
                # Check if file should be excluded
                if any(py_file.match(pattern) for pattern in excludes):
                    continue
                files.append(py_file)

        return files

    def _process_complexity_results(
        self,
        complexity_data: list[dict[str, Any]],
        raw_metrics: list[dict[str, Any]],
        maintainability_data: list[dict[str, Any]],
    ) -> QualityResult:
        """Process complexity analysis results into QualityResult."""

        # Calculate overall metrics
        total_files = len(raw_metrics)
        total_functions = len(complexity_data)

        # Complexity statistics
        complexities = [item["complexity"] for item in complexity_data]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        max_complexity = max(complexities) if complexities else 0

        # Count by complexity grades
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
        for item in complexity_data:
            grade_counts[item["rank"]] += 1

        # Raw metrics totals
        total_loc = sum(item["loc"] for item in raw_metrics)
        total_lloc = sum(item["lloc"] for item in raw_metrics)
        total_comments = sum(item["comments"] for item in raw_metrics)

        # Maintainability statistics
        if maintainability_data:
            mi_scores = [item["maintainability_index"] for item in maintainability_data]
            avg_maintainability = sum(mi_scores) / len(mi_scores)
        else:
            avg_maintainability = None

        # Calculate overall grade based on average complexity
        if avg_complexity <= 5:
            overall_grade = "A"
            score = 100.0
        elif avg_complexity <= 10:
            overall_grade = "B"
            score = 85.0
        elif avg_complexity <= 20:
            overall_grade = "C"
            score = 70.0
        elif avg_complexity <= 30:
            overall_grade = "D"
            score = 55.0
        else:
            overall_grade = "F"
            score = 40.0

        # Determine if passed based on configuration
        required_grade = self.config.get("min_grade", "C")
        max_complexity_threshold = self.config.get("max_complexity", 20)
        min_score = self.config.get("min_score", 70.0)

        grade_values = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}

        passed = (
            grade_values.get(overall_grade, 0) >= grade_values.get(required_grade, 0)
            and max_complexity <= max_complexity_threshold
            and score >= min_score
        )

        # Create detailed results
        details = {
            "total_files": total_files,
            "total_functions": total_functions,
            "average_complexity": round(avg_complexity, 2),
            "max_complexity": max_complexity,
            "overall_grade": overall_grade,
            "grade_breakdown": grade_counts,
            "lines_of_code": total_loc,
            "logical_lines": total_lloc,
            "comment_lines": total_comments,
            "grade": overall_grade,  # For grade-based gate checking
            "thresholds": {
                "min_grade": required_grade,
                "max_complexity": max_complexity_threshold,
                "min_score": min_score,
            },
        }

        if avg_maintainability is not None:
            details["average_maintainability"] = round(avg_maintainability, 2)

        # Add detailed complexity data (limited for readability)
        if complexity_data:
            # Sort by complexity (highest first) and take top 10
            sorted_complexity = sorted(complexity_data, key=lambda x: x["complexity"], reverse=True)[:10]
            details["most_complex_functions"] = sorted_complexity

        return QualityResult(tool="complexity", passed=passed, score=score, details=details)

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate complexity analysis artifacts.

        Args:
            result: Result to add artifacts to
        """
        if not self.artifact_dir:
            return

        ensure_dir(self.artifact_dir)

        try:
            # Generate JSON report
            json_file = self.artifact_dir / "complexity.json"
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
            summary_file = self.artifact_dir / "complexity_summary.txt"
            summary_report = self._generate_text_report(result)
            atomic_write_text(summary_file, summary_report)
            result.artifacts.append(summary_file)

            # Generate detailed complexity report
            if result.details.get("most_complex_functions"):
                detail_file = self.artifact_dir / "complexity_details.txt"
                detail_report = self._generate_detail_report(result)
                atomic_write_text(detail_file, detail_report)
                result.artifacts.append(detail_file)

        except Exception as e:
            # Add error to result details but don't fail
            result.details["artifact_error"] = str(e)

    def _generate_text_report(self, result: QualityResult) -> str:
        """Generate text summary report."""
        lines = [
            f"Complexity Analysis Report - {result.tool}",
            "=" * 50,
            f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}",
            f"Overall Grade: {result.details.get('overall_grade', 'N/A')}",
            f"Score: {result.score}%",
        ]

        details = result.details
        if "total_files" in details:
            lines.extend(
                [
                    f"Files Analyzed: {details['total_files']}",
                    f"Total Functions: {details['total_functions']}",
                    f"Average Complexity: {details['average_complexity']}",
                    f"Max Complexity: {details['max_complexity']}",
                    "",
                    "Grade Breakdown:",
                ]
            )

            grade_breakdown = details.get("grade_breakdown", {})
            for grade, count in grade_breakdown.items():
                if count > 0:
                    lines.append(f"  {grade}: {count} functions")

            lines.extend(
                [
                    "",
                    f"Lines of Code: {details['lines_of_code']}",
                    f"Logical Lines: {details['logical_lines']}",
                    f"Comment Lines: {details['comment_lines']}",
                ]
            )

            if "average_maintainability" in details:
                lines.append(f"Average Maintainability Index: {details['average_maintainability']}")

        if result.execution_time:
            lines.append(f"\nExecution Time: {result.execution_time:.2f}s")

        return "\n".join(lines)

    def _generate_detail_report(self, result: QualityResult) -> str:
        """Generate detailed complexity report."""
        lines = ["Most Complex Functions", "=" * 50, ""]

        functions = result.details.get("most_complex_functions", [])
        for i, func in enumerate(functions, 1):
            lines.extend(
                [
                    f"{i}. {func['name']} (Grade {func['rank']})",
                    f"   File: {func['file']}:{func['lineno']}",
                    f"   Complexity: {func['complexity']}",
                    "",
                ]
            )

        return "\n".join(lines)

    def report(self, result: QualityResult, format: str = "terminal") -> str:
        """Generate report from QualityResult (implements QualityTool protocol).

        Args:
            result: Complexity result
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
