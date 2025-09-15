"""
Code quality analysis utilities for the provide testkit.

This module provides pytest fixtures and utilities for integrating code quality
tools into testing workflows. All quality tools are optional and only activated
when explicitly requested.

Key Features:
- Coverage tracking and reporting
- Security scanning with Bandit
- Complexity analysis with Radon
- Performance profiling with py-spy
- Documentation coverage with Interrogate

Usage:
    # Basic quality fixture
    def test_with_coverage(quality_coverage):
        result = quality_coverage.track_coverage()

    # Quality decorator
    @quality_check(coverage=90, security=True)
    def test_with_gates():
        pass

    # CLI usage
    provide-testkit quality analyze src/
"""

# Core exports
from .base import QualityResult, QualityTool, BaseQualityFixture
from .runner import QualityRunner
from .report import ReportGenerator

# Lazy imports for performance - only import when used
__all__ = [
    "QualityResult",
    "QualityTool",
    "BaseQualityFixture",
    "QualityRunner",
    "ReportGenerator",
]

def __getattr__(name: str):
    """Lazy import quality tools to avoid import overhead."""
    if name == "CoverageFixture":
        from .coverage import CoverageFixture
        return CoverageFixture
    elif name == "SecurityFixture":
        from .security import SecurityFixture
        return SecurityFixture
    elif name == "ComplexityFixture":
        from .complexity import ComplexityFixture
        return ComplexityFixture
    elif name == "ProfilingFixture":
        from .profiling import ProfilingFixture
        return ProfilingFixture
    elif name == "DocumentationFixture":
        from .documentation import DocumentationFixture
        return DocumentationFixture

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")