"""Tests for the plural formula parser."""

import pytest

from pox.plural_parser import Token, group, parse


def test_japanese() -> None:
    """Japanese has a single plural form for all n."""
    expr = "0"
    for i in range(100):
        assert parse(expr, n=i) == 0


def test_english() -> None:
    """English: singular for n=1, plural otherwise."""
    expr = "n != 1"
    assert parse(expr, n=0) == 1
    assert parse(expr, n=1) == 0
    for i in range(2, 100):
        assert parse(expr, n=i) == 1


def test_french() -> None:
    """French: singular for n=0 and n=1, plural for n>1."""
    expr = "n > 1"
    assert parse(expr, n=0) == 0
    assert parse(expr, n=1) == 0
    for i in range(2, 100):
        assert parse(expr, n=i) == 1


def test_russian() -> None:
    """Russian: three forms based on equality checks."""
    expr = "(n == 1) ? 0 : (n == 2) ? 1 : 2"
    assert parse(expr, n=0) == 2
    assert parse(expr, n=1) == 0
    assert parse(expr, n=2) == 1
    for i in range(3, 100):
        assert parse(expr, n=i) == 2


def test_latvian() -> None:
    """Latvian: three forms with modulo and logical operators."""
    expr = "n % 10 == 1 && n % 100 != 11 ? 0 : n != 0 ? 1 : 2"
    assert parse(expr, n=0) == 2
    assert parse(expr, n=1) == 0
    assert parse(expr, n=2) == 1
    assert parse(expr, n=10) == 1
    assert parse(expr, n=11) == 1
    assert parse(expr, n=12) == 1
    assert parse(expr, n=20) == 1
    assert parse(expr, n=21) == 0
    assert parse(expr, n=22) == 1
    assert parse(expr, n=100) == 1
    assert parse(expr, n=101) == 0
    assert parse(expr, n=102) == 1
    assert parse(expr, n=110) == 1
    assert parse(expr, n=111) == 1
    assert parse(expr, n=112) == 1
    assert parse(expr, n=120) == 1
    assert parse(expr, n=121) == 0
    assert parse(expr, n=122) == 1


def test_slovenian() -> None:
    """Slovenian: four forms with modulo 100 checks."""
    expr = "(n % 100 == 1) ? 1 : (n % 100 == 2) ? 2 : (n % 100 == 3 || n % 100 == 4) ? 3 : 0"

    assert parse(expr, n=0) == 0
    assert parse(expr, n=1) == 1
    assert parse(expr, n=2) == 2
    assert parse(expr, n=3) == 3
    assert parse(expr, n=4) == 3
    for i in range(5, 100):
        assert parse(expr, n=i) == 0
    assert parse(expr, n=100) == 0
    assert parse(expr, n=101) == 1
    assert parse(expr, n=102) == 2
    assert parse(expr, n=103) == 3
    assert parse(expr, n=104) == 3
    for i in range(105, 200):
        assert parse(expr, n=i) == 0


def test_variable_must_be_named_n() -> None:
    """Only the variable 'n' is allowed in formulas."""
    expr = "x != 1"
    with pytest.raises(ValueError, match="Invalid character"):
        assert parse(expr, n=0)


def test_empty_expression() -> None:
    """An empty expression raises a ValueError."""
    expr = ""
    with pytest.raises(ValueError, match="Invalid syntax"):
        assert parse(expr, n=0)


def test_token_repr() -> None:
    """Token repr shows type and value."""
    t = Token("INTEGER", 42)
    assert repr(t) == "Token('INTEGER', 42)"


def test_not_operator() -> None:
    """The ! operator negates a value."""
    assert parse("!0", n=0)
    assert not parse("!1", n=0)


def test_arithmetic_operators() -> None:
    """Arithmetic operators produce correct results."""
    assert parse("n * 2", n=3) == 6
    assert parse("n / 2", n=7) == 3
    assert parse("n + 2", n=3) == 5
    assert parse("n - 1", n=5) == 4
    assert parse("n ^ 2", n=3) == 9


def test_undefined_variable() -> None:
    """Referencing n without binding it raises ValueError."""
    with pytest.raises(ValueError, match="not defined"):
        parse("n", x=1)


def test_invalid_character() -> None:
    """An unsupported character raises ValueError."""
    with pytest.raises(ValueError, match="Invalid character"):
        parse("n @ 1", n=1)


def test_invalid_logical_operator() -> None:
    """A malformed logical operator raises ValueError."""
    with pytest.raises(ValueError, match="Invalid character"):
        parse("n == 1 &| 1", n=1)


def test_group() -> None:
    """Group function partitions n-values by plural form."""
    expr = "n==1 ? 0 : n==2 ? 1 : 2"
    assert parse(expr, n=0) == 2
    assert parse(expr, n=1) == 0
    assert parse(expr, n=2) == 1
    for i in range(3, 100):
        assert parse(expr, n=i) == 2
    groups = list(group(f"Plural-Forms: nplurals=3; plural={expr}"))
    assert groups == [
        {"group": 0, "values": [1], "has_more": False},
        {"group": 1, "values": [2], "has_more": False},
        {"group": 2, "values": [0, 3, 4, 5, 6], "has_more": True},
    ]


def test_eat_wrong_token_type_raises() -> None:
    """Calling eat() with a mismatched token type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid syntax"):
        parse("(1")


def test_factor_unexpected_token_raises() -> None:
    """An unexpected token in factor position raises ValueError."""
    with pytest.raises(ValueError, match="Invalid syntax"):
        parse("+")
