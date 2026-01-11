#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Security analysis integration for provide-testkit.

Provides comprehensive security scanning using multiple security tools:
- Bandit: Python SAST (static application security testing)
- pip-audit: Dependency vulnerability scanning (PyPI advisories)
- Safety: Dependency vulnerability scanning (PyUp database)
- GitLeaks: Secret detection (fast, pattern-based)
- TruffleHog: Deep secret detection (entropy analysis, verification)
- Semgrep: Pattern-based SAST with custom rules

Features:
- Multiple vulnerability scanners for comprehensive coverage
- Dependency vulnerability scanning
- Secret/credential detection
- Security issue reporting and classification
- Integration with quality gates
- Artifact management for CI/CD

Usage:
    # Basic security scanning (Bandit)
    def test_with_security(security_scanner):
        result = security_scanner.scan(path)
        assert result.passed

    # Dependency vulnerability scanning
    from provide.testkit.quality.security import PipAuditScanner
    scanner = PipAuditScanner()
    result = scanner.analyze(path)

    # Secret detection
    from provide.testkit.quality.security import GitLeaksScanner
    scanner = GitLeaksScanner()
    result = scanner.analyze(path)
"""

from .fixture import SecurityFixture
from .gitleaks_scanner import GITLEAKS_AVAILABLE, GitLeaksScanner
from .pip_audit_scanner import PIP_AUDIT_AVAILABLE, PipAuditScanner
from .safety_scanner import SAFETY_AVAILABLE, SafetyScanner
from .scanner import BANDIT_AVAILABLE, SecurityScanner
from .semgrep_scanner import SEMGREP_AVAILABLE, SemgrepScanner
from .trufflehog_scanner import TRUFFLEHOG_AVAILABLE, TruffleHogScanner

__all__ = [
    "BANDIT_AVAILABLE",
    "GITLEAKS_AVAILABLE",
    "PIP_AUDIT_AVAILABLE",
    "SAFETY_AVAILABLE",
    "SEMGREP_AVAILABLE",
    "TRUFFLEHOG_AVAILABLE",
    # Secret detection
    "GitLeaksScanner",
    # Dependency vulnerability scanners
    "PipAuditScanner",
    "SafetyScanner",
    # Core security (Bandit)
    "SecurityFixture",
    "SecurityScanner",
    # Pattern-based SAST
    "SemgrepScanner",
    "TruffleHogScanner",
]

# 🧪✅🔚
