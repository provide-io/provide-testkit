# Getting Started with Provide TestKit

Welcome to Provide TestKit! This guide will help you get up and running with testing utilities for the provide ecosystem.

## What is Provide TestKit?

Provide TestKit is a comprehensive testing utilities library that provides:

- 🧪 **Pytest Fixtures** - Domain-organized fixtures for file, process, transport, crypto testing
- 🔧 **Testing Utilities** - Mocking helpers, async support, CLI testing tools
- 🏗️ **Foundation Integration** - Seamless testing with provide-foundation applications

## Installation

### Using uv (Recommended)

```bash
uv add provide-testkit --group dev
```

### Optional Dependencies

Install additional features as needed:

```bash
# HTTP client testing
uv add "provide-testkit[transport]" --group dev

# Cryptographic testing
uv add "provide-testkit[crypto]" --group dev

# Process monitoring
uv add "provide-testkit[process]" --group dev

# All features
uv add "provide-testkit[all]" --group dev
```

## Quick Start

Ready to write your first test? Check out the [Quick Start Guide](quick-start.md) for a hands-on introduction in just 5 minutes!

## Documentation Structure

- **[Quick Start](quick-start.md)** - Get started in 5 minutes
- **[API Reference](../reference/index.md)** - Complete API documentation
- **[Examples](../examples/)** - Practical examples and patterns

## Core Features

### Domain-Organized Fixtures

Testkit provides fixtures organized by domain:

- **File Testing** - Temporary directories, file structures, content generation
- **Process & Async** - Event loops, async timeouts, subprocess mocking
- **Transport & Network** - HTTP mocking, free ports, WebSocket testing
- **Crypto** - Certificate fixtures, PEM testing, validation helpers
- **Threading** - Thread pools, synchronization primitives, concurrent execution
- **Time** - Time freezing, clock mocking for deterministic tests

### Foundation Integration

Testkit includes specialized utilities for testing Foundation-based applications:

```python
from provide.testkit import reset_foundation_setup_for_testing

def test_foundation_app():
    """Test that uses Foundation."""
    reset_foundation_setup_for_testing()
    # Your test code here
```

### Automatic Detection

Testkit automatically detects testing contexts and adjusts behavior:

- Detects pytest execution
- Monitors `PYTEST_CURRENT_TEST` environment variable
- Adapts to unittest framework
- Respects `TESTING=true` environment variable

## Prerequisites

- Python 3.11 or higher
- Basic familiarity with pytest
- (Optional) provide-foundation for Foundation-specific testing

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/provide-io/provide-testkit/issues)
- **Documentation**: Browse the `docs/` directory
- **Examples**: See the `examples/` directory for practical patterns

## Next Steps

1. **[Quick Start Guide](quick-start.md)** - Build your first test in 5 minutes
2. **[API Reference](../reference/index.md)** - Explore available fixtures and utilities
3. **[Examples](../examples/)** - See practical testing patterns

---

**Ready to get started?** Head over to the [Quick Start Guide](quick-start.md)!
