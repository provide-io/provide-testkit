# Chaos Testing with Hypothesis

Chaos testing utilities for property-based testing with Hypothesis. This module provides reusable strategies, fixtures, and patterns for systematically exploring edge cases, race conditions, and failure scenarios.

## Quick Start

```python
from hypothesis import given
from provide.testkit.chaos import (
    chaos_timings,
    thread_counts,
    pid_recycling_scenarios,
)

@given(
    num_threads=thread_counts(),
    timing=chaos_timings(),
)
def test_concurrent_access(num_threads, timing):
    # Your chaos test here
    pass
```

## Available Strategies

### Core Strategies (`strategies.py`)

- **`chaos_timings()`** - Generate unpredictable timing patterns
- **`failure_patterns()`** - Create failure injection patterns
- **`malformed_inputs()`** - Edge-case inputs (huge strings, binary, NaN, etc.)
- **`unicode_chaos()`** - Problematic Unicode (emoji, RTL, zero-width chars)
- **`resource_limits()`** - Memory/CPU/timeout constraints
- **`edge_values()`** - Boundary values for int/float/str

### Time Strategies (`time_strategies.py`)

- **`time_advances()`** - Time progression patterns (with backwards jumps)
- **`clock_skew()`** - Clock drift and NTP issues
- **`timeout_patterns()`** - Realistic timeout scenarios
- **`rate_burst_patterns()`** - Traffic burst simulations
- **`jitter_patterns()`** - Network-like timing variations
- **`deadline_scenarios()`** - Deadline-based scenarios
- **`retry_backoff_patterns()`** - Retry/backoff configurations

### Concurrency Strategies (`concurrency_strategies.py`)

- **`thread_counts()`** - Thread count scenarios
- **`race_condition_triggers()`** - Timing patterns for races
- **`deadlock_scenarios()`** - Circular lock dependencies
- **`async_event_patterns()`** - Coroutine scheduling chaos
- **`lock_contention_patterns()`** - Lock contention scenarios
- **`task_cancellation_patterns()`** - Task cancellation scenarios
- **`process_pool_patterns()`** - Process pool configurations
- **`pid_recycling_scenarios()`** - PID recycling attack scenarios

### I/O Strategies (`io_strategies.py`)

- **`file_sizes()`** - Realistic file size distributions
- **`permission_patterns()`** - File permission scenarios
- **`disk_full_scenarios()`** - Disk space exhaustion
- **`network_error_patterns()`** - Network failure patterns
- **`buffer_overflow_patterns()`** - Buffer overflow scenarios
- **`file_corruption_patterns()`** - File corruption scenarios
- **`lock_file_scenarios()`** - File lock conflicts
- **`path_traversal_patterns()`** - Path traversal attempts

## Pytest Fixtures (`fixtures.py`)

### ChaosTimeSource

Controllable time source for testing:

```python
def test_with_time_control(chaos_time_source):
    chaos_time_source.freeze()
    start = chaos_time_source()
    chaos_time_source.advance(60)
    assert chaos_time_source() == start + 60
```

### ChaosFailureInjector

Injectable failure patterns:

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

## Hypothesis Profiles

Three pre-configured profiles:

- **`chaos`** - 1000 examples, verbose, no deadline
- **`chaos_ci`** - 100 examples, normal verbosity, 10s deadline
- **`chaos_smoke`** - 20 examples, quiet, 5s deadline

Activate via:

```python
from hypothesis import settings
settings.load_profile("chaos")
```

Or in `conftest.py`:

```python
@pytest.fixture(scope="session", autouse=True)
def configure_hypothesis():
    settings.load_profile("chaos")
```

## Example: File Lock Chaos Test

```python
from hypothesis import given
from provide.testkit.chaos import (
    thread_counts,
    chaos_timings,
    pid_recycling_scenarios,
)
from provide.foundation.file.lock import FileLock

@given(
    num_threads=thread_counts(min_threads=2, max_threads=20),
    lock_duration=chaos_timings(min_value=0.001, max_value=0.5),
)
def test_concurrent_file_lock(tmp_path, num_threads, lock_duration):
    lock_file = tmp_path / "test.lock"
    # Test concurrent access patterns
    pass

@given(scenario=pid_recycling_scenarios())
def test_pid_recycling_protection(tmp_path, scenario):
    # Test PID recycling detection
    pass
```

## Best Practices

1. **Start Small** - Begin with `chaos_smoke` profile
2. **Isolate Tests** - Mark with `@pytest.mark.chaos`
3. **Document Findings** - Record discovered edge cases
4. **CI Integration** - Use `chaos_ci` profile in CI
5. **Hypothesis Database** - Commit `.hypothesis/` for regression

## Running Chaos Tests

```bash
# All chaos tests
pytest -m chaos

# Specific profile
pytest -m chaos --hypothesis-profile=chaos_ci

# Verbose output
pytest -m chaos --hypothesis-show-statistics
```
