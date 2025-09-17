"""Performance profiling and analysis for provide-testkit.

Provides performance profiling analysis using memray, cProfile, and other tools.
Integrates with the quality framework for comprehensive performance analysis.

Features:
- Memory profiling with memray
- CPU profiling with cProfile
- Performance regression detection
- Integration with quality gates
- Configurable profiling options

Usage:
    # Basic memory profiling
    def test_with_profiling(profiling_fixture):
        result = profiling_fixture.profile_memory(function, *args)
        assert result.passed

    # CPU profiling with quality gates
    runner = QualityRunner()
    results = runner.run_with_gates(path, {"profiling": {"max_memory_mb": 100}})
"""

from .fixture import ProfilingFixture
from .profiler import PerformanceProfiler

__all__ = [
    "PerformanceProfiler",
    "ProfilingFixture",
]
