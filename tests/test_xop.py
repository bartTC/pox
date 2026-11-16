"""Tests for Excel-to-PO conversion (xop-convert) and roundtrip."""

import argparse
from pathlib import Path

import polib
import pytest
from openpyxl import Workbook, load_workbook
from openpyxl.packaging.custom import StringProperty

from pox.base import ConverterError
from pox.cli.xop_convert import Excel2PoConverter
from pox.spreadsheet import SpreadsheetGenerator

from .conftest import FIXTURES, build_context, entry_key


def test_singular_roundtrip(tmp_path: Path, singular_xlsx: Path) -> None:
    """Singular entries survive a PO-to-Excel-to-PO roundtrip."""
    opts = argparse.Namespace(
        xlsx_file=[str(singular_xlsx)],
        outdir=tmp_path,
        filename="{lang}_roundtrip.po",
    )
    converter = Excel2PoConverter(options=opts)
    converter.run()

    result_po = polib.pofile(str(tmp_path / "de_roundtrip.po"))
    msgids = [e.msgid for e in result_po]
    assert "Hello" in msgids
    assert "Goodbye" in msgids
    assert "Open" in msgids


def test_singular_translation_preserved(tmp_path: Path, singular_xlsx: Path) -> None:
    """Singular translation values are preserved through roundtrip."""
    opts = argparse.Namespace(
        xlsx_file=[str(singular_xlsx)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    converter = Excel2PoConverter(options=opts)
    converter.run()

    result_po = polib.pofile(str(tmp_path / "de.po"))
    entries = {e.msgid: e for e in result_po}
    assert entries["Hello"].msgstr == "Hallo"


def test_language_metadata_preserved(tmp_path: Path, singular_xlsx: Path) -> None:
    """Language metadata is preserved through roundtrip."""
    opts = argparse.Namespace(
        xlsx_file=[str(singular_xlsx)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    converter = Excel2PoConverter(options=opts)
    converter.run()

    result_po = polib.pofile(str(tmp_path / "de.po"))
    assert result_po.metadata["Language"] == "de"


def test_plural_roundtrip(tmp_path: Path, plurals_xlsx: Path) -> None:
    """Plural entries survive a PO-to-Excel-to-PO roundtrip."""
    opts = argparse.Namespace(
        xlsx_file=[str(plurals_xlsx)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    converter = Excel2PoConverter(options=opts)
    converter.run()

    result_po = polib.pofile(str(tmp_path / "de.po"))
    plural_entries = [e for e in result_po if e.msgid_plural]
    assert len(plural_entries) >= 1
    entry = plural_entries[0]
    assert entry.msgstr_plural[0] == "%d Gegenstand"
    assert entry.msgstr_plural[1] == "%d Gegenstaende"


def test_context_roundtrip(tmp_path: Path, singular_xlsx: Path) -> None:
    """Message context (msgctxt) is preserved through roundtrip."""
    opts = argparse.Namespace(
        xlsx_file=[str(singular_xlsx)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    converter = Excel2PoConverter(options=opts)
    converter.run()

    result_po = polib.pofile(str(tmp_path / "de.po"))
    entries = {e.msgid: e for e in result_po}
    assert entries["Open"].msgctxt == "adjective"


def test_bad_outdir_fails(tmp_path: Path) -> None:
    """Non-existent output directory raises ConverterError."""
    opts = argparse.Namespace(
        xlsx_file=[],
        outdir=tmp_path / "nonexistent",
        filename="{lang}.po",
    )
    with pytest.raises(ConverterError):
        Excel2PoConverter(options=opts)


def test_no_translations_sheet_fails(tmp_path: Path) -> None:
    """Missing Translations sheet raises ConverterError."""
    xlsx_path = tmp_path / "bad.xlsx"
    wb = Workbook()
    wb.worksheets[0].title = "NotTranslations"
    wb.save(str(xlsx_path))
    wb.close()

    opts = argparse.Namespace(
        xlsx_file=[str(xlsx_path)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    converter = Excel2PoConverter(options=opts)
    with pytest.raises(ConverterError):
        converter.run()


def test_not_enough_rows_fails(tmp_path: Path) -> None:
    """Sheet with insufficient rows raises ConverterError."""
    xlsx_path = tmp_path / "empty.xlsx"
    wb = Workbook()
    ws = wb.worksheets[0]
    ws.title = "Translations (de)"
    # Only one row (header), no data — but we need < 2 rows total
    # So leave the sheet completely empty
    wb.save(str(xlsx_path))
    wb.close()

    opts = argparse.Namespace(
        xlsx_file=[str(xlsx_path)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    converter = Excel2PoConverter(options=opts)
    with pytest.raises(ConverterError):
        converter.run()


def test_no_language_property_uses_filename(
    tmp_path: Path, no_language_xlsx: Path
) -> None:
    """Missing Language property falls back to filename extraction."""
    opts = argparse.Namespace(
        xlsx_file=[str(no_language_xlsx)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    converter = Excel2PoConverter(options=opts)
    converter.run()

    # Filename is test_en.xlsx, so language extracted from stem is "en"
    result_po = polib.pofile(str(tmp_path / "en.po"))
    assert result_po.metadata["Language"] == "en"


def test_empty_rows_skipped(tmp_path: Path) -> None:
    """Empty/None rows in the xlsx data are skipped."""
    xlsx_path = tmp_path / "gaps.xlsx"
    wb = Workbook()
    ws = wb.worksheets[0]
    ws.title = "Translations (de)"
    ws.append(["id", "Context", "Source Language", "Translation"])
    ws.append([1, None, "Hello", "Hallo"])
    ws.append([None, None, None, None])  # empty row
    ws.append(["", None, None, None])  # blank id row
    ws.append([2, None, "World", "Welt"])
    wb.custom_doc_props.append(StringProperty(name="Language", value="de"))
    wb.save(str(xlsx_path))
    wb.close()

    opts = argparse.Namespace(
        xlsx_file=[str(xlsx_path)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    converter = Excel2PoConverter(options=opts)
    converter.run()

    result_po = polib.pofile(str(tmp_path / "de.po"))
    msgids = [e.msgid for e in result_po]
    assert "Hello" in msgids
    assert "World" in msgids
    assert len(result_po) == 2


def test_obsolete_entry_roundtrip(tmp_path: Path, singular_xlsx: Path) -> None:
    """Obsolete entries have context set to None (not 'obsolete' string)."""
    opts = argparse.Namespace(
        xlsx_file=[str(singular_xlsx)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    converter = Excel2PoConverter(options=opts)
    converter.run()

    result_po = polib.pofile(str(tmp_path / "de.po"))
    # The obsolete marker in context column should not leak as msgctxt
    for entry in result_po:
        assert entry.msgctxt != "obsolete"


def test_singular_entry_in_plural_sheet_stays_singular(
    tmp_path: Path, plurals_xlsx: Path
) -> None:
    """A singular message in a sheet with plural columns imports as singular."""
    opts = argparse.Namespace(
        xlsx_file=[str(plurals_xlsx)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    Excel2PoConverter(options=opts).run()

    result_po = polib.pofile(str(tmp_path / "de.po"))
    entries = {e.msgid: e for e in result_po}
    assert entries["Hello"].msgstr == "Hallo"
    assert not entries["Hello"].msgid_plural
    assert not entries["Hello"].msgstr_plural


def _import(tmp_path: Path, xlsx_path: Path) -> polib.POFile:
    opts = argparse.Namespace(
        xlsx_file=[str(xlsx_path)],
        outdir=tmp_path,
        filename="{lang}.po",
    )
    Excel2PoConverter(options=opts).run()
    return polib.pofile(str(tmp_path / "de.po"))


def _export(tmp_path: Path, po_content: str) -> Path:
    po_path = tmp_path / "input.po"
    po_path.write_text(PO_HEADER + po_content)
    gen = SpreadsheetGenerator(outdir=tmp_path)
    return gen.generate(filename="test_{lang}.xlsx", context=build_context(po_path))


PO_HEADER = """msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: de\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

"""

MIXED_UNTRANSLATED_PO = """msgid "%d item"
msgid_plural "%d items"
msgstr[0] ""
msgstr[1] ""

msgid "%d file"
msgid_plural "%d files"
msgstr[0] "%d Datei"
msgstr[1] "%d Dateien"

msgid "Hello"
msgstr "Hallo"

msgid "Goodbye"
msgstr ""
"""


def test_untranslated_plural_entry_stays_plural(tmp_path: Path) -> None:
    """A plural row with every form empty imports as plural."""
    po = _import(tmp_path, _export(tmp_path, MIXED_UNTRANSLATED_PO))
    entries = {e.msgid: e for e in po}
    assert entries["%d item"].msgid_plural == "%d items"
    assert entries["%d item"].msgstr_plural == {0: "", 1: ""}


def test_plural_source_roundtrip(tmp_path: Path) -> None:
    """Both msgid and msgid_plural of a plural entry survive a roundtrip."""
    po = _import(tmp_path, _export(tmp_path, MIXED_UNTRANSLATED_PO))
    entries = {e.msgid: e for e in po}
    assert entries["%d file"].msgid_plural == "%d files"
    assert entries["%d file"].msgstr_plural == {0: "%d Datei", 1: "%d Dateien"}


def test_multiline_plural_source_roundtrip(tmp_path: Path) -> None:
    """Plural msgids containing newlines are split back apart exactly."""
    content = """msgid "One\\nline"
msgid_plural "Many\\nlines"
msgstr[0] "Eine\\nZeile"
msgstr[1] "Viele\\nZeilen"
"""
    po = _import(tmp_path, _export(tmp_path, content))
    assert po[0].msgid == "One\nline"
    assert po[0].msgid_plural == "Many\nlines"


def test_edited_plural_source_kept_as_plural(tmp_path: Path) -> None:
    """If the visible source cell was edited, it is kept whole as the plural."""
    xlsx_path = _export(tmp_path, MIXED_UNTRANSLATED_PO)
    wb = load_workbook(str(xlsx_path))
    wb.worksheets[0].cell(row=3, column=3).value = "%d documents"
    wb.save(str(xlsx_path))
    wb.close()

    po = _import(tmp_path, xlsx_path)
    entries = {e.msgid: e for e in po}
    assert entries["%d file"].msgid_plural == "%d documents"


def test_full_roundtrip_preserves_every_entry(tmp_path: Path) -> None:
    """Every entry type survives PO -> Excel -> PO unchanged."""
    source = polib.pofile(str(FIXTURES / "entry_types.po"))
    gen = SpreadsheetGenerator(outdir=tmp_path)
    xlsx_path = gen.generate(
        filename="test_{lang}.xlsx", context=build_context(FIXTURES / "entry_types.po")
    )
    result = _import(tmp_path, xlsx_path)
    assert [entry_key(e) for e in result] == [entry_key(e) for e in source]


# Exported with pox-convert 1.1.0 from fixtures/entry_types.po: no hatching on
# singular rows and no hidden singular-msgid column.
LEGACY_XLSX = FIXTURES / "legacy_v1.1.0.xlsx"


def test_legacy_sheet_entry_types(tmp_path: Path) -> None:
    """Old sheets import singular rows as singular and plural rows as plural."""
    po = _import(tmp_path, LEGACY_XLSX)
    plural = {e.msgid for e in po if e.msgid_plural}
    singular = {e.msgid for e in po if not e.msgid_plural}
    assert plural == {"%d files", "%d items", "%d folders", "%d olds"}
    assert singular == {"Hello", "Goodbye", "Open", "Thanks", "Gone"}


def test_legacy_sheet_translations(tmp_path: Path) -> None:
    """Old sheets keep every translation, context, and obsolete flag."""
    po = _import(tmp_path, LEGACY_XLSX)
    entries = {e.msgid: e for e in po}

    # Translated, untranslated, and partially translated plurals
    assert entries["%d files"].msgstr_plural == {0: "%d Datei", 1: "%d Dateien"}
    assert entries["%d items"].msgstr_plural == {0: "", 1: ""}
    assert entries["%d folders"].msgstr_plural == {0: "%d Ordner", 1: ""}

    # Old sheets only carry the plural msgid, so it is used for both
    assert entries["%d files"].msgid_plural == "%d files"

    assert entries["Hello"].msgstr == "Hallo"
    assert entries["Goodbye"].msgstr == ""
    assert entries["Open"].msgstr == "Offen"
    assert entries["Open"].msgctxt == "adjective"

    assert entries["%d olds"].obsolete
    assert entries["%d olds"].msgstr_plural == {0: "%d alt", 1: "%d alte"}
    assert entries["Gone"].obsolete
    assert entries["Gone"].msgstr == "Weg"


def test_hatched_cell_with_text_stays_singular(tmp_path: Path) -> None:
    """Text typed into a hatched cell doesn't turn a singular row into a plural."""
    xlsx_path = _export(tmp_path, MIXED_UNTRANSLATED_PO)
    wb = load_workbook(str(xlsx_path))
    ws = wb.worksheets[0]
    hello_row = next(r for r in ws.iter_rows(min_row=2) if r[2].value == "Hello")
    hello_row[4].value = "oops"
    wb.save(str(xlsx_path))
    wb.close()

    po = _import(tmp_path, xlsx_path)
    entries = {e.msgid: e for e in po}
    assert entries["Hello"].msgstr == "Hallo"
    assert not entries["Hello"].msgid_plural


@pytest.mark.parametrize(
    ("msgid", "msgstr"),
    [
        pytest.param("  padded  ", "  gepolstert  ", id="surrounding-spaces"),
        pytest.param("Tab\there", "Tab\thier", id="tab"),
        pytest.param("Line\n", "Zeile\n", id="trailing-newline"),
        pytest.param("One\nTwo", "Eins\nZwei", id="inner-newline"),
        pytest.param(
            '<b>Fish & Chips</b> 100% "quoted"',
            '<b>Fisch & Pommes</b> 100% "zitiert"',
            id="markup-and-quotes",
        ),
        pytest.param("%(count)s items", "%(count)s Dinge", id="format-placeholder"),
        pytest.param("Party 🎉", "Feier 🎉", id="emoji"),
        pytest.param("Hello", "שלום", id="rtl"),
        pytest.param("+49 phone", "-minus", id="leading-plus-minus"),
        pytest.param("x" * 5000, "y" * 5000, id="long-text"),
    ],
)
def test_text_survives_roundtrip(tmp_path: Path, msgid: str, msgstr: str) -> None:
    """Translations come back from the spreadsheet exactly as they went in."""
    po = polib.POFile()
    po.metadata = {"Language": "de"}
    po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
    po.save(str(tmp_path / "input.po"))

    gen = SpreadsheetGenerator(outdir=tmp_path)
    xlsx_path = gen.generate(
        filename="test_{lang}.xlsx", context=build_context(tmp_path / "input.po")
    )
    result = _import(tmp_path, xlsx_path)
    assert [(e.msgid, e.msgstr) for e in result] == [(msgid, msgstr)]


def test_header_only_sheet_fails_cleanly(tmp_path: Path) -> None:
    """A sheet with a header but no entries fails with an error, not a traceback."""
    xlsx_path = tmp_path / "header_only.xlsx"
    wb = Workbook()
    ws = wb.worksheets[0]
    ws.title = "Translations (de)"
    ws.append(["id", "Context", "Source Language", "Translation"])
    wb.save(str(xlsx_path))
    wb.close()

    with pytest.raises(ConverterError, match="Not enough rows"):
        _import(tmp_path, xlsx_path)


def test_several_spreadsheets_in_one_run(tmp_path: Path) -> None:
    """Each spreadsheet given to the import produces its own PO file."""
    gen = SpreadsheetGenerator(outdir=tmp_path)
    paths = [
        str(gen.generate(filename="t_{lang}.xlsx", context=build_context(FIXTURES / f)))
        for f in ("singular.po", "plurals_polish.po")
    ]
    opts = argparse.Namespace(xlsx_file=paths, outdir=tmp_path, filename="{lang}.po")
    Excel2PoConverter(options=opts).run()
    assert polib.pofile(str(tmp_path / "de.po")).find("Hello").msgstr == "Hallo"
    assert polib.pofile(str(tmp_path / "pl.po")).metadata["Language"] == "pl"


# --- Known bugs, kept as strict xfails until they are fixed ---


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(42, "42", id="int"),
        pytest.param(3.5, "3.5", id="float"),
        pytest.param(42.0, "42", id="whole-float"),
    ],
)
def test_numeric_translation_cell_imports_as_text(
    tmp_path: Path, value: float, expected: str
) -> None:
    """A translation Excel stored as a number is imported as its text."""
    xlsx_path = _export(tmp_path, 'msgid "Answer"\nmsgstr ""\n')
    wb = load_workbook(str(xlsx_path))
    wb.worksheets[0].cell(row=2, column=4).value = value
    wb.save(str(xlsx_path))
    wb.close()

    po = _import(tmp_path, xlsx_path)
    assert po.find("Answer").msgstr == expected


def test_numeric_plural_cell_imports_as_text(tmp_path: Path) -> None:
    """A plural form Excel stored as a number is imported as its text."""
    xlsx_path = _export(
        tmp_path, 'msgid "%d"\nmsgid_plural "%d"\nmsgstr[0] ""\nmsgstr[1] ""\n'
    )
    wb = load_workbook(str(xlsx_path))
    wb.worksheets[0].cell(row=2, column=5).value = 7
    wb.save(str(xlsx_path))
    wb.close()

    po = _import(tmp_path, xlsx_path)
    assert po[0].msgstr_plural == {0: "", 1: "7"}


@pytest.mark.xfail(
    strict=True,
    reason="Bug: text starting with '=' is written as an Excel formula, so it "
    "imports as empty and adds a second header entry.",
)
def test_text_starting_with_equals_survives_roundtrip(tmp_path: Path) -> None:
    """Source and translation starting with '=' are kept as text."""
    xlsx_path = _export(
        tmp_path, 'msgid "=== Section ==="\nmsgstr "=== Abschnitt ==="\n'
    )
    po = _import(tmp_path, xlsx_path)
    assert [(e.msgid, e.msgstr) for e in po] == [
        ("=== Section ===", "=== Abschnitt ===")
    ]


@pytest.mark.xfail(
    strict=True,
    reason="Bug: obsolete entries are exported with 'obsolete' in place of "
    "their context, so the context is lost.",
)
def test_obsolete_entry_keeps_context(tmp_path: Path) -> None:
    """An obsolete entry's msgctxt survives the roundtrip."""
    xlsx_path = _export(
        tmp_path, '#~ msgctxt "verb"\n#~ msgid "Run"\n#~ msgstr "Laufen"\n'
    )
    po = _import(tmp_path, xlsx_path)
    assert po[0].obsolete
    assert po[0].msgctxt == "verb"


@pytest.mark.xfail(
    strict=True,
    reason="Bug: a live entry whose context is literally 'obsolete' is "
    "imported as an obsolete entry without context.",
)
def test_context_named_obsolete_is_not_an_obsolete_entry(tmp_path: Path) -> None:
    """The context value 'obsolete' doesn't mark an entry as obsolete."""
    xlsx_path = _export(tmp_path, 'msgctxt "obsolete"\nmsgid "Old"\nmsgstr "Alt"\n')
    po = _import(tmp_path, xlsx_path)
    assert not po[0].obsolete
    assert po[0].msgctxt == "obsolete"


@pytest.mark.xfail(
    strict=True,
    reason="Bug: the import doesn't restore Plural-Forms, so msgfmt --check "
    "fails and gettext falls back to the two-form rule.",
)
def test_plural_forms_header_survives_roundtrip(tmp_path: Path) -> None:
    """The Plural-Forms header comes back from the spreadsheet."""
    source = polib.pofile(str(FIXTURES / "plurals_polish.po"))
    gen = SpreadsheetGenerator(outdir=tmp_path)
    xlsx_path = gen.generate(
        filename="test_{lang}.xlsx",
        context=build_context(FIXTURES / "plurals_polish.po"),
    )
    opts = argparse.Namespace(
        xlsx_file=[str(xlsx_path)], outdir=tmp_path, filename="{lang}.po"
    )
    Excel2PoConverter(options=opts).run()
    result = polib.pofile(str(tmp_path / "pl.po"))
    assert result.metadata.get("Plural-Forms") == source.metadata["Plural-Forms"]
