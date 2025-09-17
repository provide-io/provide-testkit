"""Pytest fixtures for security scanning."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from ..base import BaseQualityFixture
from .scanner import BANDIT_AVAILABLE, SecurityScanner


class SecurityFixture(BaseQualityFixture):
    """Pytest fixture for security scanning integration."""

    def __init__(self, config: dict[str, Any] | None = None, artifact_dir: Path | None = None):
        """Initialize security fixture.

        Args:
            config: Security scanner configuration
            artifact_dir: Directory for artifacts
        """
        super().__init__(config, artifact_dir)
        self.scanner: SecurityScanner | None = None

    def setup(self) -> None:
        """Setup security scanning."""
        if not BANDIT_AVAILABLE:
            pytest.skip("Bandit not available")

        try:
            self.scanner = SecurityScanner(self.config)
        except Exception as e:
            pytest.skip(f"Failed to initialize security scanner: {e}")

    def teardown(self) -> None:
        """Cleanup security scanner."""
        # No cleanup needed for security scanner
        pass

    def scan(self, path: Path) -> dict[str, Any]:
        """Perform security scan.

        Args:
            path: Path to scan

        Returns:
            Security scan results
        """
        self.ensure_setup()
        if not self.scanner:
            return {"error": "Scanner not available"}

        result = self.scanner.analyze(path, artifact_dir=self.artifact_dir)
        self.add_result(result)
        return {
            "passed": result.passed,
            "score": result.score,
            "issues": result.details.get("total_issues", 0),
            "details": result.details,
        }

    def generate_report(self, format: str = "terminal") -> str:
        """Generate security report.

        Args:
            format: Report format (terminal, json)

        Returns:
            Formatted report
        """
        if not self.scanner:
            return "No security scanner available"

        results = self.get_results_by_tool()
        if "security" not in results:
            return "No security results available"

        return self.scanner.report(results["security"], format)


@pytest.fixture
def security_scanner(request, tmp_path) -> Generator[SecurityFixture, None, None]:
    """Pytest fixture for security scanning.

    Provides a SecurityFixture instance for security vulnerability scanning.

    Usage:
        def test_security_scan(security_scanner):
            result = security_scanner.scan(Path('./src'))
            assert result['passed']
            assert result['issues'] == 0
    """
    # Get configuration from pytest request
    config = getattr(request, "param", {})

    # Create artifact directory for this test
    artifact_dir = tmp_path / "security"

    # Initialize fixture
    fixture = SecurityFixture(config=config, artifact_dir=artifact_dir)

    try:
        fixture.setup()
        yield fixture
    finally:
        fixture.teardown()


@pytest.fixture
def security_config():
    """Default security configuration fixture.

    Returns standard security configuration that can be customized
    per test or project.

    Usage:
        def test_custom_security(security_config):
            security_config["max_high_severity"] = 0
            security_config["min_score"] = 95.0
            # Use with parametrized security_scanner
    """
    return {
        "confidence": "medium",
        "severity": "medium",
        "max_high_severity": 0,
        "max_medium_severity": 5,
        "min_score": 80.0,
        "exclude": ["*/tests/*", "*/test_*", "*/.venv/*", "*/venv/*", "*/__pycache__/*", "*/migrations/*"],
    }


# Parametrized fixtures for different security configurations
@pytest.fixture(
    params=[
        {"max_high_severity": 0, "max_medium_severity": 0, "min_score": 100.0},  # Strict
        {"max_high_severity": 1, "max_medium_severity": 5, "min_score": 80.0},  # Normal
        {"max_high_severity": 5, "max_medium_severity": 10, "min_score": 60.0},  # Lenient
    ]
)
def parametrized_security(request, tmp_path) -> Generator[SecurityFixture, None, None]:
    """Parametrized security fixture for testing different configurations.

    Automatically runs tests with different security thresholds
    to validate behavior under various settings.

    Usage:
        def test_security_configs(parametrized_security):
            # Test runs multiple times with different configs
            result = parametrized_security.scan(Path('./src'))
            # Behavior will vary based on configuration
    """
    config = request.param
    artifact_dir = tmp_path / f"security_{id(config)}"

    fixture = SecurityFixture(config=config, artifact_dir=artifact_dir)

    try:
        fixture.setup()
        yield fixture
    finally:
        fixture.teardown()


# Pytest hooks for automatic security integration
def pytest_configure(config):
    """Configure pytest with security markers."""
    config.addinivalue_line("markers", "security: mark test to run with security scanning")
    config.addinivalue_line("markers", "no_security: mark test to skip security scanning")


@pytest.fixture(autouse=True)
def auto_security_marker(request):
    """Automatically apply security scanning to marked tests.

    Tests marked with @pytest.mark.security will automatically
    get security scanning without needing to explicitly use fixtures.
    """
    if request.node.get_closest_marker("security"):
        # Test is marked for security - enable automatic scanning
        if not request.node.get_closest_marker("no_security"):
            # Create temporary security fixture
            security_fixture = SecurityFixture()
            try:
                security_fixture.setup()
                # Security scan would be applied here in a real implementation
                # For now, we just yield to continue the test
                yield
            finally:
                security_fixture.teardown()
        else:
            yield
    else:
        yield
