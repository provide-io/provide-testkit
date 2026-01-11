#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Subprocess-specific test fixtures for process testing.

Provides fixtures for mocking and testing subprocess operations,
stream handling, and process communication."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from typing import Any

import pytest

from provide.testkit.mocking import AsyncMock, Mock


class AsyncMockServer:
    """Simple async HTTP-like server mock."""

    def __init__(self) -> None:
        self.started = False
        self.host = "localhost"
        self.port = 8080
        self.connections: list[dict[str, Any]] = []
        self.requests: list[bytes] = []

    async def start(self, host: str = "localhost", port: int = 8080) -> None:
        """Start the mock server."""
        self.started = True
        self.host = host
        self.port = port

    async def stop(self) -> None:
        """Stop the mock server and close connections."""
        self.started = False
        for conn in self.connections:
            writer = conn.get("writer")
            if writer is not None:
                writer.close()
                await writer.wait_closed()

    async def handle_connection(self, reader: Any, writer: Any) -> None:
        """Mock connection handler."""
        connection = {"reader": reader, "writer": writer}
        self.connections.append(connection)

        data = await reader.read(1024)
        self.requests.append(data)

        writer.write(b"HTTP/1.1 200 OK\r\n\r\nOK")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    def get_url(self) -> str:
        """Return the server URL."""
        return f"http://{self.host}:{self.port}"


class AsyncTestClient:
    """Lightweight async HTTP client mock."""

    def __init__(self) -> None:
        self.responses: dict[str, dict[str, Any]] = {}
        self.requests: list[dict[str, Any]] = []

    def set_response(self, url: str, response: dict[str, Any]) -> None:
        """Register a mock response for a URL."""
        self.responses[url] = response

    async def get(self, url: str, **kwargs: Any) -> dict[str, Any]:
        """Mock GET request."""
        self.requests.append({"method": "GET", "url": url, "kwargs": kwargs})
        return self.responses.get(url, {"status": 404, "body": "Not Found"})

    async def post(self, url: str, data: Any | None = None, **kwargs: Any) -> dict[str, Any]:
        """Mock POST request."""
        self.requests.append({"method": "POST", "url": url, "data": data, "kwargs": kwargs})
        return self.responses.get(url, {"status": 200, "body": "OK"})

    async def close(self) -> None:
        """Close the client."""
        return None

    async def __aenter__(self) -> AsyncTestClient:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any
    ) -> None:
        await self.close()


@pytest.fixture
def mock_async_process() -> AsyncMock:
    """
    Mock async subprocess for testing.

    Returns:
        AsyncMock configured as a subprocess with common attributes.
    """
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(return_value=(b"output", b""))
    mock_process.returncode = 0
    mock_process.pid = 12345
    mock_process.stdin = AsyncMock()
    mock_process.stdout = AsyncMock()
    mock_process.stderr = AsyncMock()
    mock_process.wait = AsyncMock(return_value=0)
    mock_process.kill = Mock()
    mock_process.terminate = Mock()

    return mock_process


@pytest.fixture
async def async_stream_reader() -> AsyncMock:
    """
    Mock async stream reader for subprocess stdout/stderr.

    Returns:
        AsyncMock configured as a stream reader.
    """
    reader = AsyncMock()

    # Simulate reading lines
    async def readline_side_effect() -> AsyncGenerator[bytes, None]:
        for line in [b"line1\n", b"line2\n", b""]:
            yield line

    reader.readline = AsyncMock(side_effect=readline_side_effect().__anext__)
    reader.read = AsyncMock(return_value=b"full content")
    reader.at_eof = Mock(side_effect=[False, False, True])

    return reader


@pytest.fixture
def async_subprocess() -> Callable[[int, bytes, bytes, int], AsyncMock]:
    """
    Create mock async subprocess for testing.

    Returns:
        Function that creates mock subprocess with configurable behavior.
    """

    def _create_subprocess(
        returncode: int = 0,
        stdout: bytes = b"",
        stderr: bytes = b"",
        pid: int = 12345,
    ) -> AsyncMock:
        """
        Create a mock async subprocess.

        Args:
            returncode: Process return code
            stdout: Process stdout output
            stderr: Process stderr output
            pid: Process ID

        Returns:
            AsyncMock configured as subprocess
        """
        process = AsyncMock()
        process.returncode = returncode
        process.pid = pid
        process.communicate = AsyncMock(return_value=(stdout, stderr))
        process.wait = AsyncMock(return_value=returncode)
        process.kill = Mock()
        process.terminate = Mock()
        process.send_signal = Mock()

        # Add stdout/stderr as async stream readers
        process.stdout = AsyncMock()
        process.stdout.read = AsyncMock(return_value=stdout)
        process.stdout.readline = AsyncMock(side_effect=[stdout, b""])
        process.stdout.at_eof = Mock(side_effect=[False, True])

        process.stderr = AsyncMock()
        process.stderr.read = AsyncMock(return_value=stderr)
        process.stderr.readline = AsyncMock(side_effect=[stderr, b""])
        process.stderr.at_eof = Mock(side_effect=[False, True])

        process.stdin = AsyncMock()
        process.stdin.write = AsyncMock()
        process.stdin.drain = AsyncMock()
        process.stdin.close = Mock()

        return process

    return _create_subprocess


@pytest.fixture
def async_mock_server() -> AsyncMockServer:
    """
    Create a mock async server for testing.

    Returns:
        Mock server with async methods.
    """

    return AsyncMockServer()


@pytest.fixture
def async_test_client() -> AsyncTestClient:
    """
    Create an async HTTP test client.

    Returns:
        Mock async HTTP client for testing.
    """

    return AsyncTestClient()


__all__ = [
    "async_mock_server",
    "async_stream_reader",
    "async_subprocess",
    "async_test_client",
    "mock_async_process",
]

# 🧪✅🔚
