#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Process Test Fixtures.

Core process testing fixtures with re-exports from specialized modules.
Utilities for testing async code, managing event loops, handling async
subprocess mocking, and bash script testing across the provide-io ecosystem."""

from provide.testkit.process.async_fixtures import (
    async_condition_waiter,
    async_context_manager,
    async_gather_helper,
    async_iterator,
    async_lock,
    async_pipeline,
    async_queue,
    async_rate_limiter,
    async_task_group,
    async_timeout,
    clean_event_loop,
    event_loop_policy,
)
from provide.testkit.process.script_assertions import (
    assert_directory_exists,
    assert_file_contains,
    assert_file_created,
    assert_file_executable,
    assert_file_not_contains,
    assert_git_repo_cloned,
    assert_script_exit_code,
    assert_script_failure,
    assert_script_success,
    assert_stderr_contains,
    assert_stderr_empty,
    assert_stdout_contains,
    assert_stdout_empty,
    assert_symlink_points_to,
)
from provide.testkit.process.script_fixtures import (
    ScriptExecutionContext,
    ScriptResult,
    bash_script_runner,
    git_workspace,
    isolated_workspace,
    mock_git_repo,
    script_execution_context,
)
from provide.testkit.process.subprocess_fixtures import (
    async_mock_server,
    async_stream_reader,
    async_subprocess,
    async_test_client,
    mock_async_process,
)
from provide.testkit.process.system_fixtures import (
    disable_setproctitle,
)

__all__ = [
    # Script testing classes
    "ScriptExecutionContext",
    "ScriptResult",
    # Script assertions
    "assert_directory_exists",
    "assert_file_contains",
    "assert_file_created",
    "assert_file_executable",
    "assert_file_not_contains",
    "assert_git_repo_cloned",
    "assert_script_exit_code",
    "assert_script_failure",
    "assert_script_success",
    "assert_stderr_contains",
    "assert_stderr_empty",
    "assert_stdout_contains",
    "assert_stdout_empty",
    "assert_symlink_points_to",
    # Async fixtures
    "async_condition_waiter",
    "async_context_manager",
    "async_gather_helper",
    "async_iterator",
    "async_lock",
    "async_mock_server",
    "async_pipeline",
    "async_queue",
    "async_rate_limiter",
    "async_stream_reader",
    "async_subprocess",
    "async_task_group",
    "async_test_client",
    "async_timeout",
    # Script fixtures
    "bash_script_runner",
    "clean_event_loop",
    "disable_setproctitle",
    "event_loop_policy",
    "git_workspace",
    "isolated_workspace",
    "mock_async_process",
    "mock_git_repo",
    "script_execution_context",
]

# 🧪✅🔚
