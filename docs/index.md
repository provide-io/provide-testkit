# Provide TestKit Documentation

Welcome to the Provide TestKit documentation - a comprehensive testing utilities and fixtures library for the Provide Foundry ecosystem.

!!! warning "Alpha Software - Active Development"
    provide-testkit is in active alpha development. APIs may change, and some features are experimental.

    - **Current version:** v0.0.1026
    - **Status:** Alpha (Development Status: 3)
    - **Production use:** Not recommended

    See [Quality Guide](quality_guide/) for stable testing patterns.

## Features

Provide TestKit offers:

- **Unified Testing Framework**: Consistent testing patterns across all Provide projects
- **Rich Fixture Library**: Pre-built fixtures for common testing scenarios
- **Process Management**: Tools for testing subprocess and service interactions
- **File System Testing**: Utilities for temporary files and directory management
- **Transport Testing**: Mocking and testing for network communications
- **Quality Assurance**: Code coverage, profiling, and security testing tools

---

## Part of the provide.io Ecosystem

This project is part of a larger ecosystem of tools for Python and Terraform development.

**[View Ecosystem Overview →](https://docs.provide.io/provide-foundation/ecosystem/)**

Understand how provide-foundation, pyvider, flavorpack, and other projects work together.

---

## Quick Start

```python
from provide.testkit import fixtures
from provide.testkit.process import ProcessTestCase

# Use pre-built fixtures
def test_with_temp_directory(fixtures.temp_directory):
    # Your test code here
    pass

# Test process interactions
class TestMyService(ProcessTestCase):
    def test_service_startup(self):
        # Test service processes
        pass
```

## API Reference

For complete API documentation, see the [API Reference](api/).

## Testing Modules

- **Fixtures**: Reusable test fixtures and utilities
- **Process**: Process and subprocess testing tools
- **Transport**: Network and communication testing
- **File**: File system operation testing
- **Quality**: Code quality and security testing tools