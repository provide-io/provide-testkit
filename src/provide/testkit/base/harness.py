"""
Harness Testing Utilities.

Provides utilities for testing CLI harnesses with artifact management.
"""

from pathlib import Path

from provide.foundation.process.runner import run_command


class HarnessRunner:
    """Test harness runner with artifact management."""

    def __init__(self, artifact_root: Path):
        """Initialize with artifact root directory."""
        self.artifact_root = artifact_root

    def run(
        self,
        command: list[str],
        artifact_path: Path | str,
        stdin: str | bytes | None = None,
        timeout: float = 30.0,
        cwd: Path | None = None,
    ) -> tuple[int, str, str]:
        """
        Run command and return text output.

        For binary output commands, use run_binary() instead.
        """
        exit_code, stdout_str, stderr_str, _, _ = self._run_internal(
            command, artifact_path, stdin, timeout, cwd
        )
        return exit_code, stdout_str, stderr_str

    def run_binary(
        self,
        command: list[str],
        artifact_path: Path | str,
        stdin: str | bytes | None = None,
        timeout: float = 30.0,
        cwd: Path | None = None,
    ) -> tuple[int, bytes, bytes]:
        """
        Run command and return binary output.

        Use this for commands that output binary data.
        """
        exit_code, _, _, stdout_bytes, stderr_bytes = self._run_internal(
            command, artifact_path, stdin, timeout, cwd
        )
        return exit_code, stdout_bytes, stderr_bytes

    def _run_internal(
        self,
        command: list[str],
        artifact_path: Path | str,
        stdin: str | bytes | None = None,
        timeout: float = 30.0,
        cwd: Path | None = None,
    ) -> tuple[int, str, str, bytes, bytes]:
        """
        Internal run method that returns both text and binary outputs.

        Returns:
            Tuple of (exit_code, stdout_str, stderr_str, stdout_bytes, stderr_bytes)
        """
        # Create artifact directory
        artifact_dir = self.artifact_root / artifact_path
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Save command and stdin
        (artifact_dir / "cmd.txt").write_text(" ".join(command))
        if stdin:
            (artifact_dir / "stdin.txt").write_bytes(stdin.encode() if isinstance(stdin, str) else stdin)

        # Run command in binary mode to handle binary outputs
        result = run_command(
            command,
            cwd=cwd,
            input=stdin,
            timeout=timeout,
            check=False,  # Don't raise on non-zero exit
            text=False,  # Binary mode to handle binary data
            env={"PROVIDE_TELEMETRY_DISABLED": "true"},
        )

        # Handle binary outputs - return as bytes for binary data, decode for text
        stdout_bytes = result.stdout if isinstance(result.stdout, bytes) else result.stdout.encode()
        stderr_bytes = result.stderr if isinstance(result.stderr, bytes) else result.stderr.encode()

        # Try to decode as text for logging/artifacts, but preserve original bytes
        try:
            stdout_str = stdout_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # For binary output, save as hex dump for debugging
            import base64

            stdout_str = f"[Binary data - base64]: {base64.b64encode(stdout_bytes).decode('ascii')}"

        try:
            stderr_str = stderr_bytes.decode("utf-8")
        except UnicodeDecodeError:
            stderr_str = f"[Binary stderr]: {stderr_bytes.decode('utf-8', errors='replace')}"

        # Save outputs
        (artifact_dir / "stdout.txt").write_text(stdout_str)
        (artifact_dir / "stderr.txt").write_text(stderr_str)
        (artifact_dir / "exitcode.txt").write_text(str(result.returncode))

        # Save raw binary outputs for binary commands
        if stdout_bytes:
            (artifact_dir / "stdout.bin").write_bytes(stdout_bytes)
        if stderr_bytes:
            (artifact_dir / "stderr.bin").write_bytes(stderr_bytes)

        # Return all formats
        return result.returncode, stdout_str, stderr_str, stdout_bytes, stderr_bytes


__all__ = ["HarnessRunner"]
