#
# __init__.py
#
"""
Provide TestKit.

Unified testing utilities for the provide ecosystem with automatic context detection.
Comprehensive fixtures and utilities for testing Foundation-based applications.

Note: Testing information is displayed via pytest hooks in conftest.py
"""

from __future__ import annotations

import sys
from typing import Any

# ============================================================================
# Install setproctitle blocker IMMEDIATELY on package import
# ============================================================================
# This must happen BEFORE pytest-xdist (or any other tool) imports setproctitle.
# The blocker is installed at module load time to ensure it's active as early
# as possible in the Python startup sequence.
#
# Projects should import provide.testkit in their tests/conftest.py to ensure
# this blocker is installed before pytest initializes.
# ============================================================================

import os

# Ensure .pth file is installed (one-time setup, idempotent)
from provide.testkit._install_pth import install_pth_file
install_pth_file()  # Silently installs/symlinks if not present

# DEBUG: Track when this module is loaded
_pid = os.getpid()
_debug_file = f"/tmp/testkit-debug-{_pid}.log"
with open(_debug_file, "a") as f:
    f.write(f"🐛 [PID {_pid}] provide.testkit.__init__ is being imported\n")
    f.flush()

from provide.testkit.pytest_plugin import SetproctitleImportBlocker

if not any(isinstance(hook, SetproctitleImportBlocker) for hook in sys.meta_path):
    with open(_debug_file, "a") as f:
        f.write(f"🐛 [PID {_pid}] Installing SetproctitleImportBlocker (fallback)\n")
        f.flush()
    sys.meta_path.insert(0, SetproctitleImportBlocker())
else:
    with open(_debug_file, "a") as f:
        f.write(
            f"🐛 [PID {_pid}] SetproctitleImportBlocker already installed "
            f"(likely via .pth early init)\n"
        )
        f.flush()

# Mapping of attribute names to their modules for lazy loading.
_LAZY_IMPORTS = {
    # CLI testing utilities
    "cli.testing": [
        "MockContext",
        "isolated_cli_runner",
        "temp_config_file",
        "create_test_cli",
        "CliTestCase",
        "click_testing_mode",
    ],
    # CLI runner utilities
    "cli.runner": [
        "CliTestRunner",
        "assert_cli_success",
        "assert_cli_error",
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
    "streams.testing": ["set_log_stream_for_testing", "enable_file_logging_for_testing"],
    # Common fixture utilities
    "common.fixtures": [
        "captured_stderr_for_foundation",
        "setup_foundation_telemetry_for_test",
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
        "disable_setproctitle",
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
    "crypto.fixtures": [
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
    "hub.fixtures": ["default_container_directory", "isolated_container", "isolated_hub"],
    # Environment utilities
    "utils.environment": [
        "TestEnvironment",
        "get_example_dir",
        "add_src_to_path",
        "reset_test_environment",
    ],
    # Temp environment utilities
    "utils.temp_env": [
        "temp_env",
        "temp_env_from_dict",
        "isolated_env",
        "EnvContext",
    ],
    # Base test classes
    "base.foundation": [
        "FoundationTestCase",
    ],
    "base.minimal": [
        "MinimalTestCase",
    ],
    # Base harness utilities
    "base.harness": [
        "HarnessRunner",
    ],
    # Mocking utilities
    "mocking.fixtures": [
        "ANY",
        "AsyncMock",
        "DEFAULT",
        "MagicMock",
        "Mock",
        "PropertyMock",
        "assert_mock_calls",
        "async_mock_factory",
        "auto_patch",
        "call",
        "create_autospec",
        "magic_mock_factory",
        "mock_factory",
        "mock_open",
        "mock_open_fixture",
        "patch",
        "patch_fixture",
        "patch_multiple_fixture",
        "property_mock_factory",
        "seal",
        "sentinel",
        "spy_fixture",
    ],
    # Time mocking utilities
    "mocking.time": [
        "SleepTracker",
        "mock_sleep",
        "mock_time_sleep",
        "mock_asyncio_sleep",
        "create_sleep_mock",
    ],
    # Time fixture utilities
    "time.fixtures": [
        "time_machine",
        "freeze_time",
        "mock_datetime",
        "timer",
        "time_travel",
        "rate_limiter_mock",
        "benchmark_timer",
        "advance_time",
    ],
    # File temp utilities
    "file.temp": [
        "TempFileManager",
        "create_temp_file",
        "create_temp_dir",
    ],
}

# Submodules that can be imported directly
_DIRECT_SUBMODULES = [
    "archive",
    "base",
    "cli",
    "common",
    "crypto",
    "file",
    "hub",
    "mocking",
    "process",
    "streams",
    "threading",
    "time",
    "transport",
    "utils",
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


# --- Public API ---
# This list is dynamically generated to be comprehensive and stay in sync
# with the lazy loader, ensuring a complete and correct public API.
_all_lazy_attributes: list[str] = []
for _attributes in _LAZY_IMPORTS.values():
    _all_lazy_attributes.extend(_attributes)

__all__ = sorted(list(set(_all_lazy_attributes)))
