# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`provide-testkit` is a comprehensive testing utilities library for the provide ecosystem. It provides pytest fixtures, mocking utilities, and testing helpers organized by domain (file, process, transport, crypto, etc.) to support testing of Foundation-based applications.

## Development Environment Setup

## Common Development Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest                      # Run all tests
uv run pytest -n auto              # Run tests in parallel
uv run pytest -n auto -vvv         # Verbose parallel test run
uv run pytest tests/test_specific.py   # Run specific test file
uv run pytest -k "test_name"       # Run tests matching pattern

# Code quality checks
uv run ruff check .                # Run linter
uv run ruff format .               # Format code
uv run mypy src/                   # Type checking

# Build and distribution
uv build                           # Build package
uv publish                         # Publish to PyPI
```

## Architecture & Code Structure

### Core Design Philosophy

The testkit uses a modular, domain-organized fixture system with lazy loading to minimize import overhead in production environments. All fixtures are automatically imported and available from the main `provide.testkit` namespace.

### Domain-Organized Modules

1. **File Testing** (`src/provide/testkit/file/`)
   - `fixtures.py`: Core file and directory fixtures
   - `content_fixtures.py`: Text and binary content fixtures
   - `directory_fixtures.py`: Complex directory structure fixtures
   - `special_fixtures.py`: Special file types (symlinks, permissions, etc.)

2. **Process & Async Testing** (`src/provide/testkit/process/`)
   - `fixtures.py`: Main process testing utilities
   - `async_fixtures.py`: Async/await testing support
   - `subprocess_fixtures.py`: Subprocess mocking and testing

3. **Transport & Network** (`src/provide/testkit/transport/`)
   - `fixtures.py`: HTTP client mocking, free port utilities, WebSocket testing

4. **Threading Utilities** (`src/provide/testkit/threading/`)
   - `basic_fixtures.py`: Thread creation and management
   - `sync_fixtures.py`: Synchronization primitives (locks, events)
   - `execution_fixtures.py`: Thread pool and concurrent execution
   - `data_fixtures.py`: Thread-safe data structures

5. **Crypto Testing** (`src/provide/testkit/crypto.py`)
   - Certificate fixtures (client, server, CA certificates)
   - PEM format testing utilities
   - Certificate validation helpers

6. **Archive Testing** (`src/provide/testkit/archive/`)
   - Multi-format archive fixtures (zip, tar, etc.)
   - Compression testing utilities
   - Archive corruption simulation

7. **Time & Mocking** (`src/provide/testkit/time/`)
   - Time freezing and manipulation utilities
   - Clock mocking for deterministic tests

8. **Common Utilities** (`src/provide/testkit/common/`)
   - Configuration mocking
   - Event emitter testing
   - Cache and database mocking

### Lazy Loading System

The main `__init__.py` implements a sophisticated lazy loading system using `__getattr__` that:
- Detects testing context automatically
- Issues warnings when testing utilities are used in production
- Provides backward compatibility for legacy import patterns
- Minimizes production runtime overhead

### CLI Testing Support

Comprehensive CLI testing utilities in `cli.py`:
- `MockContext`: CLI context mocking with call tracking
- `isolated_cli_runner`: Isolated test environment for CLI commands
- `temp_config_file`: Temporary configuration file management
- `CliTestCase`: Base class for CLI testing

## Development Guidelines

- **Modern Python Typing**: Use Python 3.11+ type hints (`list[str]`, `dict[str, Any]`, etc.) - never `List`, `Dict`, `Optional`
- **No Inline Defaults**: All defaults must come from configuration files, constants, or environment variables
- **Absolute Imports**: Always use absolute imports, never relative imports
- **Foundation Integration**: Use Foundation logger (`from provide.foundation import logger`) for internal logging
- **Async Support**: Use async fixtures and tests where appropriate
- **No Backward Compatibility**: Implement target state directly without migration logic

## Testing Strategy

- All fixtures are pytest-compatible and follow pytest naming conventions
- Tests use `pytest-asyncio` for async support
- Parallel execution with `pytest-xdist` 
- Coverage tracking with `pytest-cov`
- Markers: `slow`, `integration`, `unit` for selective test execution

## Fixture Organization

Fixtures are organized by domain and automatically exported through the lazy loading system. Key fixture categories:

- **File fixtures**: `temp_directory`, `test_files_structure`, `binary_file`, etc.
- **Process fixtures**: `clean_event_loop`, `async_timeout`, `mock_async_process`, etc.
- **Transport fixtures**: `free_port`, `mock_server`, `httpx_mock_responses`, etc.
- **Crypto fixtures**: `client_cert`, `server_cert`, `ca_cert`, etc.
- **Threading fixtures**: Thread pools, locks, concurrent data structures
- **Common fixtures**: Configuration, event emitters, caches

## Environment Context Detection

The testkit automatically detects testing contexts through:
- pytest module presence
- `PYTEST_CURRENT_TEST` environment variable
- unittest module detection
- `TESTING=true` environment variable
- Command line argument analysis

## Optional Dependencies

The package supports optional extras for specific functionality:
- `transport`: HTTP client testing with httpx
- `crypto`: Cryptographic testing utilities
- `process`: Process monitoring with psutil
- `all`: All optional dependencies