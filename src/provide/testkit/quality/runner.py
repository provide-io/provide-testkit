"""Quality runner for orchestrating multiple quality tools."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

from provide.foundation.file import atomic_write_text, ensure_dir

from .base import QualityError, QualityResult, QualityTool


class QualityRunner:
    """Orchestrates multiple quality analysis tools.

    Manages the execution of quality tools, artifact collection,
    and result aggregation with configurable quality gates.
    """

    def __init__(
        self,
        artifact_root: Path | None = None,
        tools: list[str] | None = None,
        config: dict[str, Any] | None = None,
    ):
        """Initialize the quality runner.

        Args:
            artifact_root: Root directory for storing artifacts (defaults to .quality-artifacts)
            tools: List of tool names to run (None for default set)
            config: Configuration for tools and runner
        """
        self.artifact_root = Path(artifact_root) if artifact_root else Path(".quality-artifacts")
        self.config = config or {}
        self.tools = tools or self._get_default_tools()
        self.tool_instances: dict[str, QualityTool] = {}
        self._initialize_tools()

    def _get_default_tools(self) -> list[str]:
        """Get default set of quality tools."""
        return ["coverage", "security", "complexity"]

    def _initialize_tools(self) -> None:
        """Initialize quality tool instances based on configuration."""
        for tool_name in self.tools:
            try:
                self.tool_instances[tool_name] = self._create_tool(tool_name)
            except (ImportError, Exception) as e:
                # Tool dependencies not available - skip gracefully
                print(f"Warning: {tool_name} tool not available: {e}")
                continue

    def _create_tool(self, tool_name: str) -> QualityTool:
        """Create a tool instance by name."""
        if tool_name == "coverage":
            from .coverage import CoverageTracker

            return CoverageTracker(self.config.get("coverage", {}))
        elif tool_name == "security":
            from .security import SecurityScanner

            return SecurityScanner(self.config.get("security", {}))
        elif tool_name == "complexity":
            from .complexity import ComplexityAnalyzer

            return ComplexityAnalyzer(self.config.get("complexity", {}))
        elif tool_name == "profiling":
            from .profiling import PerformanceProfiler

            return PerformanceProfiler(self.config.get("profiling", {}))
        elif tool_name == "documentation":
            from .documentation import DocumentationChecker

            return DocumentationChecker(self.config.get("documentation", {}))
        else:
            raise QualityError(f"Unknown tool: {tool_name}")

    def run_all(self, target: Path, **kwargs: Any) -> dict[str, QualityResult]:
        """Run all configured quality tools on the target.

        Args:
            target: Path to analyze
            **kwargs: Additional arguments passed to tools

        Returns:
            Dictionary mapping tool names to their results
        """
        results = {}
        target = Path(target)

        for tool_name, tool in self.tool_instances.items():
            artifact_dir = self.artifact_root / tool_name
            ensure_dir(artifact_dir)

            try:
                start_time = time.time()
                result = tool.analyze(target, artifact_dir=artifact_dir, **kwargs)
                result.execution_time = time.time() - start_time

                # Save artifacts
                self._save_tool_artifacts(result, artifact_dir)
                results[tool_name] = result

            except Exception as e:
                # Create failed result for tool
                results[tool_name] = QualityResult(
                    tool=tool_name, passed=False, details={"error": str(e), "error_type": type(e).__name__}
                )

        return results

    def run_with_gates(
        self, target: Path, gates: dict[str, Any], **kwargs: Any
    ) -> tuple[bool, dict[str, QualityResult]]:
        """Run quality tools and check against quality gates.

        Args:
            target: Path to analyze
            gates: Quality gate requirements
            **kwargs: Additional arguments passed to tools

        Returns:
            Tuple of (all_gates_passed, results)
        """
        results = self.run_all(target, **kwargs)
        passed = self._check_gates(results, gates)
        return passed, results

    def _check_gates(self, results: dict[str, QualityResult], gates: dict[str, Any]) -> bool:
        """Check if results meet quality gate requirements.

        Args:
            results: Tool results to check
            gates: Gate requirements

        Returns:
            True if all gates pass
        """
        for gate_name, requirement in gates.items():
            if gate_name not in results:
                # Tool didn't run - gate fails
                return False

            result = results[gate_name]
            if not self._check_single_gate(result, requirement):
                return False

        return True

    def _check_single_gate(self, result: QualityResult, requirement: Any) -> bool:
        """Check a single gate requirement against a result.

        Args:
            result: Result to check
            requirement: Gate requirement to validate against

        Returns:
            True if gate requirement is met
        """
        if isinstance(requirement, dict):
            return self._check_dict_requirement(result, requirement)
        elif isinstance(requirement, bool):
            return self._check_bool_requirement(result, requirement)
        elif isinstance(requirement, (int, float)):
            return self._check_score_requirement(result, requirement)
        elif isinstance(requirement, str):
            return self._check_grade_requirement(result, requirement)
        else:
            return True

    def _check_dict_requirement(self, result: QualityResult, requirement: dict[str, Any]) -> bool:
        """Check dictionary-based gate requirements."""
        if not requirement.get("enabled", True):
            return True

        if not result.passed:
            return False

        if "min_score" in requirement and result.score is not None:
            return result.score >= requirement["min_score"]

        return True

    def _check_bool_requirement(self, result: QualityResult, requirement: bool) -> bool:
        """Check boolean gate requirements."""
        return not requirement or result.passed

    def _check_score_requirement(self, result: QualityResult, requirement: float) -> bool:
        """Check numeric score requirements."""
        return result.score is not None and result.score >= requirement

    def _check_grade_requirement(self, result: QualityResult, requirement: str) -> bool:
        """Check grade-based requirements (A, B, C, etc.).

        Args:
            result: Result to check
            requirement: Required grade

        Returns:
            True if requirement is met
        """
        if "grade" not in result.details:
            return False

        grade_order = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}
        actual_grade = result.details["grade"]
        required_grade = requirement

        return grade_order.get(actual_grade, 0) >= grade_order.get(required_grade, 0)

    def _save_tool_artifacts(self, result: QualityResult, artifact_dir: Path) -> None:
        """Save tool artifacts and update result.

        Args:
            result: Result to save artifacts for
            artifact_dir: Directory to save artifacts in
        """
        # Save result summary
        summary_file = artifact_dir / "summary.txt"
        atomic_write_text(summary_file, result.summary)
        result.artifacts.append(summary_file)

        # Save detailed results if available
        if result.details:
            import json

            details_file = artifact_dir / "details.json"
            atomic_write_text(details_file, json.dumps(result.details, indent=2, default=str))
            result.artifacts.append(details_file)

    def get_available_tools(self) -> list[str]:
        """Get list of available tool names."""
        return list(self.tool_instances.keys())

    def generate_summary_report(self, results: dict[str, QualityResult]) -> str:
        """Generate a summary report of all results.

        Args:
            results: Results to summarize

        Returns:
            Summary report string
        """
        lines = ["Quality Analysis Summary", "=" * 30, ""]

        total_tools = len(results)
        passed_tools = sum(1 for r in results.values() if r.passed)

        lines.append(f"Tools Run: {total_tools}")
        lines.append(f"Passed: {passed_tools}")
        lines.append(f"Failed: {total_tools - passed_tools}")
        lines.append("")

        for tool_name, result in results.items():
            lines.append(result.summary)

        return "\n".join(lines)

    def run_tools(
        self,
        target: Path,
        tools: list[str] | None = None,
        artifact_dir: Path | None = None,
        tool_configs: dict[str, Any] | None = None,
    ) -> dict[str, QualityResult]:
        """Run specific quality tools on the target.

        Args:
            target: Path to analyze
            tools: List of tool names to run (None for all available)
            artifact_dir: Directory for artifacts (overrides default)
            tool_configs: Configuration for tools

        Returns:
            Dictionary mapping tool names to their results
        """
        if artifact_dir:
            original_artifact_root = self.artifact_root
            self.artifact_root = artifact_dir

        if tool_configs:
            original_config = self.config
            self.config = tool_configs
            # Re-initialize tools with new config
            self._initialize_tools()

        # Filter tools if specified
        if tools:
            filtered_instances = {name: tool for name, tool in self.tool_instances.items() if name in tools}
            original_instances = self.tool_instances
            self.tool_instances = filtered_instances

        try:
            results = self.run_all(target)
            return results
        finally:
            # Restore original state
            if artifact_dir:
                self.artifact_root = original_artifact_root
            if tool_configs:
                self.config = original_config
                self._initialize_tools()
            if tools:
                self.tool_instances = original_instances


@dataclass
class QualityGateResults:
    """Results from running quality gates."""

    passed: bool
    results: dict[str, QualityResult]
    failed_gates: list[str] = None

    def __post_init__(self):
        if self.failed_gates is None:
            self.failed_gates = []
