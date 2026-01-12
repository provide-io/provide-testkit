# AGENTS.md

This file provides guidance for AI assistants when working with code in this repository.

## Project Overview

`provide-testkit` is a comprehensive testing utilities library for the provide ecosystem. It provides pytest fixtures, mocking utilities, and testing helpers organized by domain (file, process, transport, crypto, etc.) to support testing of Foundation-based applications.

## Development Environment Setup

## Task Runner

This project uses `wrknv` for task automation. Commands are defined in `wrknv.toml`.

### Quick Reference
```bash
we tasks             # List all available tasks
we run test          # Run tests
we run lint          # Check code quality
we run format        # Format code
we run typecheck     # Type checking
we run build         # Build package
```

All tasks can be run with `we run <task>`. Nested tasks use dotted names (e.g., `we run test.coverage`).

### Task Discovery

Run `we tasks` to see the complete task tree for this project. Common task hierarchies:

```bash
we run test                # Run all tests
we run test.parallel       # Run tests in parallel
we run test.coverage       # Run tests with coverage
```

## Common Development Commands

```bash
# Environment setup
uv sync                            # Install dependencies

# Primary workflow (using we)
we run test                        # Run all tests
we run test.coverage               # Run with coverage report
we run test.parallel               # Run tests in parallel
we run lint                        # Check code quality
we run lint.fix                    # Auto-fix linting issues
we run format                      # Format code
we run format.check                # Check formatting without changes
we run typecheck                   # Run type checker
we run build                       # Build distribution

# Alternative (direct uv commands)
uv run pytest                      # Direct test execution
uv run pytest -n auto              # Run tests in parallel
uv run pytest -n auto -vvv         # Verbose parallel test run
uv run pytest tests/test_specific.py   # Run specific test file
uv run pytest -k "test_name"       # Run tests matching pattern
uv run ruff check .                # Direct linting
uv run ruff format .               # Direct formatting
uv run mypy src/                   # Direct type checking

# Publishing
uv publish                         # Publish to PyPI
```

For complete task documentation, see [wrknv.toml](wrknv.toml) or run `we tasks`.

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

### setproctitle Blocker (.pth File Approach)

The testkit uses a `.pth` file (`provide_testkit_init.pth`) to install a setproctitle import blocker **during Python's site initialization**, before pytest or any other code runs. This prevents macOS UX freezing issues with pytest-xdist.

**How it works:**
1. **Installation**: The `.pth` file is installed to `site-packages/` when the package is installed
2. **Early Execution**: Python executes `.pth` imports during site initialization (before user code)
3. **Smart Detection**: `_early_init.py` detects testing context and conditionally installs the blocker
4. **Import Blocking**: `SetproctitleImportBlocker` intercepts setproctitle imports via `sys.meta_path`
5. **Fallback Layers**: pytest11 entry point and `__init__.py` provide fallback if .pth file fails

**Key files:**
- `src/provide_testkit_init.pth`: Single-line import executed at Python startup
- `src/provide/testkit/_early_init.py`: Smart detection and blocker installation
- `src/provide/testkit/pytest_plugin.py`: SetproctitleImportBlocker implementation

**Benefits:**
- Automatic activation - no manual configuration needed
- Works before pytest loads (earlier than entry points or conftest.py)
- Per-virtualenv (installed/removed with package)
- Prevents macOS terminal freezing with pytest-xdist

**Note**: The blocker only activates in testing contexts (pytest/test in argv or PYTEST_* env vars) to minimize overhead for non-test Python scripts.

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
