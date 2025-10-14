# Testing Guide for provide-testkit

This guide shows how to use provide-testkit effectively for testing Foundation-based applications.

## Base Test Classes

### FoundationTestCase

**Always inherit from FoundationTestCase for Foundation-based tests:**

```python
from provide.testkit import FoundationTestCase

class TestMyFeature(FoundationTestCase):
    def test_something(self) -> None:
        # Foundation is automatically reset before each test
        # Temp files are automatically tracked and cleaned up
        # Mocks are automatically tracked and cleaned up
        pass
```

### What FoundationTestCase Provides

- **Automatic Foundation reset** before each test
- **Temp file tracking** with automatic cleanup
- **Mock tracking** with automatic cleanup
- **Common test utilities** (create_temp_file, create_temp_dir, etc.)

## Mock Utilities

### Time Mocking

```python
from provide.testkit import mock_sleep, mock_time_sleep, mock_asyncio_sleep

# Mock both sync and async sleep with tracking
with mock_sleep() as tracker:
    time.sleep(1.0)
    await asyncio.sleep(2.0)
    assert tracker.call_count == 2
    assert tracker.total_sleep_time == 3.0

# Mock only asyncio.sleep
with mock_asyncio_sleep() as tracker:
    await asyncio.sleep(1.0)
    assert tracker.call_count == 1
```

### Environment Variables

```python
from provide.testkit import temp_env, isolated_env, EnvContext

# Temporary environment changes
with temp_env(DEBUG="true", LOG_LEVEL="INFO"):
    # Environment variables are set
    assert os.environ["DEBUG"] == "true"
# Variables are restored automatically

# Isolated environment (clears all except specified)
with isolated_env(keep_vars=["PATH", "HOME"], TEST_MODE="true"):
    # Only PATH, HOME, and TEST_MODE are in environment
    pass

# Context manager for incremental changes
with EnvContext() as env:
    env.set("DEBUG", "true")
    env.delete("UNWANTED_VAR")
    # Changes are applied and restored automatically
```

### File Management

```python
from provide.testkit import TempFileManager, create_temp_file, create_temp_dir

# Manager approach (recommended for multiple files)
with TempFileManager() as manager:
    config_file = manager.create_json_file({"debug": True})
    temp_dir = manager.create_directory()
    nested_file = manager.create_file_in_dir(temp_dir, "test.txt", "content")
    # All files cleaned up automatically

# Simple approach (for single files)
temp_file = create_temp_file("content", suffix=".txt")
temp_dir = create_temp_dir()
```

## CLI Testing

```python
from provide.testkit import CliTestRunner

def test_cli_command():
    runner = CliTestRunner()
    result = runner.invoke(my_cli, ["--help"])

    runner.assert_success(result)
    runner.assert_output_contains(result, "Usage:")

    # Full output with ANSI stripping
    output = runner.get_full_output(result)
    assert "expected text" in output
```

## Async Testing

```python
from provide.testkit import clean_event_loop, async_timeout, async_context_manager

@pytest.mark.asyncio
async def test_async_function(clean_event_loop):
    # Event loop is automatically cleaned after test
    async with async_context_manager() as mock_cm:
        result = await my_async_function()
        assert result is not None
```

## Dependency Injection Testing (New in Phase 2)

Foundation now supports dependency injection for cleaner, more isolated tests. Instead of relying on global state and reset functions, you can create isolated Container and Hub instances per test.

### Using Isolated Container

```python
from provide.testkit import isolated_container

def test_with_isolated_container(isolated_container):
    """Each test gets a fresh Container with no shared state."""
    # Register test-specific dependencies
    isolated_container.register("my_service", MyTestService())

    # Use the container
    service = isolated_container.resolve("my_service")
    assert service is not None

    # No need to call reset_foundation_setup_for_testing()
```

### Using Isolated Hub

```python
from provide.testkit import isolated_hub
from provide.foundation.transport import UniversalClient

@pytest.mark.asyncio
async def test_with_isolated_hub(isolated_hub):
    """Hub with isolated Container for complete test isolation."""
    # Create components with explicit DI
    client = UniversalClient(hub=isolated_hub)

    # Test proceeds without affecting global Hub state
    response = await client.get("https://api.example.com")
    assert response.status == 200

    # No global state pollution - no reset needed
```

### When to Use Isolated Fixtures vs FoundationTestCase

**Use isolated fixtures (`isolated_container`, `isolated_hub`) when:**
- Writing unit tests that need complete isolation
- Testing components that accept Hub/Container via constructor
- You want to avoid global state entirely
- No need for reset functions between tests

**Use FoundationTestCase when:**
- Writing integration tests that use global Hub (via `get_hub()`)
- Testing legacy code that relies on global state
- You need automatic cleanup of temp files and mocks
- Testing components that don't support DI yet

### Comparing Testing Patterns

**Traditional Pattern (with reset):**
```python
class TestMyFeature(FoundationTestCase):
    def test_something(self) -> None:
        # Foundation reset happens automatically
        # Uses global Hub via get_hub()
        result = my_function_using_global_hub()
        assert result is not None
```

**Modern DI Pattern (no reset needed):**
```python
def test_something(isolated_hub):
    # Fresh Hub per test, no reset needed
    # Explicit DI via constructor
    component = MyComponent(hub=isolated_hub)
    result = component.do_something()
    assert result is not None
```

**Best of Both Worlds:**
```python
class TestMyFeature(FoundationTestCase):
    def test_with_di(self, isolated_hub) -> None:
        # Get FoundationTestCase cleanup + isolated Hub
        # Temp files tracked, Hub isolated
        temp_file = self.create_temp_file("data")
        component = MyComponent(hub=isolated_hub, data_file=temp_file)
        assert component.process() is not None
```

## Best Practices

1. **Always use FoundationTestCase** as base class for Foundation tests
2. **Use testkit mocks** instead of unittest.mock directly
3. **Use temp file utilities** instead of manual temp file creation
4. **Use environment utilities** instead of manual os.environ manipulation
5. **Use async fixtures** for async test scenarios
6. **Clean up properly** (FoundationTestCase handles this automatically)
7. **Prefer isolated fixtures** for new tests using DI-enabled components
8. **Use explicit DI** (pass Hub/Container to constructors) instead of global `get_hub()` calls

## Migration from Plain Test Classes

**Before:**
```python
class TestMyFeature:
    def setup_method(self) -> None:
        reset_foundation_setup_for_testing()
        self.temp_files = []

    def teardown_method(self) -> None:
        for file in self.temp_files:
            if file.exists():
                file.unlink()
```

**After:**
```python
class TestMyFeature(FoundationTestCase):
    def test_something(self) -> None:
        # Foundation reset and cleanup handled automatically
        temp_file = self.create_temp_file("content")
        # Temp file tracked and cleaned up automatically
```

## Common Patterns

### Testing Configuration

```python
def test_config_loading(self):
    config_data = {"log_level": "DEBUG", "service_name": "test"}
    config_file = self.create_temp_file(json.dumps(config_data), suffix=".json")

    with temp_env(CONFIG_FILE=str(config_file)):
        config = load_config()
        assert config.log_level == "DEBUG"
```

### Testing CLI with Files

```python
def test_cli_with_config(self):
    config_file = self.create_temp_file('{"debug": true}', suffix=".json")

    runner = CliTestRunner()
    result = runner.invoke(my_cli, ["--config", str(config_file)])
    runner.assert_success(result)
```

### Testing Async Operations

```python
@pytest.mark.asyncio
async def test_async_operation(self, clean_event_loop):
    with mock_asyncio_sleep() as sleep_tracker:
        result = await my_async_function_with_sleep()
        assert result is not None
        assert sleep_tracker.call_count > 0
```