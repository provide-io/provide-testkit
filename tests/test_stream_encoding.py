#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test logging must not raise on a console that cannot encode the message.

The plugin configures structlog before Foundation is imported, so the stream it
hands structlog is whatever pytest is holding at that moment. On Windows that is
a cp1252 console behind colorama, and a log line carrying an emoji raised
UnicodeEncodeError out of the logging call and into the test.
"""

from __future__ import annotations

import io

from provide.testkit._streams import unicode_safe


class _Cp1252Stream(io.TextIOWrapper):
    """Stands in for the Windows console pytest hands the plugin."""

    def __init__(self) -> None:
        super().__init__(io.BytesIO(), encoding="cp1252", newline="")

    def written(self) -> str:
        self.flush()
        return self.buffer.getvalue().decode("cp1252")  # type: ignore[attr-defined]


def test_the_stand_in_really_does_raise() -> None:
    """Without this, every test below could pass for the wrong reason."""
    try:
        _Cp1252Stream().write("\U0001f40d")
    except UnicodeEncodeError:
        return
    raise AssertionError("the cp1252 stand-in accepted an emoji")


def test_an_unencodable_character_does_not_raise() -> None:
    unicode_safe(_Cp1252Stream()).write("repo \U0001f40d state\n")


def test_the_surrounding_text_survives() -> None:
    stream = _Cp1252Stream()

    unicode_safe(stream).write("repo \U0001f40d state\n")

    written = stream.written()
    assert "repo " in written
    assert "state" in written


def test_the_character_is_named_rather_than_dropped() -> None:
    """backslashreplace keeps the emoji readable; 'replace' would give '?'."""
    stream = _Cp1252Stream()

    unicode_safe(stream).write("\U0001f40d\n")

    assert "\\U0001f40d" in stream.written()


def test_a_stream_that_can_encode_is_handed_back_unchanged() -> None:
    stream = io.StringIO()

    assert unicode_safe(stream) is stream


def test_wrapping_is_idempotent() -> None:
    wrapped = unicode_safe(_Cp1252Stream())

    assert unicode_safe(wrapped) is wrapped


def test_the_wrapper_delegates_what_it_does_not_define() -> None:
    stream = _Cp1252Stream()

    assert unicode_safe(stream).encoding == "cp1252"


def test_the_plugin_configures_a_stream_that_cannot_raise(monkeypatch) -> None:
    """The regression: the plugin handed structlog the raw console."""
    import structlog

    monkeypatch.setattr("sys.stdout", _Cp1252Stream())

    import provide.testkit.pytest_plugin as plugin

    plugin._configure_test_structlog()

    structlog.get_config()["logger_factory"]().msg("repo \U0001f40d state")
