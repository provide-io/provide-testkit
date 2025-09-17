#
# __init__.py
#
"""
Provide TestKit.

Unified testing utilities for the provide ecosystem with automatic context detection.
Comprehensive fixtures and utilities for testing Foundation-based applications.

Note: Testing information is displayed via pytest hooks in conftest.py
"""

from typing import Any


# Lazy imports to avoid importing testing utilities in production
def __getattr__(name: str) -> Any:
    """Lazy import testing utilities only when accessed."""

    # CLI testing utilities
    if name in [
        "MockContext",
        "isolated_cli_runner",
        "temp_config_file",
        "create_test_cli",
        "CliTestCase",
        "click_testing_mode",
    ]:
        import provide.testkit.cli as cli_module

        return getattr(cli_module, name)

    # Logger testing utilities
    elif name in [
        "reset_foundation_setup_for_testing",
        "reset_foundation_state",
        "mock_logger",
        "mock_logger_factory",
        # New hook utilities
        "DEFAULT_NOISY_LOGGERS",
        "get_noisy_loggers",
        "get_log_level_for_noisy_loggers",
        "pytest_runtest_setup",
        "suppress_loggers",
    ]:
        import provide.testkit.logger as logger_module

        return getattr(logger_module, name)

    # Stream testing utilities
    elif name in ["set_log_stream_for_testing"]:
        import provide.testkit.streams as streams_module

        return getattr(streams_module, name)

    # Fixture utilities
    elif name in [
        "captured_stderr_for_foundation",
        "setup_foundation_telemetry_for_test",
    ]:
        import provide.testkit.fixtures as fixtures_module

        return getattr(fixtures_module, name)

    # Import submodules directly
    elif name in [
        "archive",
        "common",
        "file",
        "process",
        "transport",
        "mocking",
        "time",
        "threading",
    ]:
        import importlib

        return importlib.import_module(f"provide.testkit.{name}")

    # File testing utilities (backward compatibility)
    elif name in [
        "temp_directory",
        "test_files_structure",
        "temp_file",
        "binary_file",
        "nested_directory_structure",
        "empty_directory",
        "readonly_file",
    ]:
        import provide.testkit.file.fixtures as file_module

        return getattr(file_module, name)

    # Process/async testing utilities (backward compatibility)
    elif name in [
        "clean_event_loop",
        "async_timeout",
        "mock_async_process",
        "async_stream_reader",
        "event_loop_policy",
        "async_context_manager",
        "async_iterator",
        "async_queue",
        "async_lock",
        "mock_async_sleep",
    ]:
        import provide.testkit.process.fixtures as process_module

        return getattr(process_module, name)

    # Common mock utilities (backward compatibility)
    elif name in [
        "mock_http_config",
        "mock_telemetry_config",
        "mock_config_source",
        "mock_event_emitter",
        "mock_transport",
        "mock_metrics_collector",
        "mock_cache",
        "mock_database",
        "mock_file_system",
        "mock_subprocess",
    ]:
        import provide.testkit.common.fixtures as common_module

        return getattr(common_module, name)

    # Transport/network testing utilities (backward compatibility)
    elif name in [
        "free_port",
        "mock_server",
        "httpx_mock_responses",
        "mock_websocket",
        "mock_dns_resolver",
        "tcp_client_server",
        "mock_ssl_context",
        "network_timeout",
        "mock_http_headers",
    ]:
        import provide.testkit.transport.fixtures as transport_module

        return getattr(transport_module, name)

    # Archive testing utilities
    elif name in [
        "archive_test_content",
        "large_file_for_compression",
        "multi_format_archives",
        "archive_with_permissions",
        "corrupted_archives",
        "archive_stress_test_files",
    ]:
        import provide.testkit.archive.fixtures as archive_module

        return getattr(archive_module, name)

    # Crypto fixtures (many fixtures)
    elif name in [
        "client_cert",
        "server_cert",
        "ca_cert",
        "valid_cert_pem",
        "valid_key_pem",
        "invalid_cert_pem",
        "invalid_key_pem",
        "malformed_cert_pem",
        "empty_cert",
        "temporary_cert_file",
        "temporary_key_file",
        "cert_with_windows_line_endings",
        "cert_with_utf8_bom",
        "cert_with_extra_whitespace",
        "external_ca_pem",
    ]:
        import provide.testkit.crypto as crypto_module

        return getattr(crypto_module, name)

    # Hub fixtures
    elif name in ["default_container_directory"]:
        import provide.testkit.hub as hub_module

        return getattr(hub_module, name)

    # Environment utilities
    elif name in [
        "TestEnvironment",
        "get_example_dir",
        "add_src_to_path",
        "reset_test_environment",
    ]:
        import provide.testkit.environment as environment_module

        return getattr(environment_module, name)

    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Public API - these will be available for import but loaded lazily
__all__ = [
    # Context detection
    "_is_testing_context",
    # CLI testing
    "MockContext",
    "isolated_cli_runner",
    "temp_config_file",
    "create_test_cli",
    "mock_logger",
    "CliTestCase",
    # Logger testing
    "reset_foundation_setup_for_testing",
    "reset_foundation_state",
    # Logger hook utilities
    "DEFAULT_NOISY_LOGGERS",
    "get_noisy_loggers",
    "get_log_level_for_noisy_loggers",
    "pytest_runtest_setup",
    "suppress_loggers",
    # Stream testing
    "set_log_stream_for_testing",
    # Common fixtures
    "captured_stderr_for_foundation",
    "setup_foundation_telemetry_for_test",
    # Crypto fixtures
    "client_cert",
    "server_cert",
    "ca_cert",
    "valid_cert_pem",
    "valid_key_pem",
    "invalid_cert_pem",
    "invalid_key_pem",
    "malformed_cert_pem",
    "empty_cert",
    "temporary_cert_file",
    "temporary_key_file",
    "cert_with_windows_line_endings",
    "cert_with_utf8_bom",
    "cert_with_extra_whitespace",
    "external_ca_pem",
    # Hub fixtures
    "default_container_directory",
    # Environment utilities
    "TestEnvironment",
    "get_example_dir",
    "add_src_to_path",
    "reset_test_environment",
]
