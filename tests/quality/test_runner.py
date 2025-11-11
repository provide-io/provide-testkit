#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for quality runner orchestration."""

import json
from pathlib import Path
from typing import Any

from provide.testkit.mocking import Mock, patch  # type: ignore[import-untyped]
from provide.testkit.quality.base import QualityResult  # type: ignore[import-untyped]
from provide.testkit.quality.runner import QualityRunner  # type: ignore[import-untyped]


class MockQualityTool:
    """Mock quality tool for testing."""

    def __init__(self, name: str, should_pass: bool = True, score: float | None = None) -> None:
        self.name = name
        self.should_pass = should_pass
        self.score = score
        self.analyze_calls: list[tuple[Path, dict[str, Any]]] = []

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        self.analyze_calls.append((path, kwargs))
        return QualityResult(tool=self.name, passed=self.should_pass, score=self.score, details={"mock": True})

    def report(self, result: QualityResult, format: str = "terminal") -> str:
        return f"{self.name} report for {result.tool}"


class TestQualityRunner:
    """Test QualityRunner orchestration."""

    def test_initialization_default_tools(self, tmp_path: Path) -> None:
        """Test runner initialization with default tools."""
        with patch.object(QualityRunner, "_initialize_tools"):
            runner = QualityRunner(artifact_root=tmp_path)

        assert runner.artifact_root == tmp_path
        assert runner.tools == ["coverage", "security", "complexity"]
        assert runner.config == {}

    def test_initialization_custom_tools(self, tmp_path: Path) -> None:
        """Test runner initialization with custom tools."""
        tools = ["security", "complexity"]
        config = {"security": {"level": "high"}}

        with patch.object(QualityRunner, "_initialize_tools"):
            runner = QualityRunner(artifact_root=tmp_path, tools=tools, config=config)

        assert runner.tools == tools
        assert runner.config == config

    def test_run_all_success(self, tmp_path: Path) -> None:
        """Test running all tools successfully."""
        runner = QualityRunner(artifact_root=tmp_path, tools=[])

        # Mock tools
        tool1 = MockQualityTool("tool1", should_pass=True, score=95.0)
        tool2 = MockQualityTool("tool2", should_pass=True, score=88.5)
        runner.tool_instances = {"tool1": tool1, "tool2": tool2}

        target = tmp_path / "src"
        target.mkdir()

        results = runner.run_all(target, extra_arg="test")

        # Check results
        assert len(results) == 2
        assert "tool1" in results
        assert "tool2" in results

        # Check tool1 result
        result1 = results["tool1"]
        assert result1.tool == "tool1"
        assert result1.passed is True
        assert result1.score == 95.0
        assert result1.execution_time is not None

        # Check that tools were called correctly
        assert len(tool1.analyze_calls) == 1
        call_path, call_kwargs = tool1.analyze_calls[0]
        assert call_path == target
        assert call_kwargs["extra_arg"] == "test"
        assert "artifact_dir" in call_kwargs

        # Check artifacts were saved
        assert len(result1.artifacts) >= 1
        summary_file = tmp_path / "tool1" / "summary.txt"
        assert summary_file.exists()

    def test_run_all_with_tool_failure(self, tmp_path: Path) -> None:
        """Test running tools when one fails."""
        runner = QualityRunner(artifact_root=tmp_path, tools=[])

        # Mock tools - one that passes, one that raises exception
        good_tool = MockQualityTool("good", should_pass=True)
        bad_tool = Mock()
        bad_tool.analyze.side_effect = RuntimeError("Tool crashed")

        runner.tool_instances = {"good": good_tool, "bad": bad_tool}

        target = tmp_path / "src"
        target.mkdir()

        results = runner.run_all(target)

        # Check results
        assert len(results) == 2
        assert results["good"].passed is True
        assert results["bad"].passed is False
        assert "error" in results["bad"].details
        assert results["bad"].details["error"] == "Tool crashed"

    def test_run_with_gates_all_pass(self, tmp_path: Path) -> None:
        """Test running with quality gates that all pass."""
        runner = QualityRunner(artifact_root=tmp_path, tools=[])

        # Mock tools
        coverage_tool = MockQualityTool("coverage", should_pass=True, score=95.0)
        security_tool = MockQualityTool("security", should_pass=True)
        runner.tool_instances = {"coverage": coverage_tool, "security": security_tool}

        target = tmp_path / "src"
        target.mkdir()

        gates = {
            "coverage": 90.0,  # Score requirement
            "security": True,  # Must pass
        }

        passed, results = runner.run_with_gates(target, gates)

        assert passed is True
        assert len(results) == 2

    def test_run_with_gates_score_failure(self, tmp_path: Path) -> None:
        """Test running with quality gates where score fails."""
        runner = QualityRunner(artifact_root=tmp_path, tools=[])

        # Mock tool with low score
        coverage_tool = MockQualityTool("coverage", should_pass=True, score=85.0)
        runner.tool_instances = {"coverage": coverage_tool}

        target = tmp_path / "src"
        target.mkdir()

        gates = {"coverage": 90.0}  # Requires 90%, but tool returns 85%

        passed, results = runner.run_with_gates(target, gates)

        assert passed is False
        assert results["coverage"].score == 85.0

    def test_run_with_gates_complex_requirements(self, tmp_path: Path) -> None:
        """Test running with complex gate requirements."""
        runner = QualityRunner(artifact_root=tmp_path, tools=[])

        # Mock tools
        coverage_tool = MockQualityTool("coverage", should_pass=True, score=95.0)
        security_tool = MockQualityTool("security", should_pass=True)
        runner.tool_instances = {"coverage": coverage_tool, "security": security_tool}

        target = tmp_path / "src"
        target.mkdir()

        gates = {"coverage": {"enabled": True, "min_score": 90.0}, "security": {"enabled": True}}

        passed, results = runner.run_with_gates(target, gates)

        assert passed is True
        assert set(results) == {"coverage", "security"}

    def test_check_grade_requirement(self, tmp_path: Path) -> None:
        """Test grade-based requirement checking."""
        runner = QualityRunner(artifact_root=tmp_path, tools=[])

        # Result with grade A
        result_a = QualityResult(tool="test", passed=True, details={"grade": "A"})
        assert runner._check_grade_requirement(result_a, "A") is True
        assert runner._check_grade_requirement(result_a, "B") is True
        assert runner._check_grade_requirement(result_a, "C") is True

        # Result with grade C
        result_c = QualityResult(tool="test", passed=True, details={"grade": "C"})
        assert runner._check_grade_requirement(result_c, "A") is False
        assert runner._check_grade_requirement(result_c, "B") is False
        assert runner._check_grade_requirement(result_c, "C") is True
        assert runner._check_grade_requirement(result_c, "D") is True

        # Result without grade
        result_no_grade = QualityResult(tool="test", passed=True)
        assert runner._check_grade_requirement(result_no_grade, "A") is False

    def test_save_tool_artifacts(self, tmp_path: Path) -> None:
        """Test artifact saving functionality."""
        runner = QualityRunner(artifact_root=tmp_path, tools=[])

        result = QualityResult(tool="test", passed=True, score=95.0, details={"issues": 2, "lines": 100})

        artifact_dir = tmp_path / "test"
        artifact_dir.mkdir()

        runner._save_tool_artifacts(result, artifact_dir)

        # Check summary file
        summary_file = artifact_dir / "summary.txt"
        assert summary_file.exists()

        # Check details file
        details_file = artifact_dir / "details.json"
        assert details_file.exists()
        details_data = json.loads(details_file.read_text())
        assert details_data["issues"] == 2
        assert details_data["lines"] == 100

        # Check artifacts were added to result
        assert summary_file in result.artifacts
        assert details_file in result.artifacts

    def test_generate_summary_report(self, tmp_path: Path) -> None:
        """Test summary report generation."""
        runner = QualityRunner(artifact_root=tmp_path, tools=[])

        results = {
            "coverage": QualityResult(tool="coverage", passed=True, score=95.0),
            "security": QualityResult(tool="security", passed=False),
            "complexity": QualityResult(tool="complexity", passed=True, score=88.0),
        }

        report = runner.generate_summary_report(results)

        assert "Quality Analysis Summary" in report
        assert "Tools Run: 3" in report
        assert "Passed: 2" in report
        assert "Failed: 1" in report
        assert "security: ❌ FAILED" in report

    def test_get_available_tools(self, tmp_path: Path) -> None:
        """Test getting available tools."""
        runner = QualityRunner(artifact_root=tmp_path, tools=[])

        tool1 = MockQualityTool("tool1")
        tool2 = MockQualityTool("tool2")
        runner.tool_instances = {"tool1": tool1, "tool2": tool2}

        available = runner.get_available_tools()
        assert set(available) == {"tool1", "tool2"}


# 🧪✅🔚
