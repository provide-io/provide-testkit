"""Pytest fixtures for chaos testing.

Provides reusable fixtures that enable chaos injection and control
in property-based tests.
"""

from __future__ import annotations

from collections.abc import Callable, Generator
import time
from typing import Any

from hypothesis import Phase, Verbosity, settings
import pytest


class ChaosTimeSource:
    """Controllable time source for chaos testing.

    Allows tests to manipulate time for testing time-dependent behavior.
    """

    def __init__(self, start_time: float | None = None) -> None:
        """Initialize chaos time source.

        Args:
            start_time: Initial time value (defaults to current time)
        """
        self._current_time = start_time if start_time is not None else time.time()
        self._frozen = False

    def __call__(self) -> float:
        """Get current time.

        Returns:
            Current time value
        """
        if not self._frozen:
            self._current_time = time.time()
        return self._current_time

    def advance(self, seconds: float) -> None:
        """Advance time by specified seconds.

        Args:
            seconds: Time to advance (can be negative for backwards jumps)
        """
        self._current_time += seconds

    def set(self, timestamp: float) -> None:
        """Set time to specific value.

        Args:
            timestamp: Absolute time value to set
        """
        self._current_time = timestamp

    def freeze(self) -> None:
        """Freeze time at current value."""
        self._frozen = True

    def unfreeze(self) -> None:
        """Resume normal time progression."""
        self._frozen = False

    def reset(self) -> None:
        """Reset to current real time."""
        self._current_time = time.time()
        self._frozen = False


class ChaosFailureInjector:
    """Injectable failure patterns for chaos testing.

    Allows tests to inject failures at specific points.
    """

    def __init__(self) -> None:
        """Initialize failure injector."""
        self._failure_patterns: list[tuple[int, type[Exception]]] = []
        self._call_count = 0

    def set_patterns(self, patterns: list[tuple[int, type[Exception]]]) -> None:
        """Set failure patterns.

        Args:
            patterns: List of (call_number, exception_type) tuples
        """
        self._failure_patterns = sorted(patterns, key=lambda x: x[0])
        self._call_count = 0

    def check(self) -> None:
        """Check if failure should be injected at this call.

        Raises:
            Exception: If a failure is scheduled for this call number
        """
        for call_num, exc_type in self._failure_patterns:
            if call_num == self._call_count:
                self._call_count += 1
                raise exc_type(f"Chaos-injected failure at call {call_num}")

        self._call_count += 1

    def reset(self) -> None:
        """Reset call counter."""
        self._call_count = 0


@pytest.fixture
def chaos_time_source() -> Generator[ChaosTimeSource, None, None]:
    """Provide a controllable time source for chaos testing.

    Yields:
        ChaosTimeSource instance for time manipulation

    Example:
        ```python
        def test_with_time_control(chaos_time_source):
            chaos_time_source.freeze()
            start = chaos_time_source()
            chaos_time_source.advance(60)
            assert chaos_time_source() == start + 60
        ```
    """
    source = ChaosTimeSource()
    yield source
    source.reset()


@pytest.fixture
def chaos_failure_injector() -> Generator[ChaosFailureInjector, None, None]:
    """Provide a failure injector for chaos testing.

    Yields:
        ChaosFailureInjector instance

    Example:
        ```python
        def test_with_failures(chaos_failure_injector):
            chaos_failure_injector.set_patterns([(2, ValueError), (5, IOError)])
            for i in range(10):
                try:
                    chaos_failure_injector.check()
                    # Operation succeeds
                except (ValueError, IOError):
                    # Operation fails as injected
                    pass
        ```
    """
    injector = ChaosFailureInjector()
    yield injector
    injector.reset()


@pytest.fixture
def hypothesis_chaos_settings() -> Generator[None, None, None]:
    """Apply Hypothesis settings optimized for chaos testing.

    Configures Hypothesis for thorough chaos exploration.

    Example:
        ```python
        @pytest.mark.usefixtures("hypothesis_chaos_settings")
        class TestChaos:
            @given(data=st.data())
            def test_something(self, data):
                # Uses chaos settings
                pass
        ```
    """
    # Apply chaos profile
    settings.load_profile("chaos")

    yield

    # Restore to default profile
    settings.load_profile("default")


@pytest.fixture
def chaos_config() -> dict[str, Any]:
    """Provide chaos testing configuration.

    Returns:
        Dictionary with chaos configuration options

    Example:
        ```python
        def test_with_config(chaos_config):
            max_retries = chaos_config['max_retries']
            timeout = chaos_config['timeout']
        ```
    """
    return {
        "max_retries": 10,
        "timeout": 30.0,
        "enable_time_chaos": True,
        "enable_failure_injection": True,
        "enable_concurrency_chaos": True,
        "enable_io_chaos": True,
    }


def chaos_time_source_factory(initial_time: float | None = None) -> Callable[[], float]:
    """Create a time source function for components that need callable time sources.

    Args:
        initial_time: Initial time value

    Returns:
        Callable that returns time

    Example:
        ```python
        def test_component():
            time_source = chaos_time_source_factory()
            component = MyComponent(time_source=time_source)
        ```
    """
    source = ChaosTimeSource(start_time=initial_time)
    return source


# Register Hypothesis profiles
settings.register_profile(
    "chaos",
    max_examples=1000,
    verbosity=Verbosity.verbose,
    deadline=None,  # Disable for async tests
    report_multiple_bugs=True,
    phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink],
    print_blob=True,  # Enable statistics printing
)

settings.register_profile(
    "chaos_ci",
    max_examples=100,
    verbosity=Verbosity.normal,
    deadline=10000,
    report_multiple_bugs=False,
    phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink],
    print_blob=True,  # Enable statistics printing
)

settings.register_profile(
    "chaos_smoke",
    max_examples=20,
    verbosity=Verbosity.quiet,
    deadline=5000,
    report_multiple_bugs=False,
    phases=[Phase.explicit, Phase.generate],  # Skip shrinking for speed
    print_blob=True,  # Enable statistics printing
)


__all__ = [
    "ChaosFailureInjector",
    "ChaosTimeSource",
    "chaos_config",
    "chaos_failure_injector",
    "chaos_time_source",
    "chaos_time_source_factory",
    "hypothesis_chaos_settings",
]
