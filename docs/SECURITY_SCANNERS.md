# Security Scanners Guide

Comprehensive guide for using provide-testkit security scanners across the provide-io ecosystem.

## Overview

provide-testkit includes production-focused security scanners that integrate seamlessly with CI/CD pipelines. All scanners follow a consistent plugin architecture and return standardized `QualityResult` objects.

**Available Scanners:**
- **GitLeaks** - Secret detection (API keys, tokens, credentials)
- **PipAudit** - PyPI package vulnerability scanning
- **Safety** - PyUp vulnerability database scanning
- **Semgrep** - Pattern-based SAST (Static Application Security Testing)
- **SecurityScanner (Bandit)** - Python-specific SAST
- **TruffleHog** - Deep secret detection with verification

**Test Coverage:** 88% overall (all scanners 85-95% coverage)

## Quick Start

### Installation

```bash
# Basic installation
pip install provide-testkit

# With all security scanners (requires Go binaries for GitLeaks/TruffleHog)
pip install bandit semgrep safety pip-audit

# Install GitLeaks (macOS)
brew install gitleaks

# Install TruffleHog (macOS)
brew install trufflehog
```

### Basic Usage

```python
from pathlib import Path
from provide.testkit.quality.security import (
    GitLeaksScanner,
    PipAuditScanner,
    SafetyScanner,
    SemgrepScanner,
    SecurityScanner,
    TruffleHogScanner,
)

# Scan for secrets
gitleaks = GitLeaksScanner(config={"max_secrets": 0})
result = gitleaks.analyze(Path("./src"))
print(f"Secrets found: {result.details['total_secrets']}")
print(f"Score: {result.score}%")
print(f"Passed: {result.passed}")

# Scan Python dependencies for vulnerabilities
pip_audit = PipAuditScanner(config={"max_vulnerabilities": 0})
result = pip_audit.analyze(Path("."))
print(f"Vulnerabilities: {result.details['total_vulnerabilities']}")

# Scan Python code for security issues
bandit = SecurityScanner(config={
    "max_high_severity": 0,
    "max_medium_severity": 5,
    "min_score": 80.0,
    "verbosity": "quiet",  # quiet, normal, or verbose
})
result = bandit.analyze(Path("./src"))
print(f"Issues: {result.details['total_issues']}")
```

## Scanner Details

### 1. GitLeaks - Secret Detection

Scans for exposed secrets like API keys, passwords, and tokens in code and git history.

**Configuration:**
```python
config = {
    "max_secrets": 0,                    # Maximum allowed secrets
    "config_file": ".gitleaks.toml",    # Custom config file
    "verbose": True,                     # Verbose output
    "redact": True,                      # Redact secrets in output
    "timeout": 300,                      # Timeout in seconds
}

scanner = GitLeaksScanner(config)
result = scanner.analyze(Path("./src"), artifact_dir=Path(".security"))
```

**Auto-detection:** Automatically uses `.provide/security/gitleaks.toml` if present.

**Score Calculation:** 100 - (secrets_found × 25)

**Example Output:**
```python
{
    "tool": "gitleaks",
    "passed": False,
    "score": 75.0,
    "details": {
        "total_secrets": 1,
        "secrets": [{
            "description": "AWS Access Key",
            "file": "config.py",
            "line": 10,
            "secret": "***REDACTED***",  # Always redacted
            "rule_id": "aws-access-key",
        }]
    }
}
```

### 2. PipAudit - PyPI Vulnerability Scanner

Scans Python dependencies against the PyPI security advisory database.

**Configuration:**
```python
config = {
    "max_vulnerabilities": 0,           # Maximum allowed vulnerabilities
    "strict": False,                    # Strict mode
    "local": False,                     # Only scan local packages
    "skip_editable": False,             # Skip editable installs
    "timeout": 300,
}

scanner = PipAuditScanner(config)
result = scanner.analyze(Path("."))  # Scans requirements.txt or pyproject.toml
```

**Score Calculation:** 100 - (vulnerabilities × 10)

**Example Output:**
```python
{
    "tool": "pip-audit",
    "passed": False,
    "score": 90.0,
    "details": {
        "total_dependencies": 50,
        "total_vulnerabilities": 1,
        "vulnerabilities": [{
            "package": "requests",
            "version": "2.28.0",
            "id": "PYSEC-2023-123",
            "description": "Request smuggling vulnerability",
            "fix_versions": ["2.31.0"],
        }]
    }
}
```

### 3. Safety - PyUp Vulnerability Database

Scans Python dependencies against the PyUp Safety database.

**Configuration:**
```python
config = {
    "max_vulnerabilities": 0,
    "policy_file": ".safety-policy.yml",  # Policy file path
    "full_report": False,                 # Full vulnerability details
    "ignore_vulns": ["12345", "67890"],  # Vulnerability IDs to ignore
    "timeout": 120,
}

scanner = SafetyScanner(config)
result = scanner.analyze(Path("."))
```

**Auto-detection:** Automatically uses `.provide/security/safety-policy.yml` if present.

**Score Calculation:** 100 - (vulnerabilities × 10)

### 4. Semgrep - Pattern-Based SAST

Scans code for security vulnerabilities, bugs, and anti-patterns using pattern rules.

**Configuration:**
```python
config = {
    "config": ["auto"],                  # or ["p/security-audit", "p/owasp-top-10"]
    "severity": ["ERROR", "WARNING"],    # Severity levels to include
    "max_findings": 0,                   # Maximum allowed findings
    "exclude": ["**/test_*", "**/.venv/**"],
    "max_memory": 4000,                  # Max memory in MB
    "timeout_per_rule": 30,              # Timeout per rule
    "timeout": 600,
}

scanner = SemgrepScanner(config)
result = scanner.analyze(Path("./src"))
```

**Auto-detection:** Automatically uses `.provide/security/semgrep.yml` if present.

**Score Calculation:**
- ERROR: -15 points
- WARNING: -5 points
- INFO: -1 point

**Example Output:**
```python
{
    "tool": "semgrep",
    "passed": True,
    "score": 84.0,
    "details": {
        "total_findings": 3,
        "severity_breakdown": {"ERROR": 1, "WARNING": 1, "INFO": 1},
        "findings": [{
            "check_id": "python.lang.security.audit.exec-used",
            "path": "utils.py",
            "start_line": 42,
            "severity": "ERROR",
            "message": "Use of exec() is dangerous",
        }]
    }
}
```

### 5. SecurityScanner (Bandit) - Python SAST

Scans Python code for common security issues using Bandit.

**Configuration:**
```python
config = {
    "max_high_severity": 0,              # Maximum HIGH severity issues
    "max_medium_severity": 5,            # Maximum MEDIUM severity issues
    "min_score": 80.0,                   # Minimum passing score
    "verbosity": "quiet",                # quiet, normal, or verbose
    "exclude": ["*/tests/*", "*/.venv/*"],  # Exclude patterns
}

scanner = SecurityScanner(config)
result = scanner.analyze(Path("./src"), artifact_dir=Path(".provide/output/security"))
```

**Verbosity Levels:**
- `quiet`: Only errors (best for CI/CD)
- `normal`: Errors and warnings (default)
- `verbose`: All messages including debug info

**Score Calculation:**
- HIGH severity: -10 points
- MEDIUM severity: -5 points
- LOW severity: -1 point

**Example Output:**
```python
{
    "tool": "security",
    "passed": False,
    "score": 90.0,
    "details": {
        "total_files": 25,
        "total_issues": 1,
        "severity_breakdown": {"HIGH": 1, "MEDIUM": 0, "LOW": 0},
        "confidence_breakdown": {"HIGH": 1, "MEDIUM": 0, "LOW": 0},
        "thresholds": {
            "max_high_severity": 0,
            "max_medium_severity": 5,
            "min_score": 80.0,
        },
        "issues": [{
            "filename": "/path/to/file.py",
            "line_number": 42,
            "test_id": "B101",
            "test_name": "assert_used",
            "severity": "HIGH",
            "confidence": "HIGH",
            "text": "Use of assert detected",
            "code": "assert user.is_authenticated",
        }]
    }
}
```

### 6. TruffleHog - Deep Secret Detection

Scans for secrets using entropy analysis and pattern matching with optional verification.

**Configuration:**
```python
config = {
    "max_secrets": 0,
    "only_verified": False,              # Only report verified secrets
    "no_verification": False,            # Skip verification entirely
    "concurrency": 4,                    # Parallel workers
    "include_detectors": ["aws", "github"],  # Only these detectors
    "exclude_detectors": ["generic"],    # Exclude these detectors
    "exclude_paths": ["*.test", "vendor/*"],  # Exclude file patterns
    "timeout": 600,
}

scanner = TruffleHogScanner(config)
result = scanner.analyze(Path("."))
```

**Auto-detection:** Automatically uses `.provide/security/trufflehog.yml` if present.

**Score Calculation:**
- Verified (active) secrets: -50 points each
- Unverified secrets: -15 points each

**Example Output:**
```python
{
    "tool": "trufflehog",
    "passed": False,
    "score": 50.0,
    "details": {
        "total_secrets": 2,
        "verified_secrets": 1,           # 🔴 ACTIVE and dangerous!
        "unverified_secrets": 1,         # ⚪ Potential false positive
        "secrets": [{
            "detector_type": "AWS",
            "detector_name": "AWS Access Key",
            "verified": True,            # Secret is ACTIVE
            "file": "config.py",
            "line": 10,
            "raw": "***REDACTED***",     # Never exposed
            "redacted": "AKIA****************",
        }]
    }
}
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for GitLeaks

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install scanners
        run: |
          pip install provide-testkit bandit semgrep safety pip-audit
          # Install GitLeaks
          wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz
          tar -xzf gitleaks_8.18.0_linux_x64.tar.gz
          sudo mv gitleaks /usr/local/bin/

      - name: Run security scans
        run: |
          python -c "
          from pathlib import Path
          from provide.testkit.quality.security import *

          # Run all scanners
          scanners = [
              ('GitLeaks', GitLeaksScanner({'max_secrets': 0})),
              ('PipAudit', PipAuditScanner({'max_vulnerabilities': 0})),
              ('Safety', SafetyScanner({'max_vulnerabilities': 0})),
              ('Semgrep', SemgrepScanner({'max_findings': 10})),
              ('Bandit', SecurityScanner({'max_high_severity': 0, 'verbosity': 'quiet'})),
          ]

          failed = []
          for name, scanner in scanners:
              result = scanner.analyze(Path('.'))
              print(f'{name}: Score={result.score}%, Passed={result.passed}')
              if not result.passed:
                  failed.append(name)

          if failed:
              print(f'❌ Failed scanners: {failed}')
              exit(1)
          print('✅ All security scans passed!')
          "
```

### wrknv.toml Integration

```toml
[tasks.security]
description = "Run all security scanners"
script = """
python -c "
from pathlib import Path
from provide.testkit.quality.security import *

scanners = {
    'secrets': GitLeaksScanner({'max_secrets': 0}),
    'dependencies': PipAuditScanner({'max_vulnerabilities': 0}),
    'code': SecurityScanner({'max_high_severity': 0, 'verbosity': 'quiet'}),
}

for name, scanner in scanners.items():
    result = scanner.analyze(Path('.'))
    print(f'{name}: {result.score}% - {'✅ PASSED' if result.passed else '❌ FAILED'}')
    if not result.passed:
        exit(1)
"
"""

[tasks.security.gitleaks]
description = "Scan for secrets with GitLeaks"
script = """
python -c "
from pathlib import Path
from provide.testkit.quality.security.gitleaks_scanner import GitLeaksScanner
scanner = GitLeaksScanner({'max_secrets': 0})
result = scanner.analyze(Path('.'))
report = scanner.report(result, 'terminal')
print(report)
exit(0 if result.passed else 1)
"
"""

[tasks.security.dependencies]
description = "Scan dependencies for vulnerabilities"
script = """
python -c "
from pathlib import Path
from provide.testkit.quality.security.pip_audit_scanner import PipAuditScanner
scanner = PipAuditScanner({'max_vulnerabilities': 0})
result = scanner.analyze(Path('.'))
report = scanner.report(result, 'terminal')
print(report)
exit(0 if result.passed else 1)
"
"""
```

## Running Scanners on provide-testkit Itself

Example of dogfooding - running scanners on this codebase:

```python
from pathlib import Path
from provide.testkit.quality.security import (
    GitLeaksScanner,
    PipAuditScanner,
    SecurityScanner,
    SemgrepScanner,
)

# Scan testkit for secrets
gitleaks = GitLeaksScanner(config={"max_secrets": 0})
result = gitleaks.analyze(
    Path("/home/user/provide-testkit"),
    artifact_dir=Path(".provide/output/security")
)
print(f"\n{'='*50}")
print(f"GitLeaks Results:")
print(f"{'='*50}")
print(f"Secrets found: {result.details['total_secrets']}")
print(f"Score: {result.score}%")
print(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")

# Scan testkit dependencies
pip_audit = PipAuditScanner(config={"max_vulnerabilities": 5})
result = pip_audit.analyze(Path("/home/user/provide-testkit"))
print(f"\n{'='*50}")
print(f"PipAudit Results:")
print(f"{'='*50}")
print(f"Dependencies: {result.details.get('total_dependencies', 'N/A')}")
print(f"Vulnerabilities: {result.details['total_vulnerabilities']}")
print(f"Score: {result.score}%")
print(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")

# Scan testkit Python code
bandit = SecurityScanner(config={
    "max_high_severity": 0,
    "max_medium_severity": 10,
    "verbosity": "quiet",
})
result = bandit.analyze(Path("/home/user/provide-testkit/src"))
print(f"\n{'='*50}")
print(f"Bandit (SecurityScanner) Results:")
print(f"{'='*50}")
print(f"Files scanned: {result.details.get('total_files', 'N/A')}")
print(f"Issues found: {result.details['total_issues']}")
print(f"Severity: HIGH={result.details['severity_breakdown']['HIGH']}, "
      f"MEDIUM={result.details['severity_breakdown']['MEDIUM']}, "
      f"LOW={result.details['severity_breakdown']['LOW']}")
print(f"Score: {result.score}%")
print(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")

# Scan with Semgrep
semgrep = SemgrepScanner(config={
    "config": ["auto"],
    "max_findings": 20,
})
result = semgrep.analyze(Path("/home/user/provide-testkit/src"))
print(f"\n{'='*50}")
print(f"Semgrep Results:")
print(f"{'='*50}")
print(f"Findings: {result.details['total_findings']}")
print(f"Severity: ERROR={result.details['severity_breakdown']['ERROR']}, "
      f"WARNING={result.details['severity_breakdown']['WARNING']}, "
      f"INFO={result.details['severity_breakdown']['INFO']}")
print(f"Score: {result.score}%")
print(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
```

## Architecture & Extensibility

### Adding Enterprise Scanners (Snyk, SonarQube)

The plugin architecture makes it easy to add enterprise scanners:

#### Example: Adding Snyk Scanner

```python
from pathlib import Path
import json
import time
from typing import Any

from provide.foundation.errors.process import ProcessError
from provide.foundation.file import atomic_write_text, ensure_dir
from provide.foundation.process import run
from provide.testkit.quality.base import QualityResult, QualityToolError


def _check_snyk_available() -> bool:
    """Check if Snyk is available."""
    try:
        result = run(["snyk", "--version"], timeout=10, check=False)
        return result.returncode == 0
    except (ProcessError, TimeoutError):
        return False


SNYK_AVAILABLE = _check_snyk_available()


class SnykScanner:
    """Snyk vulnerability scanner.

    Scans code and dependencies for vulnerabilities using Snyk.
    Requires: snyk CLI (npm install -g snyk) and authentication.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize Snyk scanner."""
        if not SNYK_AVAILABLE:
            raise QualityToolError(
                "Snyk not available. Install with: npm install -g snyk",
                tool="snyk",
            )

        self.config = config or {}
        self.artifact_dir: Path | None = None

    def analyze(self, path: Path, **kwargs: Any) -> QualityResult:
        """Run Snyk analysis."""
        self.artifact_dir = kwargs.get("artifact_dir", Path(".provide/output/security"))
        start_time = time.time()

        try:
            result = self._run_snyk_scan(path)
            result.execution_time = time.time() - start_time
            self._generate_artifacts(result)
            return result

        except Exception as e:
            return QualityResult(
                tool="snyk",
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                execution_time=time.time() - start_time,
            )

    def _run_snyk_scan(self, path: Path) -> QualityResult:
        """Run Snyk scan."""
        try:
            cmd = ["snyk", "test", "--json", str(path)]

            if self.config.get("severity_threshold"):
                cmd.extend(["--severity-threshold", self.config["severity_threshold"]])

            result = run(cmd, timeout=self.config.get("timeout", 300), check=False)

            snyk_data = json.loads(result.stdout) if result.stdout else {}
            return self._process_results(snyk_data, result.returncode)

        except TimeoutError as e:
            raise QualityToolError(f"Snyk scan timed out: {e!s}", tool="snyk") from e
        except Exception as e:
            raise QualityToolError(f"Snyk scan failed: {e!s}", tool="snyk") from e

    def _process_results(self, snyk_data: dict[str, Any], returncode: int) -> QualityResult:
        """Process Snyk results into QualityResult."""
        vulnerabilities = snyk_data.get("vulnerabilities", [])
        total_vulns = len(vulnerabilities)

        # Calculate score
        score = 100.0 - (total_vulns * 10)
        score = max(0.0, score)

        max_vulns = self.config.get("max_vulnerabilities", 0)
        passed = total_vulns <= max_vulns

        details = {
            "total_vulnerabilities": total_vulns,
            "score": score,
            "vulnerabilities": vulnerabilities[:20],
            "returncode": returncode,
        }

        return QualityResult(tool="snyk", passed=passed, score=score, details=details)

    def _generate_artifacts(self, result: QualityResult) -> None:
        """Generate Snyk analysis artifacts."""
        if not self.artifact_dir:
            return

        ensure_dir(self.artifact_dir)

        try:
            json_file = self.artifact_dir / "snyk.json"
            json_data = {
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
                "execution_time": result.execution_time,
            }
            atomic_write_text(json_file, json.dumps(json_data, indent=2))
            result.artifacts.append(json_file)

        except Exception as e:
            result.details["artifact_error"] = str(e)

    def report(self, result: QualityResult, format: str = "terminal") -> str:
        """Generate report from QualityResult."""
        if format == "json":
            return json.dumps({
                "tool": result.tool,
                "passed": result.passed,
                "score": result.score,
                "details": result.details,
            }, indent=2)
        else:
            return str(result.details)
```

**Usage:**
```python
from snyk_scanner import SnykScanner

scanner = SnykScanner(config={
    "max_vulnerabilities": 0,
    "severity_threshold": "high",  # Snyk-specific option
})
result = scanner.analyze(Path("."))
```

### Key Architecture Points

1. **Standardized Result Format:** All scanners return `QualityResult` objects
2. **Foundation Integration:** All use `foundation.process.run` for subprocess execution
3. **Absolute Imports:** Always use absolute imports, never relative
4. **Artifact Generation:** All generate JSON and text reports
5. **Exception Handling:** Proper error handling with `QualityToolError`
6. **Configuration:** Support both explicit config and auto-detection
7. **Scoring:** Consistent scoring system (0-100 scale)

## Best Practices

### 1. Progressive Security Gates

Start permissive, tighten over time:

```python
# Week 1: Establish baseline
config_baseline = {
    "max_high_severity": 10,
    "max_medium_severity": 50,
    "min_score": 50.0,
}

# Week 4: Tighten requirements
config_strict = {
    "max_high_severity": 5,
    "max_medium_severity": 20,
    "min_score": 70.0,
}

# Production: Zero tolerance
config_production = {
    "max_high_severity": 0,
    "max_medium_severity": 5,
    "min_score": 90.0,
}
```

### 2. Layered Defense

Use multiple scanners for comprehensive coverage:

```python
# Secrets: GitLeaks (fast) + TruffleHog (deep)
# Dependencies: PipAudit + Safety (different databases)
# Code: Bandit (Python-specific) + Semgrep (multi-language)
```

### 3. Artifact Management

Always save artifacts for audit trails:

```python
artifact_dir = Path(f".provide/output/security/{datetime.now().isoformat()}")

for scanner in all_scanners:
    result = scanner.analyze(path, artifact_dir=artifact_dir)
    # Artifacts saved with timestamps for historical tracking
```

### 4. Quiet Mode in CI/CD

Reduce noise in CI/CD logs:

```python
# Bandit verbosity
bandit = SecurityScanner({"verbosity": "quiet"})

# GitLeaks verbose mode off
gitleaks = GitLeaksScanner({"verbose": False})
```

## Troubleshooting

### Scanner Not Available

```python
from provide.testkit.quality.security.gitleaks_scanner import GITLEAKS_AVAILABLE

if not GITLEAKS_AVAILABLE:
    print("GitLeaks not installed!")
    print("Install: brew install gitleaks")
```

### Timeouts

```python
# Increase timeout for large codebases
scanner = SemgrepScanner({"timeout": 1200})  # 20 minutes
```

### False Positives

```python
# GitLeaks: Use .gitleaksignore
# Semgrep: Use --exclude patterns
# Bandit: Use # nosec comments (sparingly!)
# Safety: Use ignore_vulns list
```

## License

Apache-2.0

## Support

- Documentation: https://github.com/provide-io/provide-testkit
- Issues: https://github.com/provide-io/provide-testkit/issues
- provide-io ecosystem: https://provide.io
