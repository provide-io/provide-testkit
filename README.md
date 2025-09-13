# Provide TestKit

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Testing](https://img.shields.io/badge/testing-pytest-green.svg)

**Comprehensive testing utilities and fixtures for the [provide ecosystem](https://github.com/provide-io)**

TestKit provides a unified testing framework designed specifically for applications built with `provide-foundation`. It offers intelligent context detection, extensive fixture libraries, and seamless integration with popular testing frameworks.

## ✨ Key Features

- 🔍 **Smart Context Detection** - Automatically detects testing environments
- 🏗️ **Foundation Integration** - Native support for provide-foundation components
- 🧪 **Comprehensive Fixtures** - Pre-built fixtures for common testing scenarios
- 🚀 **CLI Testing Support** - Advanced utilities for testing Click-based applications
- 🔐 **Crypto Testing** - Certificate and key generation utilities
- 🌐 **Transport Mocking** - HTTP, WebSocket, and network testing tools
- 📁 **File System Utilities** - Temporary files, directories, and archive testing
- ⚡ **Async Support** - Full async/await testing capabilities
- 🧵 **Thread Safety Testing** - Multi-threading test utilities

## 📦 Installation

### Basic Installation
```bash
pip install provide-testkit
```

### With Optional Dependencies
```bash
# Transport testing (HTTP, WebSocket)
pip install provide-testkit[transport]

# Crypto testing (certificates, keys)
pip install provide-testkit[crypto]  

# Process testing (async, subprocess)
pip install provide-testkit[process]

# Everything
pip install provide-testkit[all]
```

### Development Installation
```bash
git clone https://github.com/provide-io/provide-testkit
cd provide-testkit
pip install -e ".[all,dev]"
```

## 🚀 Quick Start

### Basic Foundation Testing
```python
import pytest
from provide.testkit import (
    reset_foundation_setup_for_testing,
    set_log_stream_for_testing, 
    MockContext
)

@pytest.fixture(autouse=True)
def reset_foundation():
    """Reset Foundation state before each test."""
    reset_foundation_setup_for_testing()

def test_foundation_logger():
    """Test Foundation logger functionality."""
    import sys
    from provide.foundation import logger
    
    # Capture Foundation logs to stderr for testing
    set_log_stream_for_testing(sys.stderr)
    
    logger.info("Test message", component="test")
    # Test assertions here...
```

### CLI Testing
```python
from provide.testkit import MockContext, isolated_cli_runner, temp_config_file
import click

@click.command()
@click.pass_context  
def my_command(ctx):
    """Sample CLI command."""
    click.echo(f"Profile: {ctx.obj.profile}")

def test_cli_command():
    """Test CLI command with mock context."""
    # Create isolated CLI runner with temporary environment
    with isolated_cli_runner() as runner:
        # Create mock context
        mock_ctx = MockContext(profile="test-profile")
        
        # Run command with mock context
        result = runner.invoke(my_command, obj=mock_ctx)
        
        assert result.exit_code == 0
        assert "Profile: test-profile" in result.output
```

### Configuration Testing
```python
from provide.testkit import temp_config_file
from provide.foundation.config import TelemetryConfig

def test_config_loading():
    """Test configuration loading from file."""
    config_data = {
        "service_name": "test-service",
        "logging": {
            "default_level": "DEBUG"
        }
    }
    
    # Create temporary config file
    with temp_config_file(config_data, format="toml") as config_path:
        config = TelemetryConfig.from_file(config_path)
        assert config.service_name == "test-service"
        assert config.logging.default_level == "DEBUG"
```

## 📚 Core Components

### 🔍 Context Detection

TestKit automatically detects testing environments and provides appropriate warnings:

```python
from provide.testkit import _is_testing_context

# Automatically detects pytest, unittest, or TESTING=true environment
if _is_testing_context():
    print("Running in test mode!")
```

### 🧪 Foundation Integration

Seamless integration with Foundation's logging and configuration systems:

```python
from provide.testkit import (
    reset_foundation_setup_for_testing,
    setup_foundation_telemetry_for_test,
    captured_stderr_for_foundation
)

# Reset Foundation state
reset_foundation_setup_for_testing()

# Setup telemetry for testing
setup_foundation_telemetry_for_test(service_name="test-app")

# Capture Foundation logs
with captured_stderr_for_foundation() as captured:
    # Your test code here
    assert "expected log message" in captured
```

### 🏗️ Fixture Categories

TestKit organizes fixtures into logical categories:

#### CLI Testing
```python
from provide.testkit import (
    MockContext,           # Mock CLI context with tracking
    isolated_cli_runner,   # Isolated Click test runner
    temp_config_file,      # Temporary configuration files
    create_test_cli,       # CLI application factory
)
```

#### File System Testing
```python  
from provide.testkit.file import (
    temp_directory,        # Temporary directories
    temp_file,            # Temporary files
    binary_file,          # Binary test files
    readonly_file,        # Read-only files
    nested_directory_structure,  # Complex directory structures
)
```

#### Transport Testing
```python
from provide.testkit.transport import (
    free_port,            # Find available ports
    mock_server,          # Mock HTTP servers
    httpx_mock_responses, # HTTP response mocking
    mock_websocket,       # WebSocket mocking
)
```

#### Crypto Testing
```python
from provide.testkit import (
    client_cert,          # Client certificates
    server_cert,          # Server certificates  
    ca_cert,             # Certificate authorities
    temporary_cert_file, # Temporary cert files
)
```

#### Process Testing
```python
from provide.testkit.process import (
    clean_event_loop,     # Clean async event loops
    async_timeout,        # Async operation timeouts
    mock_async_process,   # Subprocess mocking
)
```

## 🎯 Advanced Usage

### Custom Test Environment

```python
from provide.testkit import TestEnvironment

class MyTestEnvironment(TestEnvironment):
    """Custom test environment with app-specific setup."""
    
    def setup(self):
        """Setup custom test environment."""
        super().setup()
        # Your custom setup here
        self.setup_database()
        self.setup_cache()
    
    def teardown(self):
        """Cleanup custom test environment."""  
        self.cleanup_database()
        self.cleanup_cache()
        super().teardown()

# Usage in tests
@pytest.fixture
def test_env():
    """Provide custom test environment."""
    env = MyTestEnvironment()
    env.setup()
    yield env
    env.teardown()
```

### Integration Testing

```python
from provide.testkit import (
    MockContext,
    mock_telemetry_config,
    mock_transport,
    free_port
)

@pytest.mark.integration
async def test_full_application():
    """Integration test with full application stack."""
    # Setup mock configuration
    config = mock_telemetry_config(
        service_name="integration-test",
        log_level="DEBUG"
    )
    
    # Get free port for test server
    port = free_port()
    
    # Mock transport layer
    with mock_transport() as transport:
        # Your integration test here
        pass
```

### Performance Testing

```python
from provide.testkit.time import (
    mock_time,
    time_travel,
    performance_timer
)

def test_performance():
    """Test performance with timing utilities."""
    with performance_timer() as timer:
        # Your performance-critical code
        result = expensive_operation()
    
    # Assert performance requirements
    assert timer.elapsed < 1.0  # Less than 1 second
    assert result is not None

def test_time_dependent_behavior():
    """Test time-dependent behavior."""
    with mock_time() as mock:
        # Travel to specific time
        mock.travel_to("2024-01-01T00:00:00Z")
        
        # Test time-dependent logic
        result = time_sensitive_function()
        assert result.date == "2024-01-01"
```

## 🔧 Configuration

### Environment Variables

TestKit respects several environment variables:

```bash
# Suppress testing warnings
export FOUNDATION_SUPPRESS_TESTING_WARNINGS=1

# Enable testing mode explicitly
export TESTING=true

# Control pytest behavior  
export PYTEST_CURRENT_TEST="test_module.py::test_function"
```

### pytest Configuration

Add to your `pytest.ini` or `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
markers = [
    "integration: marks tests as integration tests",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

## 📖 API Reference

### Core Functions

#### Context Management
- `reset_foundation_setup_for_testing()` - Reset Foundation state
- `set_log_stream_for_testing(stream)` - Direct Foundation logs to stream
- `MockContext(**kwargs)` - Create mock CLI context

#### File Operations
- `temp_file(content, suffix)` - Create temporary file
- `temp_directory()` - Create temporary directory  
- `temp_config_file(data, format)` - Create temporary config file

#### CLI Testing
- `isolated_cli_runner()` - Isolated Click test runner
- `create_test_cli(commands)` - Create test CLI application

#### Transport Testing
- `free_port()` - Find available network port
- `mock_server(responses)` - Create mock HTTP server

### Fixture Categories

TestKit provides fixtures in these categories:

- **`provide.testkit.cli`** - CLI testing utilities
- **`provide.testkit.file`** - File system fixtures
- **`provide.testkit.transport`** - Network/HTTP fixtures
- **`provide.testkit.process`** - Async/subprocess fixtures
- **`provide.testkit.crypto`** - Certificate/key fixtures
- **`provide.testkit.time`** - Time manipulation utilities
- **`provide.testkit.mocking`** - General mocking utilities

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/provide-io/provide-testkit
cd provide-testkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install in development mode
pip install -e ".[all,dev]"

# Run tests
pytest

# Run type checking
mypy src/

# Run linting
ruff check src/
ruff format src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m "not slow"          # Skip slow tests
pytest -m integration         # Only integration tests

# Run with coverage
pytest --cov=src --cov-report=html

# Run in parallel
pytest -n auto
```

## 📄 License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

## 🔗 Related Projects

- [**provide-foundation**](https://github.com/provide-io/provide-foundation) - Core telemetry and logging library
- [**provide ecosystem**](https://github.com/provide-io) - Complete provide.io toolkit

## 📞 Support

- 📚 [Documentation](https://github.com/provide-io/provide-testkit/wiki)
- 🐛 [Issue Tracker](https://github.com/provide-io/provide-testkit/issues)  
- 💬 [Discussions](https://github.com/provide-io/provide-testkit/discussions)

---

<p align="center">
  <strong>TestKit</strong> • Part of the <a href="https://github.com/provide-io">provide.io</a> ecosystem
</p>