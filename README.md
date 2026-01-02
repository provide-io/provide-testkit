# 🧪✅ Provide TestKit

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/) [![uv](https://img.shields.io/badge/uv-package_manager-FF6B35.svg)](https://github.com/astral-sh/uv) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![CI](https://github.com/provide-io/provide-testkit/actions/workflows/ci.yml/badge.svg)](https://github.com/provide-io/provide-testkit/actions)

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

## Quick Start
1. Install: `uv add provide-testkit`
2. Read the [Quick Start guide](https://github.com/provide-io/provide-testkit/blob/main/docs/getting-started/quick-start.md).
3. Explore examples in [examples/README.md](https://github.com/provide-io/provide-testkit/blob/main/examples/README.md).

## Documentation
- [Documentation index](https://github.com/provide-io/provide-testkit/blob/main/docs/index.md)
- [Examples](https://github.com/provide-io/provide-testkit/blob/main/examples/README.md)

## Development

### Quick Start

```bash
# Set up environment
uv sync

# Run common tasks
uv run pytest              # Run tests
uv run pytest -n auto      # Run tests in parallel
uv run pytest --cov        # Run tests with coverage
uv run ruff check .        # Check code
uv run ruff format .       # Format code
uv run mypy src/           # Type checking
```

See [CLAUDE.md](https://github.com/provide-io/provide-testkit/blob/main/CLAUDE.md) for detailed development instructions and architecture information.

## Contributing

See [CONTRIBUTING.md](https://github.com/provide-io/provide-testkit/blob/main/CONTRIBUTING.md) for contribution guidelines.

See [CLAUDE.md](https://github.com/provide-io/provide-testkit/blob/main/CLAUDE.md) for detailed development instructions and architecture information.

## Contributing
See [CONTRIBUTING.md](https://github.com/provide-io/provide-testkit/blob/main/CONTRIBUTING.md) for contribution guidelines.

## License
See [LICENSE](https://github.com/provide-io/provide-testkit/blob/main/LICENSE) for license details.

Copyright (c) provide.io LLC.
