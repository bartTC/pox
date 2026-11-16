"""Tests for how the PO-to-Excel converter finds its input files."""

import argparse
import asyncio
import shutil
import sys
from pathlib import Path

import pytest

from pox.base import ConverterError
from pox.cli.main import main
from pox.cli.pox_convert import Po2ExcelConverter

from .conftest import FIXTURES


def _converter(outdir: Path, *patterns: str) -> Po2ExcelConverter:
    opts = argparse.Namespace(
        po_file=list(patterns),
        outdir=outdir,
        filename="{lang}.xlsx",
        language=None,
        fuzzy="stop",
    )
    return Po2ExcelConverter(options=opts)


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
