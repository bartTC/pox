"""Tests for how the PO-to-Excel converter finds its input files."""

import argparse
import asyncio
import shutil
import sys
from pathlib import Path

import pytest
from openpyxl import load_workbook

from pox.base import ConverterError
from pox.cli.main import main
from pox.cli.pox_convert import Po2ExcelConverter

from .conftest import FIXTURES


def _converter(
    outdir: Path,
    *patterns: str,
    language: str | None = None,
    fuzzy: str = "stop",
) -> Po2ExcelConverter:
    opts = argparse.Namespace(
        po_file=list(patterns),
        outdir=outdir,
        filename="{lang}.xlsx",
        language=language,
        fuzzy=fuzzy,
    )
    return Po2ExcelConverter(options=opts)


def _exported_msgids(xlsx_path: Path) -> list[str]:
    wb = load_workbook(str(xlsx_path), read_only=True)
    msgids = [r[2] for r in wb.worksheets[0].iter_rows(min_row=2, values_only=True)]
    wb.close()
    return msgids


@pytest.fixture
def locales(tmp_path: Path) -> Path:
    """Build a locales/<lang>/django.po tree."""
    root = tmp_path / "locales"
    for lang in ("de", "pl"):
        (root / lang).mkdir(parents=True)
        shutil.copy(FIXTURES / "singular.po", root / lang / "django.po")
    return root


def test_absolute_path(tmp_path: Path, locales: Path) -> None:
    """An absolute path to a PO file is accepted."""
    po_path = locales / "de" / "django.po"
    conv = _converter(tmp_path, str(po_path))
    assert conv.po_files == [po_path.resolve()]

    asyncio.run(conv.run())
    assert (tmp_path / "de.xlsx").exists()


def test_absolute_glob(tmp_path: Path, locales: Path) -> None:
    """An absolute glob pattern is expanded."""
    conv = _converter(tmp_path, f"{locales}/*/django.po")
    assert conv.po_files == [
        (locales / "de" / "django.po").resolve(),
        (locales / "pl" / "django.po").resolve(),
    ]


def test_relative_path(
    tmp_path: Path, locales: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A path relative to the working directory is accepted."""
    monkeypatch.chdir(tmp_path)
    conv = _converter(tmp_path, "locales/de/django.po")
    assert conv.po_files == [(locales / "de" / "django.po").resolve()]


@pytest.mark.usefixtures("locales")
def test_recursive_glob(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A relative ** pattern matches PO files at any depth."""
    monkeypatch.chdir(tmp_path)
    conv = _converter(tmp_path, "locales/**/django.po")
    assert len(conv.po_files) == 2


def test_directory_is_skipped(
    tmp_path: Path, locales: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A directory matching the pattern is skipped with a warning."""
    po_path = locales / "pl" / "django.po"
    conv = _converter(tmp_path, str(locales / "de"), str(po_path))
    assert conv.po_files == [po_path.resolve()]
    assert "is a folder" in capsys.readouterr().err


def test_instances_do_not_share_files(tmp_path: Path, locales: Path) -> None:
    """Each converter only holds the files it was given."""
    _converter(tmp_path, str(locales / "de" / "django.po"))
    conv = _converter(tmp_path, str(locales / "pl" / "django.po"))
    assert conv.po_files == [(locales / "pl" / "django.po").resolve()]


def test_unmatched_pattern_warns(
    tmp_path: Path, locales: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A pattern matching nothing warns, and the other files are still used."""
    po_path = locales / "de" / "django.po"
    conv = _converter(tmp_path, str(tmp_path / "missing.po"), str(po_path))
    assert conv.po_files == [po_path.resolve()]
    assert f'No files match "{tmp_path / "missing.po"}"' in capsys.readouterr().err


def test_no_files_found_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """If nothing matches at all, the converter fails instead of doing nothing."""
    with pytest.raises(ConverterError):
        _converter(tmp_path, str(tmp_path / "missing.po"))
    assert "No po files found." in capsys.readouterr().err


def test_cli_exits_nonzero_when_no_files_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The export command exits with status 1 when no PO files are found."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["pox-convert", "export", "-o", str(tmp_path), str(tmp_path / "missing.po")],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


# --- Converting PO files ---


def test_fuzzy_stop_fails_without_writing(tmp_path: Path) -> None:
    """With --fuzzy=stop, a file with fuzzy entries aborts the export."""
    conv = _converter(tmp_path, str(FIXTURES / "fuzzy.po"), fuzzy="stop")
    with pytest.raises(ExceptionGroup) as exc:
        asyncio.run(conv.run())
    assert exc.group_contains(ConverterError, match="Found 1 fuzzy entries")
    assert not list(tmp_path.glob("*.xlsx"))


@pytest.mark.parametrize(
    ("fuzzy", "expected"),
    [
        pytest.param("ignore", ["Hello"], id="ignore-drops-fuzzy"),
        pytest.param("include", ["Hello", "Maybe"], id="include-keeps-fuzzy"),
    ],
)
def test_fuzzy_modes(tmp_path: Path, fuzzy: str, expected: list[str]) -> None:
    """--fuzzy=ignore leaves fuzzy entries out, --fuzzy=include keeps them."""
    conv = _converter(tmp_path, str(FIXTURES / "fuzzy.po"), fuzzy=fuzzy)
    asyncio.run(conv.run())
    assert _exported_msgids(tmp_path / "de.xlsx") == expected


def test_missing_language_skips_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A PO file without a Language header is skipped with an explanation."""
    conv = _converter(tmp_path, str(FIXTURES / "no_language.po"))
    asyncio.run(conv.run())
    assert not list(tmp_path.glob("*.xlsx"))
    out = capsys.readouterr()
    assert 'has no "Language" set' in out.err
    assert "--locale" in out.out + out.err  # the detailed description


@pytest.mark.parametrize(
    "po_name",
    [
        pytest.param("no_language.po", id="po-without-language"),
        pytest.param("singular.po", id="po-with-other-language"),
    ],
)
def test_language_option_overrides_metadata(tmp_path: Path, po_name: str) -> None:
    """--language wins over the PO's own Language header, or fills it in."""
    conv = _converter(tmp_path, str(FIXTURES / po_name), language="fr")
    asyncio.run(conv.run())
    assert [p.name for p in tmp_path.glob("*.xlsx")] == ["fr.xlsx"]


def test_language_option_with_several_files_fails(
    tmp_path: Path, locales: Path
) -> None:
    """--language can't be combined with several files; they'd overwrite."""
    with pytest.raises(ConverterError):
        _converter(tmp_path, f"{locales}/*/django.po", language="fr")


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(b"\xff\xfe\x00\x01binary", id="not-utf8"),
        pytest.param(b"garbage line\n", id="syntax-error"),
    ],
)
def test_unreadable_file_is_skipped(
    tmp_path: Path, content: bytes, capsys: pytest.CaptureFixture[str]
) -> None:
    """A file polib can't parse is skipped with a warning, not a traceback."""
    po_path = tmp_path / "broken.po"
    po_path.write_bytes(content)
    conv = _converter(tmp_path, str(po_path))
    asyncio.run(conv.run())
    assert not list(tmp_path.glob("*.xlsx"))
    assert "is unreadable" in capsys.readouterr().err


def test_several_files_each_get_a_spreadsheet(tmp_path: Path) -> None:
    """Each PO file in a glob produces its own spreadsheet, named by language."""
    for name in ("singular.po", "plurals_polish.po"):
        shutil.copy(FIXTURES / name, tmp_path / name)
    conv = _converter(tmp_path, f"{tmp_path}/*.po")
    asyncio.run(conv.run())
    assert sorted(p.name for p in tmp_path.glob("*.xlsx")) == ["de.xlsx", "pl.xlsx"]


@pytest.mark.xfail(
    strict=True,
    reason="Bug: two PO files with the same language silently overwrite one "
    "spreadsheet. Expected a warning or an error.",
)
def test_same_language_files_do_not_silently_overwrite(
    tmp_path: Path, locales: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Two PO files with the same language don't silently share one output."""
    shutil.copy(locales / "pl" / "django.po", locales / "pl" / "other.po")
    conv = _converter(tmp_path, f"{locales}/pl/*.po")
    asyncio.run(conv.run())
    assert capsys.readouterr().err


def test_empty_po_exports_header_only(tmp_path: Path) -> None:
    """A PO file with no entries exports a sheet with only the header row."""
    po_path = tmp_path / "empty.po"
    po_path.write_text('msgid ""\nmsgstr ""\n"Language: de\\n"\n')
    conv = _converter(tmp_path, str(po_path))
    asyncio.run(conv.run())
    assert _exported_msgids(tmp_path / "de.xlsx") == []
