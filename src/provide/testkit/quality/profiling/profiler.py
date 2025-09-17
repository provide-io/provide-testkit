"""Performance profiling implementation using memray and cProfile."""

from __future__ import annotations

from collections.abc import Callable
import cProfile
from io import StringIO
import json
from pathlib import Path
import pstats
import time
import tracemalloc
from typing import Any

from provide.foundation.file import temp_file

try:
    import memray

    MEMRAY_AVAILABLE = True
except ImportError:
    MEMRAY_AVAILABLE = False
    memray = None

from ..base import QualityResult, QualityToolError


class PerformanceProfiler:
    """Performance profiler using memray, cProfile, and tracemalloc.

    Provides high-level interface for performance analysis with automatic
    artifact management and integration with the quality framework.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize performance profiler.

        Args:
            config: Profiler configuration options
        """
        self.config = config or {}
        self.artifact_dir: Path | None = None

    def profile_function(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> QualityResult:
        """Profile a function's performance.

        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            QualityResult with profiling data
        """
        start_time = time.time()

        try:
            # Configure profiling options
            profile_memory = self.config.get("profile_memory", True)
            profile_cpu = self.config.get("profile_cpu", True)
            use_memray = self.config.get("use_memray", MEMRAY_AVAILABLE)

            results = {}

            # Memory profiling
            if profile_memory:
                if use_memray and MEMRAY_AVAILABLE:
                    memory_result = self._profile_memory_memray(func, *args, **kwargs)
                else:
                    memory_result = self._profile_memory_tracemalloc(func, *args, **kwargs)
                results.update(memory_result)

            # CPU profiling
            if profile_cpu:
                cpu_result = self._profile_cpu(func, *args, **kwargs)
                results.update(cpu_result)

            # Analyze results
            return self._process_profiling_results(results, time.time() - start_time)

        except Exception as e:
            return QualityResult(
                tool="profiling",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def _profile_memory_memray(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Profile memory usage using memray."""
        if not MEMRAY_AVAILABLE:
            raise QualityToolError("Memray not available", tool="profiling")

        with temp_file(suffix=".bin", cleanup=False) as output_path:
            try:
                # Run function with memray profiling
                with memray.Tracker(output_path):
                    result = func(*args, **kwargs)

                # Generate basic statistics
                stats = memray.FileReader(output_path).get_memory_snapshots()
                if stats:
                    peak_memory = max(snapshot.heap_size for snapshot in stats)
                    avg_memory = sum(snapshot.heap_size for snapshot in stats) / len(stats)
                else:
                    peak_memory = 0
                    avg_memory = 0

                return {
                    "memory_profiling": {
                        "tool": "memray",
                        "peak_memory_bytes": peak_memory,
                        "average_memory_bytes": avg_memory,
                        "peak_memory_mb": peak_memory / (1024 * 1024),
                        "average_memory_mb": avg_memory / (1024 * 1024),
                        "profile_file": str(output_path),
                        "function_result": result,
                    }
                }

            finally:
                # Clean up temp file
                if output_path.exists():
                    output_path.unlink()

    def _profile_memory_tracemalloc(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        """Profile memory usage using tracemalloc."""
        tracemalloc.start()

        try:
            # Take initial snapshot
            snapshot1 = tracemalloc.take_snapshot()

            # Run function
            result = func(*args, **kwargs)

            # Take final snapshot
            snapshot2 = tracemalloc.take_snapshot()

            # Calculate memory usage
            current, peak = tracemalloc.get_traced_memory()
            top_stats = snapshot2.compare_to(snapshot1, "lineno")

            # Get top memory allocations
            top_allocations = []
            for stat in top_stats[:10]:  # Top 10 allocations
                top_allocations.append(
                    {
                        "file": stat.traceback.format()[0] if stat.traceback.format() else "unknown",
                        "size_bytes": stat.size,
                        "size_mb": stat.size / (1024 * 1024),
                        "count": stat.count,
                    }
                )

            return {
                "memory_profiling": {
                    "tool": "tracemalloc",
                    "current_memory_bytes": current,
                    "peak_memory_bytes": peak,
                    "current_memory_mb": current / (1024 * 1024),
                    "peak_memory_mb": peak / (1024 * 1024),
                    "top_allocations": top_allocations,
                    "function_result": result,
                }
            }

        finally:
            tracemalloc.stop()

    def _profile_cpu(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Profile CPU usage using cProfile."""
        profiler = cProfile.Profile()

        # Profile function execution
        profiler.enable()
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        profiler.disable()

        # Generate statistics
        stats_stream = StringIO()
        stats = pstats.Stats(profiler, stream=stats_stream)
        stats.sort_stats("cumulative")

        # Get top functions by cumulative time
        top_functions = []
        for func_info, (cc, nc, tt, ct, callers) in stats.stats.items():
            filename, line, func_name = func_info
            top_functions.append(
                {
                    "function": f"{filename}:{line}({func_name})",
                    "call_count": nc,
                    "total_time": tt,
                    "cumulative_time": ct,
                    "time_per_call": tt / nc if nc > 0 else 0,
                }
            )

        # Sort by cumulative time and take top 10
        top_functions.sort(key=lambda x: x["cumulative_time"], reverse=True)

        return {
            "cpu_profiling": {
                "tool": "cProfile",
                "execution_time": end_time - start_time,
                "total_function_calls": stats.total_calls,
                "primitive_calls": stats.prim_calls,
                "top_functions": top_functions[:10],
                "function_result": result,
            }
        }

    def _process_profiling_results(self, results: dict[str, Any], execution_time: float) -> QualityResult:
        """Process profiling results into QualityResult."""

        # Extract key metrics
        memory_data = results.get("memory_profiling", {})
        cpu_data = results.get("cpu_profiling", {})

        # Calculate scores based on thresholds
        memory_score = self._calculate_memory_score(memory_data)
        cpu_score = self._calculate_cpu_score(cpu_data)

        # Overall score is average of component scores
        overall_score = (
            (memory_score + cpu_score) / 2 if memory_score and cpu_score else (memory_score or cpu_score or 0)
        )

        # Determine pass/fail
        min_score = self.config.get("min_score", 70.0)
        max_memory_mb = self.config.get("max_memory_mb")
        max_execution_time = self.config.get("max_execution_time")

        passed = overall_score >= min_score

        # Check hard limits
        if max_memory_mb and memory_data:
            peak_mb = memory_data.get("peak_memory_mb", 0)
            if peak_mb > max_memory_mb:
                passed = False

        if max_execution_time and cpu_data:
            exec_time = cpu_data.get("execution_time", 0)
            if exec_time > max_execution_time:
                passed = False

        # Create detailed results
        details = {
            "memory": memory_data,
            "cpu": cpu_data,
            "scores": {"memory_score": memory_score, "cpu_score": cpu_score, "overall_score": overall_score},
            "thresholds": {
                "min_score": min_score,
                "max_memory_mb": max_memory_mb,
                "max_execution_time": max_execution_time,
            },
        }

        return QualityResult(
            tool="profiling",
            passed=passed,
            score=overall_score,
            details=details,
            execution_time=execution_time,
        )

    def _calculate_memory_score(self, memory_data: dict[str, Any]) -> float | None:
        """Calculate memory efficiency score."""
        if not memory_data:
            return None

        peak_mb = memory_data.get("peak_memory_mb", 0)

        # Score based on memory usage (lower is better)
        if peak_mb <= 10:  # Very efficient
            return 100.0
        elif peak_mb <= 50:  # Good
            return 90.0
        elif peak_mb <= 100:  # Acceptable
            return 80.0
        elif peak_mb <= 200:  # Poor
            return 60.0
        elif peak_mb <= 500:  # Very poor
            return 40.0
        else:  # Unacceptable
            return 20.0

    def _calculate_cpu_score(self, cpu_data: dict[str, Any]) -> float | None:
        """Calculate CPU efficiency score."""
        if not cpu_data:
            return None

        exec_time = cpu_data.get("execution_time", 0)

        # Score based on execution time (lower is better)
        if exec_time <= 0.1:  # Very fast
            return 100.0
        elif exec_time <= 0.5:  # Fast
            return 90.0
        elif exec_time <= 1.0:  # Acceptable
            return 80.0
        elif exec_time <= 2.0:  # Slow
            return 60.0
        elif exec_time <= 5.0:  # Very slow
            return 40.0
        else:  # Unacceptable
            return 20.0

    def generate_report(self, result: QualityResult, format: str = "terminal") -> str:
        """Generate profiling report.

        Args:
            result: Profiling result
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

    def _generate_text_report(self, result: QualityResult) -> str:
        """Generate text profiling report."""
        lines = [
            f"Performance Profiling Report - {result.tool}",
            "=" * 50,
            f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}",
            f"Overall Score: {result.score:.1f}%",
        ]

        details = result.details
        scores = details.get("scores", {})

        if scores:
            lines.extend(
                [
                    "",
                    "Component Scores:",
                    f"  Memory Score: {scores.get('memory_score', 'N/A')}%",
                    f"  CPU Score: {scores.get('cpu_score', 'N/A')}%",
                ]
            )

        # Memory analysis
        memory_data = details.get("memory", {})
        if memory_data:
            lines.extend(
                [
                    "",
                    f"Memory Analysis ({memory_data.get('tool', 'unknown')}):",
                    f"  Peak Memory: {memory_data.get('peak_memory_mb', 0):.2f} MB",
                ]
            )

            if "average_memory_mb" in memory_data:
                lines.append(f"  Average Memory: {memory_data['average_memory_mb']:.2f} MB")

        # CPU analysis
        cpu_data = details.get("cpu", {})
        if cpu_data:
            lines.extend(
                [
                    "",
                    f"CPU Analysis ({cpu_data.get('tool', 'unknown')}):",
                    f"  Execution Time: {cpu_data.get('execution_time', 0):.4f}s",
                    f"  Total Function Calls: {cpu_data.get('total_function_calls', 0):,}",
                ]
            )

            top_functions = cpu_data.get("top_functions", [])
            if top_functions:
                lines.extend(
                    [
                        "",
                        "Top CPU Consumers:",
                    ]
                )
                for i, func in enumerate(top_functions[:5], 1):
                    lines.append(f"  {i}. {func['function']} ({func['cumulative_time']:.4f}s)")

        # Thresholds
        thresholds = details.get("thresholds", {})
        if thresholds:
            lines.extend(
                [
                    "",
                    "Thresholds:",
                    f"  Minimum Score: {thresholds.get('min_score', 'N/A')}%",
                ]
            )

            if thresholds.get("max_memory_mb"):
                lines.append(f"  Maximum Memory: {thresholds['max_memory_mb']} MB")
            if thresholds.get("max_execution_time"):
                lines.append(f"  Maximum Execution Time: {thresholds['max_execution_time']}s")

        if result.execution_time:
            lines.append(f"\nProfiling Time: {result.execution_time:.2f}s")

        return "\n".join(lines)

    def report(self, result: QualityResult, format: str = "terminal") -> str:
        """Generate report from QualityResult (implements QualityTool protocol).

        Args:
            result: Profiling result
            format: Report format

        Returns:
            Formatted report
        """
        return self.generate_report(result, format)
