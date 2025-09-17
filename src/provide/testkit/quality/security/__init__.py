"""Security analysis integration for provide-testkit.

Provides security vulnerability scanning using bandit and other security tools.
Integrates with the quality framework for comprehensive security analysis.

Features:
- Vulnerability scanning with bandit
- Security issue reporting and classification
- Integration with quality gates
- Artifact management for CI/CD

Usage:
    # Basic security scanning
    def test_with_security(security_scanner):
        result = security_scanner.scan(path)
        assert result.passed

    # Security with quality gates
    runner = QualityRunner()
    results = runner.run_with_gates(path, {"security": True})
"""

from .fixture import SecurityFixture
from .scanner import SecurityScanner

__all__ = [
    "SecurityFixture",
    "SecurityScanner",
]
