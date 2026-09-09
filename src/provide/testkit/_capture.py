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

This belongs in pytest, so the module is built to retire itself rather than to
be remembered. Installing drives a real capture through swap, suspend and
resume, and patches only a pytest that loses the swap -- one that keeps it is
left alone, by whatever route it came to keep it. A pytest that no longer has
the class costs the fix and nothing else: the import is asked for inside the
call rather than at module scope, so a reshaped capture module cannot take the
plugin, and every suite that loads it, down with it.
"""

from __future__ import annotations

import io
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from _pytest.capture import SysCaptureBase

__all__ = ["install_capture_swap_fix"]

_INSTALLED_MARKER = "_provide_testkit_swap_safe"
# The stream is parked on pytest's object, so the name says whose it is.
_SWAPPED_IN = "_provide_testkit_swapped_in"
_STDOUT_FD = 1


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


def _capture_classes() -> tuple[Any, type] | None:
    """The class to patch and the one to probe, or ``None`` from a pytest without them.

    ``SysCaptureBase`` carries the two methods for every capture that reaches
    ``sys``; ``SysCapture`` is the one that can be driven. Asking for them here
    rather than at import is what keeps a renamed or removed class a lost fix
    instead of an ``ImportError`` raised while the plugin is loading.
    """
    try:
        from _pytest.capture import SysCapture, SysCaptureBase
    except (ImportError, AttributeError):
        return None
    return SysCaptureBase, SysCapture


def _drops_a_swap(probe_class: type) -> bool:
    """Whether this pytest loses a stream installed after capturing started.

    The question is behavioural, so the answer is measured rather than read off
    a version: start a capture, swap the stream, cycle suspend and resume, and
    see which stream is left standing. A pytest that keeps the swap wants
    nothing from this module, and a version number cannot say which pytest that
    is -- a backport, a fork or a vendored copy all answer here for themselves.

    A probe that cannot be driven at all -- a capture reshaped past recognition
    -- reports no defect. Patching a class whose behaviour could not be
    established is how a fix becomes the outage.
    """
    saved = sys.stdout
    try:
        probe = probe_class(_STDOUT_FD)
        probe.start()
        try:
            swapped_in = io.StringIO()
            sys.stdout = swapped_in
            probe.suspend()
            probe.resume()
            return sys.stdout is not swapped_in
        finally:
            probe.done()
    except Exception:
        return False
    finally:
        sys.stdout = saved


def install_capture_swap_fix() -> bool:
    """Make pytest's stream capture preserve a swap made after it started.

    Returns whether this call is the one that installed it. Declining leaves
    pytest exactly as found -- a pytest that already keeps the swap, one whose
    methods belong to another patcher, and one this module cannot recognise are
    all cases where doing nothing is the whole job.
    """
    classes = _capture_classes()
    if classes is None:
        return False
    patch_target, probe_class = classes

    # Read the marker off the class itself. A subclass inherits it, and asking
    # through inheritance would report a fix that is not on the class in hand.
    if _INSTALLED_MARKER in patch_target.__dict__:
        return False
    if any(getattr(patch_target, name).__module__ != "_pytest.capture" for name in ("suspend", "resume")):
        return False
    if not _drops_a_swap(probe_class):
        return False

    patch_target.suspend = _suspend
    patch_target.resume = _resume
    setattr(patch_target, _INSTALLED_MARKER, True)
    return True
