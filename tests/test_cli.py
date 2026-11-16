"""End-to-end tests driving the pox-convert command line in-process."""

import shutil
import sys
from pathlib import Path

import polib
import pytest

from pox.cli.main import main

from .conftest import FIXTURES, entry_key


def _run(monkeypatch: pytest.MonkeyPatch, *args: str) -> None:
    monkeypatch.setattr(sys, "argv", ["pox-convert", *args])
    main()


def test_export_then_import_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exporting and importing through the CLI gives back the same entries."""
    monkeypatch.chdir(tmp_path)
    shutil.copy(FIXTURES / "entry_types.po", tmp_path / "django.po")

    _run(monkeypatch, "export", "django.po")
    assert (tmp_path / "translations_de.xlsx").exists()

    _run(monkeypatch, "import", "translations_de.xlsx", "-f", "{lang}_back.po")

    source = polib.pofile(str(tmp_path / "django.po"))
    result = polib.pofile(str(tmp_path / "de_back.po"))
    assert [entry_key(e) for e in result] == [entry_key(e) for e in source]
    assert result.metadata == source.metadata


def test_full_po_header_survives_cli_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every header field of a real-world PO file comes back unchanged."""
    monkeypatch.chdir(tmp_path)
    shutil.copy(FIXTURES / "demo.po", tmp_path / "django.po")

    _run(monkeypatch, "export", "--fuzzy", "include", "django.po")
    _run(monkeypatch, "import", "translations_pl.xlsx", "-f", "{lang}_back.po")

    source = polib.pofile(str(tmp_path / "django.po"))
    result = polib.pofile(str(tmp_path / "pl_back.po"))
    assert list(result.metadata.items()) == list(source.metadata.items())


def test_export_fuzzy_stop_exits_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Fuzzy entries abort the export with status 1 and a message, no traceback."""
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "export", "-o", str(tmp_path), str(FIXTURES / "fuzzy.po"))
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "Found 1 fuzzy entries" in err
    assert "Traceback" not in err
    assert not list(tmp_path.glob("*.xlsx"))


def test_export_bad_outdir_exits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing output directory makes the export exit with status 1."""
    with pytest.raises(SystemExit) as exc:
        _run(
            monkeypatch,
            "export",
            "-o",
            str(tmp_path / "missing"),
            str(FIXTURES / "singular.po"),
        )
    assert exc.value.code == 1


def test_import_bad_outdir_exits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing output directory makes the import exit with status 1."""
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "import", "-o", str(tmp_path / "missing"), "x.xlsx")
    assert exc.value.code == 1
