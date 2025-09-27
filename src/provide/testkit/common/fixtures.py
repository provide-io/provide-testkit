"""
Common Test Fixtures for Foundation.

Provides pytest fixtures for capturing output, setting up telemetry,
and other common testing scenarios across the Foundation test suite.
"""

from collections.abc import Callable, Generator
import io
from typing import Any, TextIO
from unittest.mock import Mock

import pytest

from provide.foundation import TelemetryConfig, get_hub
from provide.testkit.streams import set_log_stream_for_testing


@pytest.fixture
def captured_stderr_for_foundation() -> Generator[TextIO]:
    """
    Fixture to capture stderr output from Foundation's logging system.

    It redirects Foundation's log stream to an `io.StringIO` buffer, yields the buffer
    to the test, and then restores the original stream.
    """
    current_test_stream = io.StringIO()
    set_log_stream_for_testing(current_test_stream)
    yield current_test_stream
    set_log_stream_for_testing(None)
    current_test_stream.close()


@pytest.fixture
def setup_foundation_telemetry_for_test(
    captured_stderr_for_foundation: TextIO,
) -> Callable[[TelemetryConfig | None], None]:
    """
    Fixture providing a function to set up Foundation Telemetry for tests.

    This fixture captures stderr via `captured_stderr_for_foundation`
    and provides a callable to configure telemetry with custom settings.
    """

    def _setup(config: TelemetryConfig | None = None) -> None:
        if config is None:
            config = TelemetryConfig()

        # Use Hub API directly instead of deprecated setup_telemetry
        hub = get_hub()
        hub.initialize_foundation(config, force=True)

    return _setup


# Mock fixtures for common testing scenarios
@pytest.fixture
def mock_cache() -> Mock:
    """Mock cache object for testing."""
    mock = Mock()
    mock.get.return_value = None
    mock.set.return_value = None
    mock.delete.return_value = None
    mock.clear.return_value = None
    return mock


@pytest.fixture
def mock_config_source() -> Mock:
    """Mock configuration source for testing."""
    mock = Mock()
    mock.load.return_value = {}
    mock.reload.return_value = {}
    return mock


@pytest.fixture
def mock_database() -> Mock:
    """Mock database connection for testing."""
    mock = Mock()
    mock.connect.return_value = None
    mock.disconnect.return_value = None
    mock.execute.return_value = []
    mock.commit.return_value = None
    mock.rollback.return_value = None
    return mock


@pytest.fixture
def mock_event_emitter() -> Mock:
    """Mock event emitter for testing."""
    mock = Mock()
    mock.emit.return_value = None
    mock.on.return_value = None
    mock.off.return_value = None
    return mock


@pytest.fixture
def mock_file_system() -> Mock:
    """Mock file system for testing."""
    mock = Mock()
    mock.read.return_value = ""
    mock.write.return_value = None
    mock.exists.return_value = True
    mock.delete.return_value = None
    return mock


@pytest.fixture
def mock_http_config() -> Mock:
    """Mock HTTP configuration for testing."""
    mock = Mock()
    mock.base_url = "http://localhost:8080"
    mock.timeout = 30
    mock.retries = 3
    return mock


@pytest.fixture
def mock_metrics_collector() -> Mock:
    """Mock metrics collector for testing."""
    mock = Mock()
    mock.collect.return_value = {}
    mock.reset.return_value = None
    mock.increment.return_value = None
    mock.gauge.return_value = None
    return mock


@pytest.fixture
def mock_subprocess() -> Mock:
    """Mock subprocess for testing."""
    mock = Mock()
    mock.run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock.Popen.return_value = Mock(
        returncode=0,
        stdout=Mock(read=Mock(return_value="")),
        stderr=Mock(read=Mock(return_value="")),
        communicate=Mock(return_value=("", "")),
    )
    return mock


@pytest.fixture
def mock_telemetry_config() -> Mock:
    """Mock telemetry configuration for testing."""
    mock = Mock()
    mock.service_name = "test-service"
    mock.log_level = "DEBUG"
    mock.enable_file_logging = False
    mock.log_file_path = None
    return mock


@pytest.fixture
def mock_transport() -> Mock:
    """Mock transport for testing."""
    mock = Mock()
    mock.send.return_value = {"status": "success"}
    mock.receive.return_value = {"data": "test"}
    mock.connect.return_value = None
    mock.disconnect.return_value = None
    return mock
