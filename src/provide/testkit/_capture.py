#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Capture that gives back the stream it took, not the one it remembers.

``SysCaptureBase.suspend`` hands ``sys.stdout`` back to the stream pytest saved
before capture started, and ``resume`` reinstates ``tmpfile`` -- the stream
capture installed at ``start``. Neither looks at what is actually there. A test
that swaps the stream after capture started owns something pytest has no record
of, so the swap is discarded on the first suspend and every write after it lands
in pytest's buffer instead of the caller's.

``log_cli = true`` makes that ordinary: pytest's live-log handler sits on the
root logger and suspends global capture around each record. One log line emitted
from inside ``CliRunner.invoke`` -- from any library, at any depth -- leaves
``result.output`` empty while the text itself is real and lands in pytest's own
capture. ``contextlib.redirect_stdout`` and hand-rolled stream fixtures lose
their swap the same way.

The pair below remembers the stream that was in place at suspend and returns it
at resume, which is what the two methods already claim to do. Teardown is
untouched: ``done`` still restores the stream capture replaced, so a swap left
behind by a test cannot outlive it.

This belongs in pytest, and the tests in ``tests/test_capture_stream_swap.py``
drive the real ``SysCapture``, so they fail loudly once pytest changes the
methods underneath -- whether it fixes this or reshapes the class. Drop this
module when the pytest floor carries the fix.
"""

from __future__ import annotations

import sys
from typing import Any

from _pytest.capture import SysCaptureBase

__all__ = ["install_capture_swap_fix"]

_INSTALLED_MARKER = "_provide_testkit_swap_safe"
# The stream is parked on pytest's object, so the name says whose it is.
_SWAPPED_IN = "_provide_testkit_swapped_in"


def _suspend(self: SysCaptureBase[Any]) -> None:
    self._assert_state("suspend", ("started", "suspended"))
    # Suspending while suspended is legal, and the stream sitting there then is
    # the one suspend itself installed -- not a swap worth remembering.
    if self._state == "started":
        setattr(self, _SWAPPED_IN, getattr(sys, self.name))
    setattr(sys, self.name, self._old)
    self._state = "suspended"


def _resume(self: SysCaptureBase[Any]) -> None:
    self._assert_state("resume", ("started", "suspended"))
    if self._state == "started":
        return
    # A capture resumed without ever suspending has nothing recorded, and the
    # stream capture installed is the right answer for it.
    setattr(sys, self.name, getattr(self, _SWAPPED_IN, self.tmpfile))
    self._state = "started"


def install_capture_swap_fix() -> bool:
    """Make pytest's stream capture preserve a swap made after it started.

    Returns whether this call is the one that installed it. Declining leaves
    pytest exactly as found: the fix is worth having, and silently layering it
    over a patch someone else installed is not.
    """
    if getattr(SysCaptureBase, _INSTALLED_MARKER, False):
        return False
    if any(getattr(SysCaptureBase, name).__module__ != "_pytest.capture" for name in ("suspend", "resume")):
        return False
    SysCaptureBase.suspend = _suspend  # type: ignore[method-assign]
    SysCaptureBase.resume = _resume  # type: ignore[method-assign]
    setattr(SysCaptureBase, _INSTALLED_MARKER, True)
    return True
