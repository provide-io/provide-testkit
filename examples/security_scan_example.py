#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Example: Running security scanners on provide-testkit itself (dogfooding).

This demonstrates practical usage of all security scanners across the
provide-io ecosystem.

Usage:
    python examples/security_scan_example.py
"""

from pathlib import Path
import sys

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from provide.testkit.quality.security import (
    BANDIT_AVAILABLE,
    GITLEAKS_AVAILABLE,
    PIP_AUDIT_AVAILABLE,
    SAFETY_AVAILABLE,
    SEMGREP_AVAILABLE,
    TRUFFLEHOG_AVAILABLE,
    GitLeaksScanner,
    PipAuditScanner,
    SafetyScanner,
    SecurityScanner,
    SemgrepScanner,
    TruffleHogScanner,
)


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"{title:^60}")
    print(f"{'=' * 60}\n")


def print_result(scanner_name: str, result: any, available: bool) -> None:
    """Print formatted scanner result."""
    if not available:
        print(f"⏭️  {scanner_name}: Scanner not installed (skipped)")
        return

    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print(f"{status} {scanner_name}")
    print(f"  Score: {result.score}%")
    print(f"  Time: {result.execution_time:.2f}s")

    # Scanner-specific details
    details = result.details
    if "total_secrets" in details:
        print(f"  Secrets: {details['total_secrets']}")
    if "total_vulnerabilities" in details:
        print(f"  Vulnerabilities: {details['total_vulnerabilities']}")
        if details.get("total_dependencies"):
            print(f"  Dependencies scanned: {details['total_dependencies']}")
    if "total_issues" in details:
        print(f"  Issues: {details['total_issues']}")
        breakdown = details.get("severity_breakdown", {})
        if breakdown:
            print(
                f"    HIGH: {breakdown.get('HIGH', 0)}, "
                f"MEDIUM: {breakdown.get('MEDIUM', 0)}, "
                f"LOW: {breakdown.get('LOW', 0)}"
            )
    if "total_findings" in details:
        print(f"  Findings: {details['total_findings']}")
        breakdown = details.get("severity_breakdown", {})
        if breakdown:
            print(
                f"    ERROR: {breakdown.get('ERROR', 0)}, "
                f"WARNING: {breakdown.get('WARNING', 0)}, "
                f"INFO: {breakdown.get('INFO', 0)}"
            )

    # Show errors if present
    if "error" in details:
        print(f"  Error: {details['error']}")

    print()


def main() -> int:
    """Run all security scanners on provide-testkit."""
    print_header("Security Scanner Demonstration")
    print("Running all scanners on provide-testkit codebase")
    print("This demonstrates dogfooding - using scanners on themselves!\n")

    testkit_root = Path(__file__).parent.parent
    src_dir = testkit_root / "src"
    artifact_dir = testkit_root / ".provide" / "output" / "security"

    # Track overall results
    all_passed = True
    scanners_run = 0
    scanners_skipped = 0

    # 1. GitLeaks - Secret Detection
    print_header("1. GitLeaks - Secret Detection")
    if GITLEAKS_AVAILABLE:
        try:
            scanner = GitLeaksScanner(config={"max_secrets": 0})
            result = scanner.analyze(testkit_root, artifact_dir=artifact_dir)
            print_result("GitLeaks", result, True)
            scanners_run += 1
            if not result.passed:
                all_passed = False
        except Exception as e:
            print(f"❌ GitLeaks error: {e}\n")
            all_passed = False
    else:
        print_result("GitLeaks", None, False)
        scanners_skipped += 1

    # 2. TruffleHog - Deep Secret Detection
    print_header("2. TruffleHog - Deep Secret Detection")
    if TRUFFLEHOG_AVAILABLE:
        try:
            scanner = TruffleHogScanner(
                config={
                    "max_secrets": 0,
                    "no_verification": True,  # Faster, don't verify secrets
                }
            )
            result = scanner.analyze(testkit_root, artifact_dir=artifact_dir)
            print_result("TruffleHog", result, True)
            scanners_run += 1
            if not result.passed:
                all_passed = False
        except Exception as e:
            print(f"❌ TruffleHog error: {e}\n")
            all_passed = False
    else:
        print_result("TruffleHog", None, False)
        scanners_skipped += 1

    # 3. PipAudit - Dependency Vulnerabilities
    print_header("3. PipAudit - Dependency Vulnerabilities")
    if PIP_AUDIT_AVAILABLE:
        try:
            scanner = PipAuditScanner(config={"max_vulnerabilities": 5})
            result = scanner.analyze(testkit_root, artifact_dir=artifact_dir)
            print_result("PipAudit", result, True)
            scanners_run += 1
            if not result.passed:
                all_passed = False
        except Exception as e:
            print(f"❌ PipAudit error: {e}\n")
            all_passed = False
    else:
        print_result("PipAudit", None, False)
        scanners_skipped += 1

    # 4. Safety - Dependency Vulnerabilities
    print_header("4. Safety - Dependency Vulnerabilities")
    if SAFETY_AVAILABLE:
        try:
            scanner = SafetyScanner(config={"max_vulnerabilities": 5})
            result = scanner.analyze(testkit_root, artifact_dir=artifact_dir)
            print_result("Safety", result, True)
            scanners_run += 1
            if not result.passed:
                all_passed = False
        except Exception as e:
            print(f"❌ Safety error: {e}\n")
            all_passed = False
    else:
        print_result("Safety", None, False)
        scanners_skipped += 1

    # 5. Bandit - Python Security Scanner
    print_header("5. Bandit (SecurityScanner) - Python Code Analysis")
    if BANDIT_AVAILABLE:
        try:
            scanner = SecurityScanner(
                config={
                    "max_high_severity": 0,
                    "max_medium_severity": 10,
                    "min_score": 80.0,
                    "verbosity": "quiet",
                }
            )
            result = scanner.analyze(src_dir, artifact_dir=artifact_dir)
            print_result("Bandit (SecurityScanner)", result, True)
            scanners_run += 1
            if not result.passed:
                all_passed = False
        except Exception as e:
            print(f"❌ Bandit error: {e}\n")
            all_passed = False
    else:
        print_result("Bandit", None, False)
        scanners_skipped += 1

    # 6. Semgrep - Pattern-Based SAST
    print_header("6. Semgrep - Pattern-Based SAST")
    if SEMGREP_AVAILABLE:
        try:
            scanner = SemgrepScanner(
                config={
                    "config": ["auto"],
                    "max_findings": 20,
                }
            )
            result = scanner.analyze(src_dir, artifact_dir=artifact_dir)
            print_result("Semgrep", result, True)
            scanners_run += 1
            if not result.passed:
                all_passed = False
        except Exception as e:
            print(f"❌ Semgrep error: {e}\n")
            all_passed = False
    else:
        print_result("Semgrep", None, False)
        scanners_skipped += 1

    # Summary
    print_header("Summary")
    print(f"Scanners run: {scanners_run}")
    print(f"Scanners skipped: {scanners_skipped}")
    print(f"\nOverall status: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
    print(f"\nArtifacts saved to: {artifact_dir}")
    print("\nTo install missing scanners:")
    if not GITLEAKS_AVAILABLE:
        print("  GitLeaks: brew install gitleaks")
    if not TRUFFLEHOG_AVAILABLE:
        print("  TruffleHog: brew install trufflehog")
    if not PIP_AUDIT_AVAILABLE:
        print("  PipAudit: uv tool install pip-audit")
    if not SAFETY_AVAILABLE:
        print("  Safety: uv tool install safety")
    if not SEMGREP_AVAILABLE:
        print("  Semgrep: uv tool install semgrep")

    print("\n" + "=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


# 🧪✅🔚
