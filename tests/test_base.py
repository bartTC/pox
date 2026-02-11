"""Tests for base converters, plural hints, and utility functions."""

import pytest

from pox.base import ArgumentFormatter, BaseConverter, ConverterError
from pox.plurals import _format_values, get_plural_hints
from pox.utils import box_message, dedent, remove_control_characters
from pox.warnings import ConversionErrorDescription as D


def test_fail_raises_converter_error() -> None:
    """Calling fail() raises ConverterError."""
    converter = BaseConverter()
    with pytest.raises(ConverterError):
        converter.fail("something went wrong")


def test_fail_writes_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    """Calling fail() writes the message to stderr."""
    converter = BaseConverter()
    with pytest.raises(ConverterError):
        converter.fail("something went wrong")
    assert "something went wrong" in capsys.readouterr().err


def test_warning_writes_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    """Calling warning() writes the message to stderr."""
    converter = BaseConverter()
    converter.warning("watch out")
    assert "watch out" in capsys.readouterr().err


def test_ok_writes_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """Calling ok() writes the message to stdout."""
    converter = BaseConverter()
    converter.ok("all good")
    assert "all good" in capsys.readouterr().out


def test_display_messages(capsys: pytest.CaptureFixture[str]) -> None:
    """display_messages() outputs conversion issues to stderr."""
    converter = BaseConverter()
    converter.display_messages([D.DECODE_ERROR, D.MISSING_LANGUAGE])
    err = capsys.readouterr().err
    assert "issues during the conversion" in err


def test_argument_formatter() -> None:
    """ArgumentFormatter stores the program name."""
    formatter = ArgumentFormatter("test-prog")
    assert formatter._prog == "test-prog"


def test_plural_hints_none() -> None:
    """None input returns default singular/plural hints."""
    assert get_plural_hints(None) == {0: "Singular", 1: "Plural"}


def test_plural_hints_two_forms() -> None:
    """Standard two-form plural expression returns two hints with examples."""
    result = get_plural_hints("nplurals=2; plural=(n != 1);")
    assert result == {
        0: "Singular, n = 1",
        1: "Plural, n = 0, 2-999",
    }


def test_plural_hints_three_forms() -> None:
    """Three-form plural expression returns three hints with ranges."""
    result = get_plural_hints(
        "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : "
        "n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
    )
    assert result == {
        0: "Singular, n = 1, 21, ...",
        1: "Plural, n = 2-4, 22-24, ...",
        2: "Plural, n = 0, 5-20, ...",
    }


def test_plural_hints_arabic_six_forms() -> None:
    """Arabic six-form plural expression returns six hints with ranges."""
    result = get_plural_hints(
        "nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : "
        "n%100>=3 && n%100<=10 ? 3 : n%100>=11 ? 4 : 5);"
    )
    assert result == {
        0: "Plural, n = 0",
        1: "Singular, n = 1",
        2: "Plural, n = 2",
        3: "Plural, n = 3-10, 103-110, ...",
        4: "Plural, n = 11-99, 111-199, ...",
        5: "Plural, n = 100-102, 200-202, ...",
    }


def test_plural_hints_invalid() -> None:
    """Invalid plural string falls back to default hints."""
    assert get_plural_hints("garbage") == {0: "Singular", 1: "Plural"}


def test_plural_hints_unparseable_formula_falls_back() -> None:
    """Plural form with nplurals but broken formula falls back to numbered forms."""
    result = get_plural_hints("nplurals=3; plural=@@@;")
    assert result == {0: "Plural Form 1", 1: "Plural Form 2", 2: "Plural Form 3"}


def test_format_values_empty() -> None:
    """Empty values list returns empty string."""
    assert _format_values([], has_more=False) == ""


def test_box_message_single_line() -> None:
    """Single-line input produces inline box format."""
    result = box_message("hello")
    assert result == "╼ hello"


def test_box_message_multi_line() -> None:
    """Multi-line input produces bordered box format."""
    result = box_message("line1\nline2\nline3\n")
    assert result.startswith("┍")
    assert "│" in result
    assert "┕" in result


def test_dedent() -> None:
    """Dedent strips leading indent and surrounding blank lines."""
    result = dedent("""
        hello
        world
    """)
    assert result == "hello\nworld"


def test_remove_control_characters() -> None:
    """Control characters are stripped, preserving printable text."""
    result = remove_control_characters("hello\\world\n\t ")
    assert result == "helloworld"
