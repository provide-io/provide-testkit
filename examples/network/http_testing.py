#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Example: HTTP Client Testing Patterns

This example demonstrates testing HTTP clients and network operations
using provide-testkit's network fixtures and testing patterns.

Key fixtures used:
- temp_directory: For configuration files and test data
- mock_server: HTTP server mocking (if available)
- isolated_cli_runner: For CLI apps that make HTTP requests

Learning objectives:
- Test HTTP clients without external dependencies
- Mock HTTP responses and simulate network conditions
- Test error handling and timeouts
- Validate request/response patterns"""

import json
from pathlib import Path
from typing import Any

import pytest
import requests

from provide.testkit.mocking import Mock, patch


# Example HTTP client to demonstrate testing patterns
class ApiClient:
    """Example HTTP client for API interactions."""

    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def get_user(self, user_id: int) -> dict[str, object]:
        """Get user by ID."""
        url = f"{self.base_url}/api/users/{user_id}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def create_user(self, user_data: dict[str, object]) -> dict[str, object]:
        """Create a new user."""
        url = f"{self.base_url}/api/users"
        response = self.session.post(url, json=user_data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def upload_file(self, file_path: Path, endpoint: str = "/api/upload") -> dict[str, object]:
        """Upload a file to the API."""
        url = f"{self.base_url}{endpoint}"
        with file_path.open("rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            response = self.session.post(url, files=files, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            url = f"{self.base_url}/health"
            response = self.session.get(url, timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False


class ConfigurableClient:
    """HTTP client that loads configuration from files."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.config = self._load_config()
        self.client = ApiClient(
            base_url=self.config["base_url"],
            api_key=self.config.get("api_key"),
            timeout=self.config.get("timeout", 30.0),
        )

    def _load_config(self) -> dict[str, object]:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        return json.loads(self.config_path.read_text())

    def get_all_users(self) -> list[dict[str, object]]:
        """Get all users with pagination."""
        all_users = []
        page = 1
        per_page = self.config.get("per_page", 50)

        while True:
            response = self.client.session.get(
                f"{self.client.base_url}/api/users",
                params={"page": page, "per_page": per_page},
                timeout=self.client.timeout,
            )
            response.raise_for_status()
            data = response.json()

            users = data.get("users", [])
            if not users:
                break

            all_users.extend(users)

            if len(users) < per_page:
                break
            page += 1

        return all_users


# Test Patterns


def test_mock_http_responses() -> None:
    """Pattern 1: Mocking HTTP responses with requests_mock or unittest.mock."""

    # Mock the entire requests.Session.get method
    with patch.object(requests.Session, "get") as mock_get:
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123, "name": "John Doe", "email": "john@example.com"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test the client
        client = ApiClient("https://api.example.com", "test-key")
        user = client.get_user(123)

        # Verify the mock was called correctly
        mock_get.assert_called_once_with("https://api.example.com/api/users/123", timeout=30.0)

        # Verify the result
        assert user["id"] == 123
        assert user["name"] == "John Doe"
        assert user["email"] == "john@example.com"


def test_mock_http_post_request() -> None:
    """Pattern 2: Mocking POST requests with request validation."""

    with patch.object(requests.Session, "post") as mock_post:
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 456,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "created_at": "2024-01-15T10:30:00Z",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test user creation
        client = ApiClient("https://api.example.com", "test-key")
        user_data = {"name": "Jane Smith", "email": "jane@example.com"}
        result = client.create_user(user_data)

        # Verify the request
        mock_post.assert_called_once_with("https://api.example.com/api/users", json=user_data, timeout=30.0)

        # Verify the response
        assert result["id"] == 456
        assert result["name"] == "Jane Smith"


def test_error_handling_patterns() -> None:
    """Pattern 3: Testing error handling and HTTP status codes."""

    # Test 404 Not Found
    with patch.object(requests.Session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        client = ApiClient("https://api.example.com")

        with pytest.raises(requests.HTTPError):
            client.get_user(999)

    # Test connection timeout
    with patch.object(requests.Session, "get") as mock_get:
        mock_get.side_effect = requests.Timeout("Connection timed out")

        client = ApiClient("https://api.example.com")

        with pytest.raises(requests.Timeout):
            client.get_user(123)

    # Test connection error
    with patch.object(requests.Session, "get") as mock_get:
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        client = ApiClient("https://api.example.com")

        with pytest.raises(requests.ConnectionError):
            client.get_user(123)


def test_health_check_scenarios() -> None:
    """Pattern 4: Testing different health check scenarios."""

    # Test healthy service
    with patch.object(requests.Session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = ApiClient("https://api.example.com")
        assert client.health_check() is True

    # Test unhealthy service (500 error)
    with patch.object(requests.Session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        client = ApiClient("https://api.example.com")
        assert client.health_check() is False

    # Test connection timeout
    with patch.object(requests.Session, "get") as mock_get:
        mock_get.side_effect = requests.Timeout("Health check timeout")

        client = ApiClient("https://api.example.com")
        assert client.health_check() is False


def test_file_upload_mocking(temp_directory: Path) -> None:
    """Pattern 5: Mocking file upload operations."""

    # Create a test file
    test_file = temp_directory / "test_upload.txt"
    test_file.write_text("This is test file content for upload testing.")

    with patch.object(requests.Session, "post") as mock_post:
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "file_id": "abc123",
            "filename": "test_upload.txt",
            "size": len(test_file.read_text()),
            "upload_time": "2024-01-15T10:30:00Z",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test file upload
        client = ApiClient("https://api.example.com", "test-key")
        result = client.upload_file(test_file)

        # Verify the upload call
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Check URL and timeout
        assert call_args[1]["timeout"] == 30.0

        # Check that files parameter was passed (exact content hard to verify due to file objects)
        assert "files" in call_args[1]

        # Verify response
        assert result["file_id"] == "abc123"
        assert result["filename"] == "test_upload.txt"


def test_configuration_based_client(temp_directory: Path) -> None:
    """Pattern 6: Testing clients that use configuration files."""

    # Create configuration file
    config_file = temp_directory / "api_config.json"
    config_data = {
        "base_url": "https://api.example.com",
        "api_key": "test-api-key-12345",
        "timeout": 60.0,
        "per_page": 25,
    }
    config_file.write_text(json.dumps(config_data, indent=2))

    with patch.object(requests.Session, "get") as mock_get:
        # Mock paginated response
        def mock_paginated_response(url: str, **kwargs: Any) -> Mock:
            params = kwargs.get("params", {})
            page = params.get("page", 1)

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None

            if page == 1:
                # First page with users
                mock_response.json.return_value = {
                    "users": [{"id": 1, "name": "User 1"}, {"id": 2, "name": "User 2"}]
                }
            else:
                # Empty page (end of results)
                mock_response.json.return_value = {"users": []}

            return mock_response

        mock_get.side_effect = mock_paginated_response

        # Test configurable client
        client = ConfigurableClient(config_file)
        users = client.get_all_users()

        # Verify configuration was loaded
        assert client.config["base_url"] == "https://api.example.com"
        assert client.config["per_page"] == 25

        # Verify API calls
        assert mock_get.call_count == 2  # Two pages (first with data, second empty)

        # Verify results
        assert len(users) == 2
        assert users[0]["name"] == "User 1"
        assert users[1]["name"] == "User 2"


def test_missing_config_file(temp_directory: Path) -> None:
    """Pattern 7: Testing error handling for missing configuration."""

    missing_config = temp_directory / "nonexistent_config.json"

    with pytest.raises(FileNotFoundError, match="Config file not found"):
        ConfigurableClient(missing_config)


def test_headers_and_authentication() -> None:
    """Pattern 8: Testing request headers and authentication."""

    with patch.object(requests.Session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"authenticated": True}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test with API key
        client = ApiClient("https://api.example.com", "secret-api-key")

        # Verify that session headers include authorization
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer secret-api-key"

        # Make a request
        result = client.get_user(123)

        # Verify the request was made
        mock_get.assert_called_once()
        assert result["authenticated"] is True


def test_multiple_sequential_requests() -> None:
    """Pattern 9: Testing sequences of HTTP requests."""

    with patch.object(requests.Session, "get") as mock_get:
        # Configure different responses for different calls
        responses = [
            # First call (user 1)
            Mock(status_code=200, json=lambda: {"id": 1, "name": "Alice"}),
            # Second call (user 2)
            Mock(status_code=200, json=lambda: {"id": 2, "name": "Bob"}),
            # Third call (user 3)
            Mock(status_code=200, json=lambda: {"id": 3, "name": "Charlie"}),
        ]

        for response in responses:
            response.raise_for_status.return_value = None

        mock_get.side_effect = responses

        # Test multiple requests
        client = ApiClient("https://api.example.com")
        users = []

        for user_id in [1, 2, 3]:
            user = client.get_user(user_id)
            users.append(user)

        # Verify all requests were made
        assert mock_get.call_count == 3

        # Verify responses
        assert len(users) == 3
        assert users[0]["name"] == "Alice"
        assert users[1]["name"] == "Bob"
        assert users[2]["name"] == "Charlie"


def test_timeout_configuration() -> None:
    """Pattern 10: Testing timeout configuration and behavior."""

    # Test default timeout
    client = ApiClient("https://api.example.com")
    assert client.timeout == 30.0

    # Test custom timeout
    client = ApiClient("https://api.example.com", timeout=10.0)
    assert client.timeout == 10.0

    # Test that timeout is passed to requests
    with patch.object(requests.Session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client.get_user(123)

        # Verify timeout was passed
        mock_get.assert_called_once_with("https://api.example.com/api/users/123", timeout=10.0)


if __name__ == "__main__":
    print("🌐 HTTP Client Testing Patterns with provide-testkit")
    print("=" * 60)
    print("This example demonstrates HTTP client testing patterns:")
    print("")
    print("  • Mocking HTTP responses with unittest.mock")
    print("  • Testing error conditions and timeouts")
    print("  • Validating request parameters and headers")
    print("  • Testing authentication mechanisms")
    print("  • Handling file uploads and downloads")
    print("  • Configuration-based client testing")
    print("")
    print("📋 Key Patterns Covered:")
    print("  ✓ Response mocking and validation")
    print("  ✓ Error handling (404, 500, timeouts, connection errors)")
    print("  ✓ Sequential and paginated requests")
    print("  ✓ Authentication header testing")
    print("  ✓ File upload operations")
    print("  ✓ Configuration management")
    print("  ✓ Health check patterns")
    print("")
    print("🚀 Run with pytest to see examples:")
    print("   pytest examples/network/http_testing.py -v")
    print("")
    print("💡 Key Benefits:")
    print("  • Test without external services")
    print("  • Simulate network conditions")
    print("  • Validate request/response patterns")
    print("  • Ensure proper error handling")

# 🧪✅🔚
