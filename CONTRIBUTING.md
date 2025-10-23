# Contributing to provide-testkit

Thank you for your interest in contributing to provide-testkit! This package provides the testing foundation for the entire provide.io ecosystem, so your contributions help improve testing across all projects.

## Development Setup

### Prerequisites
- Python 3.11 or higher
- UV package manager
- Git

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/provide-io/provide-testkit.git
cd provide-testkit

# Set up development environment
uv sync  # This creates workenv/ and installs dependencies

# Verify setup
pytest tests/
```

### Alternative Setup (Ecosystem Development)
If you're working on the entire ecosystem:
```bash
# From the provide-io root directory
cd /path/to/provide-io
uv sync --extra all --extra dev
source .venv/bin/activate
```

## Project Structure

```
provide-testkit/
├── src/provide/testkit/           # Main package
│   ├── __init__.py               # Lazy loading and exports
│   ├── common/                   # Common utilities and base classes
│   ├── file/                     # File and directory testing
│   ├── process/                  # Process and async testing
│   ├── transport/                # Network and HTTP testing
│   ├── threading/                # Threading and concurrency testing
│   ├── crypto.py                 # Cryptography testing
│   ├── archive/                  # Archive format testing
│   ├── time/                     # Time manipulation utilities
│   └── cli.py                    # CLI testing support
├── tests/                        # Test suite
├── docs/                         # Documentation
├── examples/                     # Usage examples
├── README.md                     # Project overview
├── CHANGELOG.md                  # Version history
├── CONTRIBUTING.md               # This file
└── pyproject.toml               # Package configuration
```

## Testing Philosophy

### Domain Organization
Fixtures are organized by domain to make them easy to find and use:

- **File domain**: Everything related to files, directories, and filesystem operations
- **Process domain**: Async operations, subprocesses, event loops
- **Transport domain**: Network operations, HTTP clients, mock servers
- **Threading domain**: Concurrency, thread pools, synchronization
- **Crypto domain**: Certificates, keys, cryptographic operations
- **Archive domain**: Archive creation, extraction, validation
- **Time domain**: Clock mocking, time manipulation

### Lazy Loading
The package uses lazy loading to minimize production overhead:

```python
# __init__.py uses __getattr__ for lazy loading
def __getattr__(name: str):
    if name in _fixture_map:
        return _load_fixture(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

This ensures that importing testkit in production doesn't load testing dependencies.

### Testing Context Detection
The system automatically detects testing contexts:

```python
def is_testing_context() -> bool:
    """Detect if we're in a testing environment."""
    indicators = [
        lambda: "pytest" in sys.modules,
        lambda: os.getenv("PYTEST_CURRENT_TEST") is not None,
        lambda: os.getenv("TESTING") == "true",
        lambda: "unittest" in sys.modules,
        lambda: any("test" in arg for arg in sys.argv)
    ]
    return any(indicator() for indicator in indicators)
```

## Contribution Guidelines

### Adding New Fixtures

1. **Choose the right domain**: Place fixtures in the appropriate domain directory
2. **Follow naming conventions**: Use descriptive names that indicate what the fixture provides
3. **Include comprehensive docstrings**: Document parameters, return values, and usage examples
4. **Add tests**: Every fixture should have tests demonstrating its usage
5. **Update exports**: Add new fixtures to the appropriate `__all__` list

Example fixture:

```python
import pytest
from pathlib import Path
from typing import Generator

@pytest.fixture
def temp_config_file() -> Generator[Path, None, None]:
    """Create a temporary configuration file.

    Returns:
        Path to a temporary configuration file that will be cleaned up after the test.

    Example:
        ```python
        def test_config_loading(temp_config_file):
            temp_config_file.write_text('{"debug": true}')
            config = load_config(temp_config_file)
            assert config.debug is True
        ```
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = Path(f.name)

    try:
        yield config_path
    finally:
        config_path.unlink(missing_ok=True)
```

### Fixture Design Principles

1. **Isolation**: Each fixture should be independent and not affect others
2. **Cleanup**: Always clean up resources after tests complete
3. **Flexibility**: Allow customization through parameters where appropriate
4. **Performance**: Minimize fixture setup time for fast test execution
5. **Reliability**: Fixtures should work consistently across platforms

### Documentation Standards

1. **Docstrings**: Every public function and fixture needs comprehensive docstrings
2. **Examples**: Include working code examples in docstrings
3. **Type hints**: Use comprehensive type annotations
4. **README updates**: Update README.md when adding major features

### Testing Requirements

1. **Test your fixtures**: Every fixture should have tests
2. **Cross-platform**: Test on multiple platforms (macOS, Linux, Windows)
3. **Python versions**: Ensure compatibility with Python 3.11+
4. **Performance**: Avoid fixtures that significantly slow down test suites

### Code Quality Standards

```bash
# Format code
ruff format src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run tests
pytest tests/ -v

# Check test coverage
pytest tests/ --cov=src/provide/testkit --cov-report=term-missing
```

## Common Patterns

### Context Managers
Many fixtures use context managers for resource cleanup:

```python
@pytest.fixture
def mock_server():
    """Create a mock HTTP server."""
    with HTTPServer() as server:
        yield server
    # Automatic cleanup when context exits
```

### Parameterized Fixtures
Use parameterization for testing multiple scenarios:

```python
@pytest.fixture(params=["json", "yaml", "toml"])
def config_format(request):
    """Test with multiple configuration formats."""
    return request.param
```

### Async Fixtures
Support async testing with async fixtures:

```python
@pytest.fixture
async def async_client():
    """Create an async HTTP client."""
    async with httpx.AsyncClient() as client:
        yield client
```

## Development Workflow

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/add-database-fixtures
   ```

2. **Add your fixture**:
   ```bash
   # Add fixture to appropriate domain
   vim src/provide/testkit/database/fixtures.py

   # Add tests
   vim tests/test_database_fixtures.py

   # Update exports
   vim src/provide/testkit/database/__init__.py
   ```

3. **Test your changes**:
   ```bash
   pytest tests/test_database_fixtures.py -v
   pytest tests/ # Run all tests
   ```

4. **Update documentation**:
   ```bash
   # Update README if needed
   vim README.md

   # Add changelog entry
   vim CHANGELOG.md
   ```

5. **Submit a pull request**:
   ```bash
   git add .
   git commit -m "feat: add database testing fixtures"
   git push origin feature/add-database-fixtures
   ```

### Review Process

1. **Automated checks**: CI will run tests, linting, and type checking
2. **Code review**: Maintainers will review for:
   - Code quality and style
   - Test coverage
   - Documentation completeness
   - Cross-platform compatibility
   - Performance impact

3. **Testing**: Changes will be tested across the ecosystem
4. **Integration**: Once approved, changes will be merged

## Issue Reporting

### Bug Reports
When reporting bugs, include:

- **Environment**: OS, Python version, testkit version
- **Minimal reproduction**: Smallest possible test case that demonstrates the issue
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Any relevant error messages or stack traces

### Feature Requests
When requesting features, include:

- **Use case**: Why is this feature needed?
- **Proposed API**: How should the fixture work?
- **Domain**: Which domain should it belong to?
- **Examples**: How would it be used in tests?

## Release Process

1. **Version bumping**: Follow semantic versioning
2. **Changelog**: Update CHANGELOG.md with all changes
3. **Testing**: Run full test suite across ecosystem
4. **Documentation**: Update API documentation
5. **Release**: Create GitHub release with notes

## Questions?

- **Documentation**: Check the docs directory for detailed guides
- **Examples**: Look at the examples directory for usage patterns
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions and ideas

Thank you for contributing to provide-testkit! Your work helps ensure the entire provide.io ecosystem has excellent testing support. 🧪✨