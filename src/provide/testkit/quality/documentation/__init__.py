"""Documentation coverage analysis for provide-testkit.

Provides documentation coverage analysis using interrogate and other tools.
Integrates with the quality framework for comprehensive docstring analysis.

Features:
- Docstring coverage analysis with interrogate
- Module, class, and function documentation checking
- Integration with quality gates
- Configurable exclusions and requirements

Usage:
    # Basic documentation coverage
    def test_with_docs(documentation_checker):
        result = documentation_checker.check(path)
        assert result.passed

    # Documentation with quality gates
    runner = QualityRunner()
    results = runner.run_with_gates(path, {"documentation": 80.0})
"""

from .checker import DocumentationChecker
from .fixture import DocumentationFixture

__all__ = [
    "DocumentationChecker",
    "DocumentationFixture",
]
