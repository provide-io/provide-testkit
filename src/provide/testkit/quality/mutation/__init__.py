"""Mutation testing integration for provide-testkit.

Provides pytest fixtures and utilities for mutation testing with mutmut.
Integrates mutation testing into the provide quality analysis framework.

Features:
- Module-priority based mutation testing
- Git integration for changed-file mutation
- Historical mutation score tracking
- Multiple report formats (terminal, HTML, JSON, markdown)
- Integration with quality gates and CI/CD

Usage:
    # Basic mutation testing
    def test_with_mutations(mutation_runner):
        result = mutation_runner.analyze(Path("src/mymodule"))
        assert result.score >= 80

    # Test only changed files
    def test_changed_mutations(mutation_runner):
        result = mutation_runner.run_changed_files()
        assert result.passed

    # Module-specific mutation testing
    def test_security_mutations(mutation_runner):
        result = mutation_runner.run_module("src/security.py", target_score=100)
        assert result.passed
"""

from __future__ import annotations

from .config import ModulePriority, MutationConfig
from .fixture import MutationFixture, mutation_runner, session_mutation
from .reporter import MutationReporter
from .runner import MutationRunner
from .tracker import MutationTracker

__all__ = [
    "ModulePriority",
    "MutationConfig",
    "MutationFixture",
    "MutationReporter",
    "MutationRunner",
    "MutationTracker",
    "mutation_runner",
    "session_mutation",
]
