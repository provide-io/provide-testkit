"""Performance profiling fixture for pytest integration."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from ..base import BaseQualityFixture

try:
    from .profiler import MEMRAY_AVAILABLE, PerformanceProfiler
except ImportError:
    PerformanceProfiler = None
    MEMRAY_AVAILABLE = False


class ProfilingFixture(BaseQualityFixture):
    """Pytest fixture for performance profiling.

    Provides easy access to performance profiling with automatic
    setup and teardown. Integrates with the quality framework fixtures.
    """

    def __init__(self, config: dict[str, Any] | None = None, artifact_dir: Path | None = None):
        """Initialize profiling fixture.

        Args:
            config: Profiler configuration
            artifact_dir: Directory for artifacts
        """
        super().__init__(config or {}, artifact_dir)
        self.profiler: PerformanceProfiler | None = None

    def setup(self) -> None:
        """Set up performance profiler."""
        self.profiler = PerformanceProfiler(self.config)
        self._setup_complete = True

    def profile_function(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Profile a function's performance.

        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Profiling results as dict
        """
        if not self.profiler:
            return {"error": "Profiler not available"}

        result = self.profiler.profile_function(func, *args, **kwargs)
        self.add_result(result)

        return {
            "passed": result.passed,
            "score": result.score,
            "memory": result.details.get("memory", {}),
            "cpu": result.details.get("cpu", {}),
            "scores": result.details.get("scores", {}),
            "thresholds": result.details.get("thresholds", {}),
            "execution_time": result.execution_time,
            "function_result": (
                result.details.get("memory", {}).get("function_result")
                or result.details.get("cpu", {}).get("function_result")
            ),
        }

    def profile_memory(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Profile memory usage only.

        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Memory profiling results
        """
        if not self._setup_complete:
            self.setup()

        # Configure for memory-only profiling
        original_config = self.config.copy()
        self.config.update({"profile_memory": True, "profile_cpu": False})

        # Recreate profiler with updated config
        self.profiler = PerformanceProfiler(self.config)

        try:
            return self.profile_function(func, *args, **kwargs)
        finally:
            # Restore original config
            self.config = original_config
            self.profiler = PerformanceProfiler(self.config)

    def profile_cpu(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Profile CPU usage only.

        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            CPU profiling results
        """
        if not self._setup_complete:
            self.setup()

        # Configure for CPU-only profiling
        original_config = self.config.copy()
        self.config.update({"profile_memory": False, "profile_cpu": True})

        # Recreate profiler with updated config
        self.profiler = PerformanceProfiler(self.config)

        try:
            return self.profile_function(func, *args, **kwargs)
        finally:
            # Restore original config
            self.config = original_config
            self.profiler = PerformanceProfiler(self.config)

    def benchmark_function(
        self, func: Callable[..., Any], iterations: int = 100, *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        """Benchmark a function over multiple iterations.

        Args:
            func: Function to benchmark
            iterations: Number of iterations to run
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Benchmark results with statistics
        """
        if not self._setup_complete:
            self.setup()

        import statistics

        execution_times = []
        memory_peaks = []

        for _ in range(iterations):
            result = self.profile_function(func, *args, **kwargs)

            if result.get("cpu", {}).get("execution_time"):
                execution_times.append(result["cpu"]["execution_time"])

            if result.get("memory", {}).get("peak_memory_mb"):
                memory_peaks.append(result["memory"]["peak_memory_mb"])

        # Calculate statistics
        benchmark_stats = {}

        if execution_times:
            benchmark_stats["execution_time"] = {
                "mean": statistics.mean(execution_times),
                "median": statistics.median(execution_times),
                "min": min(execution_times),
                "max": max(execution_times),
                "stdev": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                "iterations": len(execution_times),
            }

        if memory_peaks:
            benchmark_stats["memory_usage"] = {
                "mean_mb": statistics.mean(memory_peaks),
                "median_mb": statistics.median(memory_peaks),
                "min_mb": min(memory_peaks),
                "max_mb": max(memory_peaks),
                "stdev_mb": statistics.stdev(memory_peaks) if len(memory_peaks) > 1 else 0,
                "iterations": len(memory_peaks),
            }

        return {
            "benchmark_stats": benchmark_stats,
            "iterations": iterations,
            "total_profiling_runs": len(self.results),
        }

    def assert_performance(
        self,
        func: Callable[..., Any],
        max_memory_mb: float | None = None,
        max_execution_time: float | None = None,
        min_score: float | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Assert performance requirements for a function.

        Args:
            func: Function to test
            max_memory_mb: Maximum memory usage in MB
            max_execution_time: Maximum execution time in seconds
            min_score: Minimum performance score
            *args: Function arguments
            **kwargs: Function keyword arguments

        Raises:
            AssertionError: If performance requirements are not met
        """
        if not self._setup_complete:
            self.setup()

        # Update config with assertion requirements
        if max_memory_mb is not None:
            self.config["max_memory_mb"] = max_memory_mb
        if max_execution_time is not None:
            self.config["max_execution_time"] = max_execution_time
        if min_score is not None:
            self.config["min_score"] = min_score

        # Recreate profiler with updated config
        self.profiler = PerformanceProfiler(self.config)

        result = self.profile_function(func, *args, **kwargs)

        # Check assertions
        if not result["passed"]:
            failure_reasons = []

            if max_memory_mb and result.get("memory", {}).get("peak_memory_mb", 0) > max_memory_mb:
                actual_mb = result["memory"]["peak_memory_mb"]
                failure_reasons.append(f"Memory usage {actual_mb:.2f}MB exceeds limit {max_memory_mb}MB")

            if max_execution_time and result.get("cpu", {}).get("execution_time", 0) > max_execution_time:
                actual_time = result["cpu"]["execution_time"]
                failure_reasons.append(
                    f"Execution time {actual_time:.4f}s exceeds limit {max_execution_time}s"
                )

            if min_score and result.get("score", 0) < min_score:
                actual_score = result["score"]
                failure_reasons.append(f"Performance score {actual_score:.1f}% below minimum {min_score}%")

            raise AssertionError(f"Performance requirements not met: {'; '.join(failure_reasons)}")

    def generate_report(self, format: str = "terminal") -> str:
        """Generate profiling report.

        Args:
            format: Report format (terminal, json)

        Returns:
            Formatted report
        """
        if not self.profiler:
            return "No performance profiler available"

        if not self.results:
            return "No profiling results available"

        # Use the most recent result
        latest_result = self.results[-1]
        return self.profiler.report(latest_result, format)


@pytest.fixture
def profiling_fixture() -> ProfilingFixture:
    """Provide performance profiling fixture.

    Returns:
        ProfilingFixture instance
    """
    fixture = ProfilingFixture()
    fixture.setup()
    yield fixture
    fixture.teardown()


@pytest.fixture
def profiling_config() -> dict[str, Any]:
    """Provide default profiling configuration.

    Returns:
        Default configuration for profiling
    """
    return {
        "profile_memory": True,
        "profile_cpu": True,
        "use_memray": MEMRAY_AVAILABLE,
        "min_score": 70.0,
        "max_memory_mb": 100.0,
        "max_execution_time": 1.0,
    }


@pytest.fixture
def memory_profiler(profiling_config: dict[str, Any]) -> ProfilingFixture:
    """Provide memory-only profiling fixture.

    Args:
        profiling_config: Base configuration

    Returns:
        ProfilingFixture configured for memory profiling only
    """
    config = profiling_config.copy()
    config.update({"profile_memory": True, "profile_cpu": False})

    fixture = ProfilingFixture(config)
    fixture.setup()
    yield fixture
    fixture.teardown()


@pytest.fixture
def cpu_profiler(profiling_config: dict[str, Any]) -> ProfilingFixture:
    """Provide CPU-only profiling fixture.

    Args:
        profiling_config: Base configuration

    Returns:
        ProfilingFixture configured for CPU profiling only
    """
    config = profiling_config.copy()
    config.update({"profile_memory": False, "profile_cpu": True})

    fixture = ProfilingFixture(config)
    fixture.setup()
    yield fixture
    fixture.teardown()
