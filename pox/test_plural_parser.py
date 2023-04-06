import pytest

from .plural_parser import group, parse


def test_japanese():
    expr = "0"
    for i in range(100):
        assert parse(expr, n=i) == 0


def test_english():
    expr = "n != 1"
    assert parse(expr, n=0) == 1
    assert parse(expr, n=1) == 0
    for i in range(2, 100):
        assert parse(expr, n=i) == 1


def test_french():
    expr = "n > 1"
    assert parse(expr, n=0) == 0
    assert parse(expr, n=1) == 0
    for i in range(2, 100):
        assert parse(expr, n=i) == 1


def test_russian():
    expr = "(n == 1) ? 0 : (n == 2) ? 1 : 2"
    assert parse(expr, n=0) == 2
    assert parse(expr, n=1) == 0
    assert parse(expr, n=2) == 1
    for i in range(3, 100):
        assert parse(expr, n=i) == 2


def test_latvian():
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


def test_slovenian():
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


def test_variable_must_be_named_n():
    expr = "x != 1"
    with pytest.raises(ValueError):
        assert parse(expr, n=0)


def test_empty_expression():
    expr = ""
    with pytest.raises(ValueError):
        assert parse(expr, n=0)


def test_group():
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
