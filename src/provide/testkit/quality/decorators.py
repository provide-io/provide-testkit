"""Quality decorators for easy integration of quality checks."""

from __future__ import annotations

from collections.abc import Callable
import functools
import inspect
from pathlib import Path
from typing import Any, TypeVar

from .runner import QualityRunner

F = TypeVar("F", bound=Callable[..., Any])


def quality_gate(
    gates: dict[str, Any],
    path: Path | str | None = None,
    artifact_dir: Path | str | None = None,
    fail_fast: bool = True,
) -> Callable[[F], F]:
    """Decorator to apply quality gates to a function or test.

    Args:
        gates: Quality gate requirements
        path: Path to analyze (defaults to function's module file)
        artifact_dir: Directory for artifacts
        fail_fast: Whether to stop on first failure

    Returns:
        Decorated function

    Example:
        @quality_gate({"coverage": 80.0, "security": True})
        def test_my_function():
            # Test implementation
            pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Determine path to analyze
            if path is None:
                # Use the module file containing the decorated function
                module = inspect.getmodule(func)
                if module and module.__file__:
                    analysis_path = Path(module.__file__).parent
                else:
                    raise ValueError("Could not determine path to analyze")
            else:
                analysis_path = Path(path)

            # Run quality gates
            runner = QualityRunner()
            results = runner.run_with_gates(
                analysis_path,
                gates,
                artifact_dir=Path(artifact_dir) if artifact_dir else None,
                fail_fast=fail_fast,
            )

            # Check if gates passed
            if not results.passed:
                failed_tools = [tool for tool, result in results.results.items() if not result.passed]
                raise AssertionError(f"Quality gates failed for tools: {failed_tools}")

            # Execute original function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def coverage_gate(
    min_coverage: float, path: Path | str | None = None, artifact_dir: Path | str | None = None
) -> Callable[[F], F]:
    """Decorator to enforce minimum coverage requirements.

    Args:
        min_coverage: Minimum coverage percentage required
        path: Path to analyze
        artifact_dir: Directory for artifacts

    Returns:
        Decorated function

    Example:
        @coverage_gate(80.0)
        def test_my_function():
            # Test implementation
            pass
    """
    return quality_gate({"coverage": min_coverage}, path, artifact_dir)


def security_gate(
    min_score: float = 90.0, path: Path | str | None = None, artifact_dir: Path | str | None = None
) -> Callable[[F], F]:
    """Decorator to enforce security scanning requirements.

    Args:
        min_score: Minimum security score required
        path: Path to analyze
        artifact_dir: Directory for artifacts

    Returns:
        Decorated function

    Example:
        @security_gate(95.0)
        def test_my_function():
            # Test implementation
            pass
    """
    return quality_gate({"security": min_score}, path, artifact_dir)


def complexity_gate(
    max_complexity: int | None = None,
    min_grade: str | None = None,
    min_score: float | None = None,
    path: Path | str | None = None,
    artifact_dir: Path | str | None = None,
) -> Callable[[F], F]:
    """Decorator to enforce complexity requirements.

    Args:
        max_complexity: Maximum complexity allowed
        min_grade: Minimum complexity grade required
        min_score: Minimum complexity score required
        path: Path to analyze
        artifact_dir: Directory for artifacts

    Returns:
        Decorated function

    Example:
        @complexity_gate(max_complexity=10, min_grade="B")
        def test_my_function():
            # Test implementation
            pass
    """
    gate_config: dict[str, Any] = {}

    if max_complexity is not None:
        gate_config["max_complexity"] = max_complexity
    if min_grade is not None:
        gate_config["min_grade"] = min_grade
    if min_score is not None:
        gate_config["min_score"] = min_score

    if not gate_config:
        gate_config = True  # Use default requirements

    return quality_gate({"complexity": gate_config}, path, artifact_dir)


def documentation_gate(
    min_coverage: float | None = None,
    min_grade: str | None = None,
    min_score: float | None = None,
    path: Path | str | None = None,
    artifact_dir: Path | str | None = None,
) -> Callable[[F], F]:
    """Decorator to enforce documentation requirements.

    Args:
        min_coverage: Minimum documentation coverage percentage
        min_grade: Minimum documentation grade required
        min_score: Minimum documentation score required
        path: Path to analyze
        artifact_dir: Directory for artifacts

    Returns:
        Decorated function

    Example:
        @documentation_gate(min_coverage=80.0, min_grade="B")
        def test_my_function():
            # Test implementation
            pass
    """
    gate_config: dict[str, Any] = {}

    if min_coverage is not None:
        gate_config["min_coverage"] = min_coverage
    if min_grade is not None:
        gate_config["min_grade"] = min_grade
    if min_score is not None:
        gate_config["min_score"] = min_score

    if not gate_config:
        gate_config = True  # Use default requirements

    return quality_gate({"documentation": gate_config}, path, artifact_dir)


def performance_gate(
    max_memory_mb: float | None = None, max_execution_time: float | None = None, min_score: float | None = None
) -> Callable[[F], F]:
    """Decorator to enforce performance requirements on function execution.

    Args:
        max_memory_mb: Maximum memory usage in MB
        max_execution_time: Maximum execution time in seconds
        min_score: Minimum performance score

    Returns:
        Decorated function

    Example:
        @performance_gate(max_memory_mb=50.0, max_execution_time=1.0)
        def test_my_function():
            # Test implementation
            pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Configure and run profiler
            profiler = _create_performance_profiler(max_memory_mb, max_execution_time, min_score)
            result = profiler.profile_function(lambda: func(*args, **kwargs))

            # Check requirements and handle failures
            _validate_performance_requirements(result, max_memory_mb, max_execution_time, min_score)

            # Extract and return the actual function result
            return _extract_function_result(result)

        return wrapper

    return decorator


def _create_performance_profiler(
    max_memory_mb: float | None, max_execution_time: float | None, min_score: float | None
) -> Any:
    """Create and configure a performance profiler."""
    from .profiling.profiler import PerformanceProfiler

    config = {"profile_memory": True, "profile_cpu": True}

    if max_memory_mb is not None:
        config["max_memory_mb"] = max_memory_mb
    if max_execution_time is not None:
        config["max_execution_time"] = max_execution_time
    if min_score is not None:
        config["min_score"] = min_score

    return PerformanceProfiler(config)


def _validate_performance_requirements(
    result: Any, max_memory_mb: float | None, max_execution_time: float | None, min_score: float | None
) -> None:
    """Validate performance requirements and raise error if not met."""
    if result.passed:
        return

    failure_reasons = []
    memory_data = result.details.get("memory", {})
    cpu_data = result.details.get("cpu", {})

    # Check memory requirement
    if max_memory_mb and memory_data.get("peak_memory_mb", 0) > max_memory_mb:
        actual_mb = memory_data["peak_memory_mb"]
        failure_reasons.append(f"Memory usage {actual_mb:.2f}MB exceeds limit {max_memory_mb}MB")

    # Check execution time requirement
    if max_execution_time and cpu_data.get("execution_time", 0) > max_execution_time:
        actual_time = cpu_data["execution_time"]
        failure_reasons.append(f"Execution time {actual_time:.4f}s exceeds limit {max_execution_time}s")

    # Check score requirement
    if min_score and result.score < min_score:
        failure_reasons.append(f"Performance score {result.score:.1f}% below minimum {min_score}%")

    raise AssertionError(f"Performance requirements not met: {'; '.join(failure_reasons)}")


def _extract_function_result(result: Any) -> Any:
    """Extract the actual function result from profiling data."""
    return result.details.get("memory", {}).get("function_result") or result.details.get("cpu", {}).get(
        "function_result"
    )


def quality_check(
    coverage: float | bool | None = None,
    security: float | bool | None = None,
    complexity: dict[str, Any] | bool | None = None,
    documentation: dict[str, Any] | bool | None = None,
    performance: dict[str, Any] | None = None,
    path: Path | str | None = None,
    artifact_dir: Path | str | None = None,
    fail_fast: bool = True,
) -> Callable[[F], F]:
    """Comprehensive quality check decorator with multiple dimensions.

    Args:
        coverage: Coverage requirements (percentage or boolean)
        security: Security requirements (score or boolean)
        complexity: Complexity requirements (config dict or boolean)
        documentation: Documentation requirements (config dict or boolean)
        performance: Performance requirements (config dict)
        path: Path to analyze
        artifact_dir: Directory for artifacts
        fail_fast: Whether to stop on first failure

    Returns:
        Decorated function

    Example:
        @quality_check(
            coverage=80.0,
            security=True,
            complexity={"max_complexity": 10, "min_grade": "B"},
            documentation={"min_coverage": 80.0},
            performance={"max_memory_mb": 50.0}
        )
        def test_my_function():
            # Test implementation
            pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build gates configuration
            gates = {}

            if coverage is not None:
                gates["coverage"] = coverage

            if security is not None:
                gates["security"] = security

            if complexity is not None:
                gates["complexity"] = complexity

            if documentation is not None:
                gates["documentation"] = documentation

            # Handle performance separately since it profiles the function execution
            if performance is not None:
                # Apply performance gate to the function
                perf_decorator = performance_gate(
                    max_memory_mb=performance.get("max_memory_mb"),
                    max_execution_time=performance.get("max_execution_time"),
                    min_score=performance.get("min_score"),
                )
                func_with_perf = perf_decorator(func)
            else:
                func_with_perf = func

            # Apply quality gates if any are specified
            if gates:
                gate_decorator = quality_gate(gates, path, artifact_dir, fail_fast)
                func_with_gates = gate_decorator(func_with_perf)
            else:
                func_with_gates = func_with_perf

            # Execute the decorated function
            return func_with_gates(*args, **kwargs)

        return wrapper

    return decorator


# Convenience aliases
coverage_required = coverage_gate
security_required = security_gate
complexity_required = complexity_gate
documentation_required = documentation_gate
performance_required = performance_gate
quality_required = quality_check
