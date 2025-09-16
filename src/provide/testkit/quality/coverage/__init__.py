"""Coverage analysis integration for provide-testkit.

Provides pytest fixtures and utilities for tracking code coverage during tests.
Integrates with the coverage.py library for comprehensive coverage analysis.

Features:
- Automatic coverage tracking during test runs
- Coverage reporting in multiple formats
- Integration with quality gates
- Artifact management for CI/CD

Usage:
    # Basic coverage tracking
    def test_with_coverage(coverage_tracker):
        result = coverage_tracker.start()
        # ... run tests
        coverage_tracker.stop()
        assert coverage_tracker.get_coverage() > 90

    # Session-wide coverage
    def test_example(session_coverage):
        # Coverage automatically tracked across all tests
        pass
"""

from .fixture import CoverageFixture, coverage_tracker, session_coverage
from .reporter import CoverageReporter
from .tracker import CoverageTracker

__all__ = [
    "CoverageFixture",
    "CoverageReporter",
    "CoverageTracker",
    "coverage_tracker",
    "session_coverage",
]
