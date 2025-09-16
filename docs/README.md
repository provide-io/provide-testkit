# provide-testkit Documentation

Welcome to the provide-testkit documentation! This directory contains comprehensive guides, API references, and examples for using the testing utilities throughout the provide.io ecosystem.

## Documentation Structure

```
docs/
├── README.md                    # This file
├── api/                         # API reference documentation
│   ├── file.md                 # File testing fixtures
│   ├── process.md              # Process and async testing
│   ├── transport.md            # Network and HTTP testing
│   ├── threading.md            # Threading and concurrency
│   ├── crypto.md               # Cryptography testing
│   ├── archive.md              # Archive format testing
│   ├── time.md                 # Time manipulation
│   └── cli.md                  # CLI testing utilities
├── guides/                      # User guides and tutorials
│   ├── getting-started.md      # Quick start guide
│   ├── fixture-organization.md # How fixtures are organized
│   ├── testing-patterns.md     # Common testing patterns
│   ├── async-testing.md        # Async/await testing guide
│   └── custom-fixtures.md      # Creating custom fixtures
└── examples/                   # Detailed examples
    ├── basic-usage.md          # Basic fixture usage
    ├── file-operations.md      # File testing examples
    ├── async-patterns.md       # Async testing examples
    ├── network-testing.md      # Network testing examples
    └── integration-tests.md    # Integration testing examples
```

## Quick Navigation

### 🚀 Getting Started
- **[Getting Started Guide](guides/getting-started.md)**: Your first steps with provide-testkit
- **[Basic Usage Examples](examples/basic-usage.md)**: Simple examples to get you started

### 📚 Core Concepts
- **[Fixture Organization](guides/fixture-organization.md)**: How fixtures are organized by domain
- **[Testing Patterns](guides/testing-patterns.md)**: Common patterns and best practices
- **[Async Testing](guides/async-testing.md)**: Working with async/await in tests

### 🔧 API Reference
- **[File Testing](api/file.md)**: Directory structures, file content, permissions
- **[Process Testing](api/process.md)**: Async operations, subprocess mocking
- **[Transport Testing](api/transport.md)**: HTTP clients, mock servers, network utilities
- **[Threading Testing](api/threading.md)**: Thread pools, locks, concurrent data structures
- **[Crypto Testing](api/crypto.md)**: Certificates, keys, cryptographic operations
- **[Archive Testing](api/archive.md)**: Archive creation, extraction, validation
- **[Time Testing](api/time.md)**: Clock mocking, time manipulation
- **[CLI Testing](api/cli.md)**: Command-line interface testing utilities
- **[Quality Analysis](quality/quality_guide.md)**: Code quality analysis and gates

### 💡 Examples
- **[File Operations](examples/file-operations.md)**: Testing file and directory operations
- **[Async Patterns](examples/async-patterns.md)**: Async testing patterns and examples
- **[Network Testing](examples/network-testing.md)**: HTTP clients, servers, and protocols
- **[Integration Tests](examples/integration-tests.md)**: Cross-component testing
- **[Quality Examples](../examples/quality/)**: Quality analysis demonstrations

### 🛠️ Advanced Topics
- **[Custom Fixtures](guides/custom-fixtures.md)**: Creating domain-specific fixtures
- **[Performance Testing](guides/performance-testing.md)**: Benchmarking and performance validation
- **[Cross-Platform Testing](guides/cross-platform.md)**: Testing across different platforms

## Fixture Categories

### File Domain
Test filesystem operations, directory structures, and file content:

```python
def test_file_operations(temp_directory, test_files_structure):
    # Test with temporary files and directories
    config_file = temp_directory / "config.json"
    config_file.write_text('{"debug": true}')

    # Use predefined file structures
    assert test_files_structure["README.md"].exists()
```

### Process Domain
Test async operations, subprocesses, and event loops:

```python
@pytest.mark.asyncio
async def test_async_operation(clean_event_loop, async_timeout):
    # Test async operations with clean event loop
    async with async_timeout(5.0):
        result = await some_async_operation()
        assert result.success
```

### Transport Domain
Test network operations, HTTP clients, and mock servers:

```python
def test_api_client(mock_server, httpx_mock_responses):
    # Test with mock HTTP server
    mock_server.add_response("/api/users", {"users": []})

    client = APIClient(base_url=mock_server.url)
    users = client.get_users()
    assert users == []
```

### Threading Domain
Test concurrent operations and thread safety:

```python
def test_concurrent_access(thread_pool, shared_counter):
    # Test thread-safe operations
    futures = [
        thread_pool.submit(increment_counter, shared_counter)
        for _ in range(10)
    ]

    for future in futures:
        future.result()

    assert shared_counter.value == 10
```

### Crypto Domain
Test cryptographic operations and certificate handling:

```python
def test_certificate_validation(client_cert, server_cert, ca_cert):
    # Test with generated certificates
    assert validate_certificate_chain(client_cert, ca_cert)
    assert not validate_certificate_chain(client_cert, server_cert)
```

## Integration with Testing Frameworks

### pytest Integration
All fixtures are designed to work seamlessly with pytest:

```python
import pytest
from provide.testkit import temp_directory, mock_server

def test_with_fixtures(temp_directory, mock_server):
    """Test using multiple testkit fixtures."""
    # Fixtures are automatically injected
    config_file = temp_directory / "config.json"
    config_file.write_text('{"api_url": "' + mock_server.url + '"}')

    # Test your application
    app = MyApp(config_file)
    assert app.config.api_url == mock_server.url
```

### Hypothesis Integration
Property-based testing with Hypothesis:

```python
from hypothesis import given, strategies as st
from provide.testkit import temp_directory

@given(st.text())
def test_file_content_roundtrip(content, temp_directory):
    """Test that file content survives write/read roundtrip."""
    test_file = temp_directory / "test.txt"
    test_file.write_text(content)
    assert test_file.read_text() == content
```

### asyncio Integration
Async testing with pytest-asyncio:

```python
import pytest
from provide.testkit import clean_event_loop, async_timeout

@pytest.mark.asyncio
async def test_async_operation(clean_event_loop):
    """Test async operations with clean event loop."""
    async with async_timeout(10.0):
        result = await long_running_operation()
        assert result.success
```

## Best Practices

### Fixture Selection
Choose the right fixtures for your testing needs:

- **Specific fixtures**: Use specific fixtures when you know exactly what you need
- **General fixtures**: Use general fixtures for common scenarios
- **Composite fixtures**: Combine fixtures for complex test scenarios

### Performance Considerations
- **Lazy loading**: Fixtures are loaded only when needed
- **Scope management**: Use appropriate fixture scopes (function, class, module, session)
- **Resource cleanup**: All fixtures handle cleanup automatically

### Testing Patterns
- **Arrange-Act-Assert**: Structure tests clearly
- **Given-When-Then**: Use BDD patterns where appropriate
- **Test isolation**: Each test should be independent

## Migration Guide

### From Standard Testing
If you're migrating from standard Python testing utilities:

```python
# Before: Manual setup and cleanup
import tempfile
import shutil
from pathlib import Path

def test_file_operation():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        # Test logic here
    finally:
        shutil.rmtree(temp_dir)

# After: Using provide-testkit
from provide.testkit import temp_directory

def test_file_operation(temp_directory):
    test_file = temp_directory / "test.txt"
    test_file.write_text("content")
    # Test logic here
    # Cleanup handled automatically
```

### From Other Testing Libraries
Integration with popular testing libraries:

```python
# From unittest.mock
from unittest.mock import Mock, patch
from provide.testkit import mock_server

def test_with_mock_server(mock_server):
    # More realistic than pure mocks
    mock_server.add_response("/api/data", {"key": "value"})

# From responses library
import responses
from provide.testkit import httpx_mock_responses

def test_with_httpx_mock(httpx_mock_responses):
    # Type-safe, async-compatible HTTP mocking
    httpx_mock_responses.add("GET", "/api/data", json={"key": "value"})
```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're importing from the correct module
2. **Fixture not found**: Check that the fixture is available in your test scope
3. **Cleanup issues**: Fixtures handle cleanup automatically, but check for resource leaks
4. **Platform differences**: Some fixtures behave differently on different platforms

### Debugging Tips

```python
# Enable debug logging for testkit
import logging
logging.getLogger("provide.testkit").setLevel(logging.DEBUG)

# Use pytest verbose mode
pytest tests/ -v -s

# Debug specific fixtures
pytest tests/test_my_feature.py::test_specific_case -vvv
```

## Contributing

Want to contribute to provide-testkit? See our [Contributing Guide](../CONTRIBUTING.md) for:

- Development setup
- Adding new fixtures
- Testing guidelines
- Documentation standards

## Support

- **Documentation**: This documentation covers most use cases
- **Examples**: Check the examples directory for working code
- **Issues**: Report bugs or request features on GitHub
- **Discussions**: Ask questions in GitHub Discussions

---

Ready to start testing? Begin with the [Getting Started Guide](guides/getting-started.md) or jump into [Basic Usage Examples](examples/basic-usage.md)!