#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Example: Mocking and Test Double Patterns

This example demonstrates common mocking patterns and test doubles
using provide-testkit's mocking utilities and fixtures.

Key fixtures used:
- temp_directory: For file-based mocking scenarios
- mock_server: HTTP server mocking (if available)
- Various mock fixtures from common module

Learning objectives:
- Understand different types of test doubles
- Learn when to use mocks vs real objects
- Practice mocking external dependencies
- See fixture composition for complex scenarios"""

import json
from pathlib import Path

import pytest

from provide.testkit.mocking import Mock, patch


# Example classes to demonstrate mocking patterns
class DatabaseConnection:
    """Example database connection class."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.connected = False

    def connect(self) -> str:
        """Simulate database connection."""
        # In real code, this would connect to a database
        self.connected = True
        return "Connected successfully"

    def execute(self, query: str) -> str:
        """Simulate query execution."""
        if not self.connected:
            raise RuntimeError("Not connected to database")
        return f"Executed: {query}"

    def disconnect(self) -> None:
        """Simulate disconnection."""
        self.connected = False


class UserService:
    """Example service that depends on external resources."""

    def __init__(self, db_connection: DatabaseConnection, config_file: str | Path) -> None:
        self.db = db_connection
        self.config_file = Path(config_file)

    def get_user(self, user_id: int) -> str:
        """Get user from database."""
        self.db.connect()
        result = self.db.execute(f"SELECT * FROM users WHERE id = {user_id}")
        self.db.disconnect()
        return result

    def load_config(self) -> dict[str, object]:
        """Load configuration from file."""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")
        return json.loads(self.config_file.read_text())


# Test Patterns


def test_mock_object_pattern() -> None:
    """Pattern 1: Using Mock objects to replace dependencies.

    This demonstrates the most common mocking pattern - replacing external
    dependencies with controllable mock objects that can verify interactions.

    When to use: When you need to verify that your code calls external
    dependencies correctly and in the right order.
    """
    # === SETUP: Create a mock database connection ===
    # Mock(spec=DatabaseConnection) ensures the mock has the same interface
    # as the real DatabaseConnection class, catching attribute errors early
    mock_db = Mock(spec=DatabaseConnection)

    # Configure what the mock should return when methods are called
    # This simulates successful database operations without a real database
    mock_db.connect.return_value = "Connected successfully"
    mock_db.execute.return_value = "User data: John Doe"
    # Note: disconnect() doesn't need a return value since it returns None

    # Create a temporary config file for the service
    # Using tempfile ensures we don't interfere with the real filesystem
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"debug": True}, f)
        config_path = f.name

    try:
        # === ACTION: Use the service with our mocked dependency ===
        # The UserService will use our mock instead of a real database
        service = UserService(mock_db, config_path)
        result = service.get_user(123)  # This should trigger database calls

        # === VERIFICATION: Check that interactions happened correctly ===
        # This is the key benefit of mocks - we can verify behavior

        # Verify connect() was called exactly once
        mock_db.connect.assert_called_once()

        # Verify execute() was called with the exact SQL we expect
        mock_db.execute.assert_called_once_with("SELECT * FROM users WHERE id = 123")

        # Verify disconnect() was called (good resource management)
        mock_db.disconnect.assert_called_once()

        # Verify the service returned what our mock provided
        assert result == "User data: John Doe"

    finally:
        # Clean up the temporary file we created
        Path(config_path).unlink()


def test_stub_pattern(temp_directory: Path) -> None:
    """Pattern 2: Using stubs for simple return values.

    Stubs are simpler than mocks - they just return fixed values without
    verification. Use when you only care about the return value, not the
    interaction details.

    When to use: When you need predictable responses but don't need to
    verify how your code interacts with the dependency.
    """

    # === SETUP: Create a stub that always returns the same values ===
    # Unlike mocks, stubs are often simple classes with hardcoded responses
    class DatabaseStub:
        """A simple stub that always returns the same values.

        This is faster to write than configuring mocks when you only
        need consistent return values.
        """

        def connect(self) -> str:
            # Always succeeds - no complex connection logic needed
            return "Connected successfully"

        def execute(self, query: str) -> str:
            # Always returns the same result regardless of query
            # This is useful when testing business logic that processes results
            return "Stubbed result"

        def disconnect(self) -> None:
            # No-op - stubs often have empty implementations
            pass

    # === SETUP: Create real config file using temp_directory fixture ===
    # Notice how we use temp_directory instead of manual tempfile management
    # This shows how provide-testkit fixtures simplify test setup
    config_file = temp_directory / "config.json"
    config_file.write_text('{"debug": true, "timeout": 30}')

    # === ACTION: Use the service with our stub ===
    # The service gets predictable responses from our stub
    service = UserService(DatabaseStub(), config_file)
    result = service.get_user(456)  # User ID doesn't matter for stubs
    config = service.load_config()  # This uses real file I/O

    # === VERIFICATION: Check the outcomes, not the interactions ===
    # With stubs, we verify results rather than method calls

    # The stub always returns this value, regardless of user ID
    assert result == "Stubbed result"

    # The config loading uses real file operations (not stubbed)
    assert config["debug"] is True
    assert config["timeout"] == 30


def test_spy_pattern() -> None:
    """Pattern 3: Using spies to observe behavior."""

    # Arrange: Create a spy that records calls
    class DatabaseSpy:
        def __init__(self) -> None:
            self.calls = []

        def connect(self) -> str:
            self.calls.append("connect")
            return "Connected successfully"

        def execute(self, query: str) -> str:
            self.calls.append(f"execute:{query}")
            return "Spy result"

        def disconnect(self) -> None:
            self.calls.append("disconnect")

    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"app": "test"}, f)
        config_path = f.name

    try:
        # Act: Use the service with spy
        spy_db = DatabaseSpy()
        service = UserService(spy_db, config_path)
        service.get_user(789)

        # Assert: Verify the sequence of calls
        expected_calls = ["connect", "execute:SELECT * FROM users WHERE id = 789", "disconnect"]
        assert spy_db.calls == expected_calls

    finally:
        Path(config_path).unlink()


def test_fake_pattern(temp_directory: Path) -> None:
    """Pattern 4: Using fakes with working implementations."""

    # Arrange: Create a fake with simple in-memory implementation
    class InMemoryDatabase:
        def __init__(self) -> None:
            self.data = {1: "Alice", 2: "Bob", 3: "Charlie"}
            self.connected = False

        def connect(self) -> str:
            self.connected = True
            return "Connected successfully"

        def execute(self, query: str) -> str:
            if not self.connected:
                raise RuntimeError("Not connected")

            # Simple parsing for demo
            if "WHERE id = " in query:
                user_id = int(query.split("WHERE id = ")[1])
                return f"User data: {self.data.get(user_id, 'Not found')}"
            return "Unknown query"

        def disconnect(self) -> None:
            self.connected = False

    # Create config file
    config_file = temp_directory / "config.json"
    config_file.write_text('{"env": "test", "features": ["auth", "logging"]}')

    # Act: Use service with fake database
    fake_db = InMemoryDatabase()
    service = UserService(fake_db, config_file)

    result1 = service.get_user(1)
    result2 = service.get_user(2)
    result3 = service.get_user(999)  # Non-existent user

    # Assert: Verify fake behavior
    assert result1 == "User data: Alice"
    assert result2 == "User data: Bob"
    assert result3 == "User data: Not found"


@patch("__main__.DatabaseConnection")
def test_patch_decorator_pattern(mock_db_class: Mock, temp_directory: Path) -> None:
    """Pattern 5: Using @patch decorator for mocking."""
    # Arrange: Configure the patched class
    mock_db_instance = Mock()
    mock_db_instance.connect.return_value = "Patched connection"
    mock_db_instance.execute.return_value = "Patched result"
    mock_db_class.return_value = mock_db_instance

    config_file = temp_directory / "config.json"
    config_file.write_text('{"database": {"host": "localhost", "port": 5432}}')

    # Act: Create service (DatabaseConnection will be mocked)
    service = UserService(DatabaseConnection("localhost", 5432), config_file)
    result = service.get_user(100)

    # Assert: Verify patch worked
    mock_db_class.assert_called_once_with("localhost", 5432)
    assert result == "Patched result"


def test_context_manager_mocking(temp_directory: Path) -> None:
    """Pattern 6: Mocking with context managers."""
    # Arrange: Create config file
    config_file = temp_directory / "config.json"
    config_file.write_text('{"mock_test": true}')

    # Act & Assert: Use patch as context manager
    with patch.object(DatabaseConnection, "execute") as mock_execute:
        mock_execute.return_value = "Context manager result"

        db = DatabaseConnection("test", 1234)
        service = UserService(db, config_file)
        result = service.get_user(200)

        assert result == "Context manager result"
        mock_execute.assert_called_once_with("SELECT * FROM users WHERE id = 200")


def test_partial_mocking(temp_directory: Path) -> None:
    """Pattern 7: Mocking only part of an object."""
    # Arrange: Use real object but mock specific methods
    real_db = DatabaseConnection("real_host", 5432)
    config_file = temp_directory / "config.json"
    config_file.write_text('{"partial_mock": true}')

    # Act: Mock only the execute method
    with patch.object(real_db, "execute") as mock_execute:
        mock_execute.return_value = "Partially mocked result"

        service = UserService(real_db, config_file)
        result = service.get_user(300)

        # Assert: Real methods work, mocked method returns mock value
        assert real_db.host == "real_host"  # Real attribute
        assert real_db.port == 5432  # Real attribute
        assert result == "Partially mocked result"  # Mocked method


def test_mock_side_effects(temp_directory: Path) -> None:
    """Pattern 8: Using side_effects for complex mock behavior."""
    # Arrange: Create mock with side effects
    mock_db = Mock(spec=DatabaseConnection)

    # Configure side effects for different scenarios
    def execute_side_effect(query: str) -> str:
        if "id = 1" in query:
            return "Admin user"
        elif "id = 2" in query:
            return "Regular user"
        else:
            raise ValueError("User not found")

    mock_db.connect.return_value = "Connected"
    mock_db.execute.side_effect = execute_side_effect

    config_file = temp_directory / "config.json"
    config_file.write_text('{"side_effects": true}')

    # Act & Assert: Test different scenarios
    service = UserService(mock_db, config_file)

    # Test admin user
    result1 = service.get_user(1)
    assert result1 == "Admin user"

    # Test regular user
    result2 = service.get_user(2)
    assert result2 == "Regular user"

    # Test error case
    with pytest.raises(ValueError, match="User not found"):
        service.get_user(999)


def test_mock_configuration_patterns(temp_directory: Path) -> None:
    """Pattern 9: Different ways to configure mocks."""
    config_file = temp_directory / "config.json"
    config_file.write_text('{"config_patterns": true}')

    # Method 1: Configure mock after creation
    mock_db1 = Mock(spec=DatabaseConnection)
    mock_db1.connect.return_value = "Method 1"
    mock_db1.execute.return_value = "Config after creation"

    # Method 2: Configure mock at creation
    mock_db2 = Mock(
        spec=DatabaseConnection,
        connect=Mock(return_value="Method 2"),
        execute=Mock(return_value="Config at creation"),
    )

    # Method 3: Using configure_mock
    mock_db3 = Mock(spec=DatabaseConnection)
    mock_db3.configure_mock(
        **{"connect.return_value": "Method 3", "execute.return_value": "Config with configure_mock"}
    )

    # Test all configurations work
    for i, mock_db in enumerate([mock_db1, mock_db2, mock_db3], 1):
        service = UserService(mock_db, config_file)
        result = service.get_user(i)
        assert f"Method {i}" in mock_db.connect.return_value
        assert "Config" in result


def test_mock_assertion_patterns() -> None:
    """Pattern 10: Different ways to assert mock calls."""
    # Arrange
    mock_db = Mock(spec=DatabaseConnection)
    mock_db.connect.return_value = "Connected"
    mock_db.execute.return_value = "Result"

    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"assertions": True}, f)
        config_path = f.name

    try:
        # Act
        service = UserService(mock_db, config_path)
        service.get_user(42)

        # Different assertion patterns:

        # Assert method was called
        mock_db.connect.assert_called()

        # Assert method was called once
        mock_db.execute.assert_called_once()

        # Assert method was called with specific arguments
        mock_db.execute.assert_called_with("SELECT * FROM users WHERE id = 42")

        # Assert method was called once with specific arguments
        mock_db.execute.assert_called_once_with("SELECT * FROM users WHERE id = 42")

        # Assert method was not called
        assert not mock_db.reset_mock.called

        # Check call count
        assert mock_db.connect.call_count == 1
        assert mock_db.disconnect.call_count == 1

        # Check all calls
        expected_calls = [("SELECT * FROM users WHERE id = 42",)]
        actual_calls = [call.args for call in mock_db.execute.call_args_list]
        assert actual_calls == expected_calls

    finally:
        Path(config_path).unlink()


if __name__ == "__main__":
    print("🎭 Mocking Patterns with provide-testkit")
    print("=" * 50)
    print("This example demonstrates various mocking patterns:")
    print("")
    print("  • Mock - Programmable objects that verify behavior")
    print("  • Stub - Simple objects that return fixed values")
    print("  • Spy - Objects that record how they were used")
    print("  • Fake - Objects with working but simplified implementations")
    print("")
    print("📋 Key Patterns Covered:")
    print("  ✓ Basic mocking with unittest.mock")
    print("  ✓ Using @patch decorators")
    print("  ✓ Context manager mocking")
    print("  ✓ Partial mocking")
    print("  ✓ Side effects and complex behavior")
    print("  ✓ Mock configuration techniques")
    print("  ✓ Assertion patterns")
    print("")
    print("🚀 Run with pytest to see examples:")
    print("   pytest examples/patterns/mocking_patterns.py -v")
    print("")
    print("💡 When to use each pattern:")
    print("  • Mocks: When you need to verify interactions")
    print("  • Stubs: When you just need consistent return values")
    print("  • Spies: When you need to observe behavior")
    print("  • Fakes: When you need working test implementations")

# 🧪✅🔚
