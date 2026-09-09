#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Pytest's capture must give back the stream it took, not the one it remembers.

``SysCaptureBase.resume`` reinstates the stream capture installed at ``start``.
Anything that swapped ``sys.stdout`` after that point -- ``CliRunner.isolation``,
``redirect_stdout``, a fixture of one's own -- is dropped the first time capture
suspends, and every write after that lands in pytest's buffer. Live logging
(``log_cli = true``) suspends capture per record, so one log line emitted from
inside a Click command empties ``result.output`` while the text itself is real.
"""

from __future__ import annotations

from collections.abc import Iterator
import io
import sys

from _pytest.capture import SysCapture
import pytest

from provide.testkit._capture import install_capture_swap_fix

STDOUT_FD = 1


@pytest.fixture
def stdout_restored() -> Iterator[None]:
    """Put ``sys.stdout`` back, however the test under it leaves things."""
    saved = sys.stdout
    try:
        yield
    finally:
        sys.stdout = saved


@pytest.mark.usefixtures("stdout_restored")
def test_resume_returns_a_swap_made_after_capture_started() -> None:
    """The case behind an empty ``CliRunner.result.output``."""
    capture = SysCapture(STDOUT_FD)
    capture.start()
    swapped_in = io.StringIO()
    sys.stdout = swapped_in

    capture.suspend()
    capture.resume()

    assert sys.stdout is swapped_in
    capture.done()


@pytest.mark.usefixtures("stdout_restored")
def test_resume_returns_the_capture_stream_when_nothing_swapped_it() -> None:
    """The ordinary path stays exactly as pytest wrote it."""
    capture = SysCapture(STDOUT_FD)
    capture.start()

    capture.suspend()
    capture.resume()

    assert sys.stdout is capture.tmpfile
    capture.done()


@pytest.mark.usefixtures("stdout_restored")
def test_a_second_suspend_does_not_overwrite_the_remembered_swap() -> None:
    """Suspending while suspended is legal, and must not record ``_old`` as the swap."""
    capture = SysCapture(STDOUT_FD)
    capture.start()
    swapped_in = io.StringIO()
    sys.stdout = swapped_in

    capture.suspend()
    capture.suspend()
    capture.resume()

    assert sys.stdout is swapped_in
    capture.done()


@pytest.mark.usefixtures("stdout_restored")
def test_done_restores_the_stream_capture_replaced() -> None:
    """Teardown belongs to pytest: a foreign swap does not outlive the capture."""
    original = sys.stdout
    capture = SysCapture(STDOUT_FD)
    capture.start()
    sys.stdout = io.StringIO()

    capture.done()

    assert sys.stdout is original


def test_installing_the_fix_again_reports_that_it_was_already_there() -> None:
    """The plugin installs it at import; a second call must not stack a layer."""
    assert install_capture_swap_fix() is False


CLI_UNDER_LIVE_LOGGING = """
import logging

import click
from click.testing import CliRunner


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    # Any library logging from inside the command does this; the record only has
    # to reach the root logger, where live logging is listening.
    logging.getLogger("some.library").warning("a record reaches the root logger")


@cli.command()
def sub() -> None:
    click.echo("SUBCOMMAND OUTPUT")


def test_the_runner_sees_what_the_command_printed() -> None:
    assert CliRunner().invoke(cli, ["sub"]).output != ""
"""


def test_a_cli_runner_keeps_its_output_across_a_live_log_record(pytester: pytest.Pytester) -> None:
    """The reported symptom, through the real Click and the real live-log handler."""
    pytester.makepyfile(CLI_UNDER_LIVE_LOGGING)

    result = pytester.runpytest_subprocess("-o", "log_cli=true")

    result.assert_outcomes(passed=1)


def test_the_same_run_loses_its_output_without_this_plugin(pytester: pytest.Pytester) -> None:
    """Without this, the test above could pass for the wrong reason."""
    pytester.makepyfile(CLI_UNDER_LIVE_LOGGING)

    result = pytester.runpytest_subprocess("-o", "log_cli=true", "-p", "no:provide_testkit")

    result.assert_outcomes(failed=1)
