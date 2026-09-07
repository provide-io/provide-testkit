#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Keeping test logging off the path where a console encoding can raise.

This module deliberately imports nothing from Foundation. The plugin that uses
it configures structlog before any Foundation module is imported, and reaching
for Foundation here would defeat that ordering.
"""

from __future__ import annotations

from typing import Any

__all__ = ["unicode_safe"]

_UTF8_NAMES = frozenset({"utf8", "utf_8", "u8", "cp65001"})


class _UnicodeSafeStream:
    """A stream whose writes cannot fail on a character it cannot encode.

    The replacement is written through the same text layer rather than the byte
    layer underneath, so pytest's capture of that stream still sees the output.

    Everything other than `write` is delegated, so the wrapped stream answers
    for its own `isatty`, `flush` and `encoding`.
    """

    # structlog takes a weak reference to the file it logs through, so the
    # slotted class has to allow one.
    __slots__ = ("__weakref__", "_stream")

    def __init__(self, stream: Any) -> None:
        self._stream = stream

    def write(self, text: str) -> int:
        try:
            written = self._stream.write(text)
        except UnicodeEncodeError:
            encoding = getattr(self._stream, "encoding", None) or "ascii"
            # backslashreplace names the character (\U0001f40d) where replace
            # would erase it ('?'), and a test log line is read by a person.
            safe = text.encode(encoding, "backslashreplace").decode(encoding, "replace")
            self._stream.write(safe)
            return len(text)
        # colorama's Windows wrapper returns None rather than a count, so the
        # length of what was handed over stands in for it.
        return written if isinstance(written, int) else len(text)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._stream, name)


def _encodes_everything(stream: Any) -> bool:
    """Whether the stream takes any str without raising."""
    encoding = getattr(stream, "encoding", None)
    if not isinstance(encoding, str):
        # StringIO and friends hold str directly.
        return True
    return encoding.lower().replace("-", "").replace("_", "") in _UTF8_NAMES


def unicode_safe(stream: Any) -> Any:
    """The stream, wrapped only if a character could make it raise.

    Idempotent, so a stream reconfigured repeatedly does not accumulate proxies.
    """
    if isinstance(stream, _UnicodeSafeStream) or _encodes_everything(stream):
        return stream
    return _UnicodeSafeStream(stream)
