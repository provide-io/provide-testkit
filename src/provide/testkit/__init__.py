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

# Mapping of attribute names to their modules
_LAZY_IMPORTS = {
    # CLI testing utilities
    "cli": [
        "MockContext",
        "isolated_cli_runner",
        "temp_config_file",
        "create_test_cli",
        "CliTestCase",
        "click_testing_mode",
    ],
    # Logger testing utilities
    "logger": [
        "reset_foundation_setup_for_testing",
        "reset_foundation_state",
        "mock_logger",
        "mock_logger_factory",
        "DEFAULT_NOISY_LOGGERS",
        "get_noisy_loggers",
        "get_log_level_for_noisy_loggers",
        "pytest_runtest_setup",
        "suppress_loggers",
    ],
    # Stream testing utilities
    "streams": ["set_log_stream_for_testing"],
    # Fixture utilities
    "fixtures": [
        "captured_stderr_for_foundation",
        "setup_foundation_telemetry_for_test",
    ],
    # File testing utilities
    "file.fixtures": [
        "temp_directory",
        "test_files_structure",
        "temp_file",
        "binary_file",
        "nested_directory_structure",
        "empty_directory",
        "readonly_file",
    ],
    # Process/async testing utilities
    "process.fixtures": [
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
    ],
    # Common mock utilities
    "common.fixtures": [
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
    ],
    # Transport/network testing utilities
    "transport.fixtures": [
        "free_port",
        "mock_server",
        "httpx_mock_responses",
        "mock_websocket",
        "mock_dns_resolver",
        "tcp_client_server",
        "mock_ssl_context",
        "network_timeout",
        "mock_http_headers",
    ],
    # Archive testing utilities
    "archive.fixtures": [
        "archive_test_content",
        "large_file_for_compression",
        "multi_format_archives",
        "archive_with_permissions",
        "corrupted_archives",
        "archive_stress_test_files",
    ],
    # Crypto fixtures
    "crypto": [
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
    ],
    # Hub fixtures
    "hub": ["default_container_directory"],
    # Environment utilities
    "environment": [
        "TestEnvironment",
        "get_example_dir",
        "add_src_to_path",
        "reset_test_environment",
    ],
}

# Submodules that can be imported directly
_DIRECT_SUBMODULES = [
    "archive",
    "common",
    "file",
    "process",
    "transport",
    "mocking",
    "time",
    "threading",
]


def _import_from_module(module_path: str, name: str) -> Any:
    """Import an attribute from a specific module."""
    import importlib

    module = importlib.import_module(f"provide.testkit.{module_path}")
    return getattr(module, name)


def _find_attribute_module(name: str) -> str | None:
    """Find which module contains the given attribute name."""
    for module_path, attributes in _LAZY_IMPORTS.items():
        if name in attributes:
            return module_path
    return None


# Lazy imports to avoid importing testing utilities in production
def __getattr__(name: str) -> Any:
    """Lazy import testing utilities only when accessed."""
    # Check if it's a direct submodule
    if name in _DIRECT_SUBMODULES:
        import importlib

        return importlib.import_module(f"provide.testkit.{name}")

    # Find which module contains this attribute
    module_path = _find_attribute_module(name)
    if module_path:
        return _import_from_module(module_path, name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Public API - these will be available for import but loaded lazily
__all__ = [
    "DEFAULT_NOISY_LOGGERS",
    "CliTestCase",
    "MockContext",
    "TestEnvironment",
    "_is_testing_context",
    "add_src_to_path",
    "ca_cert",
    "captured_stderr_for_foundation",
    "cert_with_extra_whitespace",
    "cert_with_utf8_bom",
    "cert_with_windows_line_endings",
    "client_cert",
    "create_test_cli",
    "default_container_directory",
    "empty_cert",
    "external_ca_pem",
    "get_example_dir",
    "get_log_level_for_noisy_loggers",
    "get_noisy_loggers",
    "invalid_cert_pem",
    "invalid_key_pem",
    "isolated_cli_runner",
    "malformed_cert_pem",
    "mock_logger",
    "pytest_runtest_setup",
    "reset_foundation_setup_for_testing",
    "reset_foundation_state",
    "reset_test_environment",
    "server_cert",
    "set_log_stream_for_testing",
    "setup_foundation_telemetry_for_test",
    "suppress_loggers",
    "temp_config_file",
    "temporary_cert_file",
    "temporary_key_file",
    "valid_cert_pem",
    "valid_key_pem",
]
