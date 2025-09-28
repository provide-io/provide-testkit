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

## Best Practices

1. **Always use FoundationTestCase** as base class for Foundation tests
2. **Use testkit mocks** instead of unittest.mock directly
3. **Use temp file utilities** instead of manual temp file creation
4. **Use environment utilities** instead of manual os.environ manipulation
5. **Use async fixtures** for async test scenarios
6. **Clean up properly** (FoundationTestCase handles this automatically)

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