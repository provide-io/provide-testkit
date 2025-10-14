"""
Hub Testing Fixtures for Foundation.

Provides pytest fixtures for testing hub and component functionality,
including container directories and component registration scenarios.

Dependency Injection Testing
-----------------------------

These fixtures support Foundation's dependency injection architecture,
enabling isolated testing without global state resets.

Key fixtures:
- `isolated_container`: Creates a fresh Container for each test
- `isolated_hub`: Creates a Hub with an isolated Container
- `default_container_directory`: Provides temp directory for containers

Example usage:
    >>> def test_with_isolated_hub(isolated_hub):
    ...     # Each test gets its own Hub with clean state
    ...     # No need to call reset_foundation_setup_for_testing()
    ...     client = UniversalClient(hub=isolated_hub)
    ...     # Test proceeds with isolated dependencies
"""

from __future__ import annotations

from typing import Any

import pytest

from provide.foundation.file import temp_dir as foundation_temp_dir


@pytest.fixture(scope="session")
def default_container_directory() -> Any:
    """
    Provides a default directory for container operations in tests.

    This fixture is used by tests that need a temporary directory
    for container-related operations.
    """
    with foundation_temp_dir() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def isolated_container() -> Any:
    """
    Create an isolated Container for dependency injection testing.

    This fixture provides a fresh Container instance for each test,
    eliminating the need for global state resets between tests.

    Returns:
        Container: A new Container instance with no pre-registered dependencies.

    Example:
        >>> def test_my_component(isolated_container):
        ...     # Register test-specific dependencies
        ...     isolated_container.register("my_service", MyService())
        ...     # Test with isolated state
        ...     service = isolated_container.resolve("my_service")
        ...     assert service is not None

    Note:
        Tests using this fixture do not need to call
        reset_foundation_setup_for_testing() as each test
        gets a fresh container automatically.
    """
    from provide.foundation.hub import Container

    return Container()


@pytest.fixture
def isolated_hub() -> Any:
    """
    Create an isolated Hub with fresh registries for testing.

    This fixture provides a Hub instance with isolated registries,
    enabling dependency injection testing without global state side effects.

    Returns:
        Hub: A Hub instance with isolated registries.

    Example:
        >>> def test_with_di(isolated_hub):
        ...     # Hub has fresh, isolated state
        ...     client = UniversalClient(hub=isolated_hub)
        ...     # Test proceeds without affecting global Hub
        ...     response = await client.get("https://api.example.com")
        ...     assert response.status == 200

    Note:
        This fixture is ideal for unit tests that need Hub functionality
        but want complete isolation from other tests. No reset functions
        are needed when using this fixture.
    """
    from provide.foundation.context import CLIContext
    from provide.foundation.hub import Hub
    from provide.foundation.hub.registry import Registry

    # Create isolated registries
    component_registry = Registry()
    command_registry = Registry()

    # Create Hub with isolated registries (not shared)
    return Hub(
        context=CLIContext(),
        component_registry=component_registry,
        command_registry=command_registry,
        use_shared_registries=False,
    )
