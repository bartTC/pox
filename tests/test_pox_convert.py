"""Tests for how the PO-to-Excel converter finds its input files."""

import argparse
import asyncio
import shutil
from pathlib import Path

import pytest

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
    conv = _converter(tmp_path, str(locales / "de"))
    assert conv.po_files == []
    assert "folder" in capsys.readouterr().err.lower()


def test_instances_do_not_share_files(tmp_path: Path, locales: Path) -> None:
    """Each converter only holds the files it was given."""
    _converter(tmp_path, str(locales / "de" / "django.po"))
    conv = _converter(tmp_path, str(locales / "pl" / "django.po"))
    assert conv.po_files == [(locales / "pl" / "django.po").resolve()]
