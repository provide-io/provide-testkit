# Installation

## Requirements

Before installing Provide TestKit, ensure you have:

- **Python 3.11 or later**
- **pytest 7.0 or later**

## Installation Methods

### Using uv (Recommended)

```bash
uv add provide-testkit
```

**Why uv?** Faster dependency resolution and better environment management.

### Using pip

```bash
pip install provide-testkit
```

### From Source

For development or the latest features:

```bash
git clone https://github.com/provide-io/provide-testkit.git
cd provide-testkit
pip install -e .
```

## Optional Dependencies

Provide TestKit offers several optional feature sets:

### Quality Tools

Install all code quality analysis tools:

```bash
pip install provide-testkit[quality]
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
pip install provide-testkit[coverage,security]

# All complexity tools
pip install provide-testkit[complexity]
```

### All Features

Install everything:

```bash
pip install provide-testkit[all]
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

## Next Steps

- **[Quick Start](quick-start.md)** - Your first test with Provide TestKit
- **[API Reference](../api/index.md)** - Complete API documentation
- **[Quality Guide](../quality_guide.md)** - Code quality testing tools
