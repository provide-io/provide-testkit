# provide-testkit Examples

This directory contains practical examples demonstrating how to use provide-testkit fixtures in real-world testing scenarios. Each example is a complete, runnable test that you can use as a reference for your own tests.

## Example Categories

### 🚀 Getting Started
- **[basics/basic_usage.py](basics/basic_usage.py)**: Simple examples showing core fixture usage
- **[basics/first_test.py](basics/first_test.py)**: Your first test using provide-testkit

### 🔍 Quality Analysis
- **[quality/framework_demo.py](quality/framework_demo.py)**: Quality framework demonstration
- **[quality/decorators_demo.py](quality/decorators_demo.py)**: Quality decorators examples
- **[quality/generate_reports.py](quality/generate_reports.py)**: Report generation examples

### 📁 File and Directory Testing
- **[file/file_testing.py](file/file_testing.py)**: Testing file creation, reading, and manipulation
- **[file/advanced_file_operations.py](file/advanced_file_operations.py)**: Working with complex file workflows

### ⚡ Async Testing
- **[async/async_testing.py](async/async_testing.py)**: Testing async/await operations

### 🌐 Network and Transport Testing
- **[network/http_testing.py](network/http_testing.py)**: Testing HTTP clients with mock servers

### 💻 CLI and Command-Line Testing
- **[cli/cli_testing.py](cli/cli_testing.py)**: Testing command-line applications

### 🧩 Patterns
- **[patterns/mocking_patterns.py](patterns/mocking_patterns.py)**: Mocking and test organization patterns

### 🔐 Security
- **[security_scan_example.py](security_scan_example.py)**: Security scan fixtures and reporting

## Running Examples

### Prerequisites
```bash
# Install provide-testkit with development dependencies
uv add provide-testkit[dev]

# Or use the ecosystem setup
cd /path/to/provide-io
uv sync --all-groups
source .venv/bin/activate
```

### Running Individual Examples
```bash
# Run a specific example
pytest examples/basics/basic_usage.py -v

# Run all examples in a category
pytest examples/file/file_testing.py examples/file/advanced_file_operations.py -v

# Run with output capture disabled (to see print statements)
pytest examples/basics/basic_usage.py -v -s
```

### Running All Examples
```bash
# Run all examples
pytest examples/ -v

# Run with coverage
pytest examples/ --cov=provide.testkit --cov-report=term-missing

# Run in parallel
pytest examples/ -n auto
```

## Example Structure

Each example follows a consistent structure:

```python
"""
Example: [Title]

Description of what this example demonstrates.

Key fixtures used:
- fixture_name: Description of what it provides
- another_fixture: Description of what it provides

Learning objectives:
- What you'll learn from this example
- Key concepts demonstrated
"""

import pytest
from provide.testkit import fixture_name, another_fixture

# Example tests with clear documentation

def test_example_functionality(fixture_name):
    """Test demonstrating fixture usage."""
    # Arrange: Set up test data
    test_data = "example"

    # Act: Perform the operation being tested
    result = process_data(test_data)

    # Assert: Verify the expected outcome
    assert result == "expected_result"

# Additional tests showing different aspects
```

## Key Learning Paths

### Path 1: Testing Basics
1. **[basics/basic_usage.py](basics/basic_usage.py)**: Start here for fundamental concepts
2. **[file/file_testing.py](file/file_testing.py)**: Learn file testing patterns
3. **[async/async_testing.py](async/async_testing.py)**: Understand async testing

### Path 2: Quality & Reporting
1. **[quality/framework_demo.py](quality/framework_demo.py)**: Quality framework overview
2. **[quality/decorators_demo.py](quality/decorators_demo.py)**: Quality decorators in action
3. **[quality/generate_reports.py](quality/generate_reports.py)**: Report generation workflow

### Path 3: CLI & Automation
1. **[cli/cli_testing.py](cli/cli_testing.py)**: Command-line application testing
2. **[patterns/mocking_patterns.py](patterns/mocking_patterns.py)**: Mocking and organization patterns
3. **[security_scan_example.py](security_scan_example.py)**: Security scan fixtures

## Common Patterns

### Pattern 1: Fixture Composition
Combining multiple fixtures for complex scenarios:

```python
def test_complex_scenario(temp_directory, mock_server, client_cert):
    """Test combining multiple fixtures."""
    # Use temp_directory for file operations
    config_file = temp_directory / "config.json"
    config_file.write_text(f'{{"server_url": "{mock_server.url}"}}')

    # Use mock_server for HTTP operations
    mock_server.add_response("/api/data", {"status": "ok"})

    # Use client_cert for TLS operations
    client = SecureClient(config_file, certificate=client_cert)
    response = client.fetch_data()

    assert response["status"] == "ok"
```

### Pattern 2: Parameterized Testing
Using fixtures with parametrization:

```python
@pytest.mark.parametrize("file_format", ["json", "yaml", "toml"])
def test_config_formats(temp_directory, file_format):
    """Test configuration loading with different formats."""
    config_file = temp_directory / f"config.{file_format}"

    if file_format == "json":
        config_file.write_text('{"debug": true}')
    elif file_format == "yaml":
        config_file.write_text('debug: true')
    elif file_format == "toml":
        config_file.write_text('debug = true')

    config = load_config(config_file)
    assert config.debug is True
```

### Pattern 3: Async Context Management
Proper async testing patterns:

```python
@pytest.mark.asyncio
async def test_async_context(clean_event_loop, async_timeout):
    """Test async operations with proper context management."""
    async with async_timeout(10.0):
        # Perform async operations
        client = AsyncClient()
        async with client:
            result = await client.fetch_data()
            assert result.success
```

## Troubleshooting Examples

### Common Issues and Solutions

1. **Fixture Not Found**
   ```python
   # Problem: ImportError or fixture not recognized
   from provide.testkit import unknown_fixture  # ❌

   # Solution: Check available fixtures
   from provide.testkit import temp_directory  # ✅
   ```

2. **Async Test Issues**
   ```python
   # Problem: Async test not running properly
   def test_async_operation():  # ❌
       result = await some_async_function()

   # Solution: Use proper async test decorator
   @pytest.mark.asyncio  # ✅
   async def test_async_operation():
       result = await some_async_function()
   ```

3. **Resource Cleanup**
   ```python
   # Problem: Manual cleanup required
   def test_with_manual_cleanup():  # ❌
       temp_dir = create_temp_directory()
       try:
           # Test logic
           pass
       finally:
           cleanup_temp_directory(temp_dir)

   # Solution: Use fixtures for automatic cleanup
   def test_with_automatic_cleanup(temp_directory):  # ✅
       # Test logic - cleanup is automatic
       pass
   ```

## Performance Tips

### Optimize Test Execution
```python
# Use session-scoped fixtures for expensive setup
@pytest.fixture(scope="session")
def expensive_resource():
    """Create expensive resource once per session."""
    resource = create_expensive_resource()
    yield resource
    cleanup_expensive_resource(resource)

# Use function-scoped fixtures for isolation
@pytest.fixture(scope="function")
def isolated_resource():
    """Create fresh resource for each test."""
    return create_fresh_resource()
```

### Parallel Testing
```python
# Mark tests that can run in parallel
@pytest.mark.parallel
def test_independent_operation(temp_directory):
    """This test can run in parallel with others."""
    pass

# Mark tests that must run serially
@pytest.mark.serial
def test_shared_resource():
    """This test must run alone."""
    pass
```

## Best Practices from Examples

1. **Clear Test Names**: Use descriptive test names that explain what is being tested
2. **Good Documentation**: Include docstrings explaining the test purpose
3. **Arrange-Act-Assert**: Structure tests with clear sections
4. **Fixture Reuse**: Leverage fixtures instead of manual setup/teardown
5. **Error Testing**: Include tests for error conditions and edge cases
6. **Performance Awareness**: Use appropriate fixture scopes for performance

## Contributing Examples

Want to contribute an example? Follow these guidelines:

1. **Clear Purpose**: Each example should demonstrate specific fixture usage
2. **Complete Code**: Examples should be runnable without modification
3. **Good Comments**: Explain what each part of the test does
4. **Follow Patterns**: Use the established example structure
5. **Test Coverage**: Include both success and failure scenarios

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed contribution guidelines.

---

Ready to explore? Start with [basics/basic_usage.py](basics/basic_usage.py) or pick an example that matches your testing needs!
