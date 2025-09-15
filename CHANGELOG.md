# Changelog

All notable changes to the provide-testkit project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of provide-testkit
- Domain-organized fixture system
- File testing fixtures (temp_directory, test_files_structure, binary_file, etc.)
- Process testing fixtures (clean_event_loop, async_timeout, mock_async_process, etc.)
- Transport testing fixtures (free_port, mock_server, httpx_mock_responses, etc.)
- Threading testing utilities (thread pools, locks, concurrent data structures)
- Crypto testing fixtures (client_cert, server_cert, ca_cert, etc.)
- Archive testing utilities (multi-format archive fixtures)
- Time manipulation utilities (time freezing and clock mocking)
- CLI testing support (MockContext, isolated_cli_runner, CliTestCase)
- Comprehensive lazy loading system with automatic testing context detection
- Integration with pytest, hypothesis, and asyncio testing patterns

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- N/A (initial release)

## Release Notes

### v0.0.0 (Initial Release)

This is the first release of provide-testkit, providing a comprehensive testing framework for the provide.io ecosystem. The testkit includes:

**Core Features:**
- Domain-organized fixtures for different testing needs
- Lazy loading system to minimize production overhead
- Automatic testing context detection
- Integration with popular testing frameworks

**Fixture Categories:**
- **File Testing**: Directory structures, file content, permissions, symlinks
- **Process Testing**: Async operations, subprocess mocking, event loops
- **Network Testing**: Free ports, mock servers, HTTP client testing
- **Threading**: Thread pools, synchronization primitives, concurrent data
- **Cryptography**: Certificate generation, PEM utilities, validation
- **Archive**: Multi-format archive creation and validation
- **Time**: Clock mocking, time travel, deterministic testing

**Integration Support:**
- pytest compatibility with automatic fixture discovery
- asyncio testing support via pytest-asyncio
- Property-based testing with Hypothesis
- CLI testing utilities for command-line applications

**Development Philosophy:**
- Production-safe with minimal runtime overhead
- Type-safe with comprehensive annotations
- Well-documented with examples for all fixtures
- Extensible design for adding custom fixtures

This release establishes the foundation for consistent, comprehensive testing across all packages in the provide.io ecosystem.