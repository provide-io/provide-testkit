# Installation

## Prerequisites

--8<-- ".provide/foundry/docs/_partials/python-requirements.md"

**Additional Requirements**:
- **pytest 7.0 or later** - Required for running tests

## Installing UV

--8<-- ".provide/foundry/docs/_partials/uv-installation.md"

## Python Version Setup

--8<-- ".provide/foundry/docs/_partials/python-version-setup.md"

## Virtual Environment

--8<-- ".provide/foundry/docs/_partials/virtual-env-setup.md"

## Installing Provide TestKit

### Using UV (Recommended)

```bash
uv add provide-testkit
```

### From Source

For development or the latest features:

```bash
# Clone the repository
git clone https://github.com/provide-io/provide-testkit.git
cd provide-testkit

# Set up environment and install
uv sync

# Verify installation
python -c "import provide.testkit; print('✅ TestKit installed')"
```

## Optional Dependencies

Provide TestKit offers several optional feature sets:

### Quality Tools

Install all code quality analysis tools:

```bash
uv add provide-testkit[quality]
```

Includes:
- Code coverage (coverage.py)
- Security scanning (bandit)
- Complexity analysis (radon)
- Documentation coverage (interrogate)
- Performance profiling (memray)

### Specific Tool Sets

Install only the tools you need:

```bash
# Coverage and security only
uv add provide-testkit[coverage,security]

# All complexity tools
uv add provide-testkit[complexity]
```

### All Features

Install everything:

```bash
uv add provide-testkit[all]
```

## Verify Installation

Confirm Provide TestKit is installed correctly:

```python
import provide.testkit
print(provide.testkit.__version__)
```

In your tests:

```python
from provide.testkit import fixtures

def test_installation(fixtures.temp_directory):
    """Test that fixtures work."""
    assert fixtures.temp_directory.exists()
```

## Troubleshooting

--8<-- ".provide/foundry/docs/_partials/troubleshooting-common.md"

### TestKit-Specific Issues

**Problem**: Fixtures not discovered by pytest

**Solution**: Ensure pytest is configured to find provide.testkit:
```bash
# Check if testkit is installed
python -c "import provide.testkit; print('✅ Found')"

# Run pytest with verbose fixture discovery
pytest --fixtures | grep provide
```

**Problem**: setproctitle warnings on macOS

**Solution**: This is normal - testkit blocks setproctitle to prevent macOS terminal freezing with pytest-xdist. The blocker is working correctly.

## Next Steps

- **[Quick Start](../getting-started/quick-start/)** - Your first test with Provide TestKit
- **[API Reference](../api/)** - Complete API documentation
- **[Quality Guide](../quality_guide/)** - Code quality testing tools
