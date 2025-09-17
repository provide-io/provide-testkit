"""Complexity analysis integration for provide-testkit.

Provides code complexity analysis using radon and other complexity tools.
Integrates with the quality framework for comprehensive complexity analysis.

Features:
- Cyclomatic complexity analysis with radon
- Maintainability index calculation
- Raw metrics (lines of code, etc.)
- Integration with quality gates
- Grade-based reporting (A, B, C, D, F)

Usage:
    # Basic complexity analysis
    def test_with_complexity(complexity_analyzer):
        result = complexity_analyzer.analyze(path)
        assert result.passed

    # Complexity with quality gates
    runner = QualityRunner()
    results = runner.run_with_gates(path, {"complexity": "B"})
"""

from .analyzer import ComplexityAnalyzer
from .fixture import ComplexityFixture

__all__ = [
    "ComplexityAnalyzer",
    "ComplexityFixture",
]
