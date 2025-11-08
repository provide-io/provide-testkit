# Quick Start

Get started with Provide TestKit in 5 minutes.

## Your First Test

Create a simple test using Provide TestKit fixtures:

```python
from provide.testkit import fixtures

def test_with_temp_directory(fixtures.temp_directory):
    """Test using a temporary directory fixture."""
    # The fixture provides a clean temporary directory
    test_file = fixtures.temp_directory / "test.txt"
    test_file.write_text("Hello, TestKit!")

    assert test_file.exists()
    assert test_file.read_text() == "Hello, TestKit!"

    # Directory is automatically cleaned up after the test
```

## Common Testing Patterns

### Using Built-in Fixtures

Provide TestKit offers many pre-built fixtures:

```python
from provide.testkit import fixtures

def test_temp_file(fixtures.temp_file):
    """Test with a temporary file."""
    fixtures.temp_file.write_text("test data")
    assert fixtures.temp_file.read_text() == "test data"

def test_temp_directory(fixtures.temp_directory):
    """Test with a temporary directory."""
    (fixtures.temp_directory / "file.txt").touch()
    assert (fixtures.temp_directory / "file.txt").exists()
```

### Testing Processes

Test subprocess and service interactions:

```python
from provide.testkit.process import ProcessTestCase

class TestMyService(ProcessTestCase):
    def test_service_startup(self):
        """Test that a service starts correctly."""
        process = self.start_process(["my-service", "--port", "8080"])

        # Wait for service to be ready
        self.wait_for_ready(process)

        # Test the service
        assert process.poll() is None  # Still running

        # Clean shutdown
        self.stop_process(process)
```

### File System Operations

Test file system interactions safely:

```python
from provide.testkit import fixtures

def test_file_operations(fixtures.temp_directory):
    """Test file system operations in isolation."""
    # Create test structure
    test_dir = fixtures.temp_directory / "subdir"
    test_dir.mkdir()

    test_file = test_dir / "data.json"
    test_file.write_text('{"key": "value"}')

    # Verify
    assert test_dir.exists()
    assert test_file.exists()
    assert '"key"' in test_file.read_text()
```

## Using Quality Tools

Test code quality with built-in tools:

```python
from provide.testkit.quality import coverage_gate

@coverage_gate(80.0)
def test_coverage_requirement():
    """This test requires 80% code coverage."""
    # Your test implementation
    # Coverage is automatically tracked and verified
    pass
```

## What's Available

Provide TestKit provides testing utilities for:

- **Fixtures**: Temporary files, directories, and resources
- **Process Management**: Subprocess testing and service mocking
- **Transport Testing**: Network communication mocking
- **File System**: Safe file operation testing
- **Quality Tools**: Coverage, security, complexity analysis

## Next Steps

### Learn More

- **[API Reference](../api/index/)** - Complete API documentation
- **[Quality Guide](../quality_guide/)** - Code quality and security testing
- **[GitHub Repository](https://github.com/provide-io/provide-testkit)** - Source code and examples

### Common Use Cases

- **Testing CLI applications** - Use process fixtures
- **Testing file operations** - Use file system fixtures
- **Code quality gates** - Use quality decorators
- **Service integration tests** - Use process management tools

### Example Projects

See how Provide TestKit is used in other Provide projects:
- [provide-foundation](https://github.com/provide-io/provide-foundation) - Core framework testing
- [pyvider](https://github.com/provide-io/pyvider) - Provider testing patterns
- [flavorpack](https://github.com/provide-io/flavorpack) - Packaging system tests
