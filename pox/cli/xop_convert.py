"""Convert Excel to PO files."""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import polib
from openpyxl import load_workbook

from pox.base import ArgumentFormatter, BaseConverter
from pox.spreadsheet import (
    CONTEXT_HEADER,
    OBSOLETE_HEADER,
    OBSOLETE_MARKER,
    SOURCE_SINGULAR_HEADER,
)
from pox.styles import NOT_APPLICABLE_PATTERN, YELLOW
from pox.utils import dedent


def is_singular_row(cells: tuple, num_translation_cols: int, *, legacy: bool) -> bool:
    """
    Return whether a row in a plural-enabled sheet holds a singular message.

    The export hatches the extra plural columns of singular rows. Any hatched
    cell is enough, so a translator pasting over one of them doesn't turn the
    row into a plural entry.

    Legacy sheets predate the hatching. Their exporter gave plural rows either
    a value in every plural cell or the yellow "empty" fill, so extra cells that
    are all blank and not yellow belong to a singular row.
    """
    extra = cells[4 : 3 + num_translation_cols]
    if any(c.fill.fill_type == NOT_APPLICABLE_PATTERN for c in extra):
        return True
    if not legacy:
        return False
    return all(not c.value for c in extra) and not any(
        c.fill.fgColor.rgb == YELLOW for c in extra
    )


def cell_text(value: object) -> str:
    """
    Return a cell value as the text the translator typed.

    Excel stores input like "42" or "3.5" as a number, but PO entries need
    strings.
    """
    if value is None:
        return ""
    return str(value)


def split_plural_source(source: str, singular: str | None) -> tuple[str, str]:
    r"""
    Return (msgid, msgid_plural) for a plural row.

    The source cell shows "singular\nplural" and the hidden column holds the
    exact singular, so stripping it off yields the plural. If the source cell
    was edited, it is kept whole as the plural. Legacy sheets have no hidden
    column and only ever showed the plural msgid, so it is used for both.
    """
    if not singular:
        return source, source
    return singular, source.removeprefix(f"{singular}\n")


@dataclass(frozen=True)
class SheetLayout:
    """Where each kind of value lives in a translations sheet."""

    # Columns: id, Context, Source Language, Translation, [extra plural cols...]
    num_translation_cols: int
    # Exports before this column existed only carry the plural msgid
    singular_col: int | None
    # Older exports only have the visible Context column, where "obsolete"
    # replaces the context of obsolete entries.
    context_col: int | None
    obsolete_col: int | None
    width: int

    @classmethod
    def from_header(cls, header: list) -> "SheetLayout":
        """Find the columns by their header names."""

        def find(name: str) -> int | None:
            return header.index(name) if name in header else None

        return cls(
            num_translation_cols=sum(
                1 for h in header[3:] if h and str(h).startswith("Translation")
            ),
            singular_col=find(SOURCE_SINGULAR_HEADER),
            context_col=find(CONTEXT_HEADER),
            obsolete_col=find(OBSOLETE_HEADER),
            width=len(header),
        )


def row_to_entry(cells: tuple, layout: SheetLayout) -> polib.POEntry | None:
    """Build a PO entry from a sheet row, or return None for a blank row."""
    row = [cell_text(c.value) for c in cells]
    # Hand-edited sheets can have rows shorter than the header
    row += [""] * (layout.width - len(row))
    if not row[0]:
        return None

    if layout.context_col is not None and layout.obsolete_col is not None:
        context = row[layout.context_col] or None
        obsolete = bool(row[layout.obsolete_col])
    else:
        obsolete = row[1] == OBSOLETE_MARKER
        context = None if obsolete else row[1] or None
    msgid = row[2]

    n = layout.num_translation_cols
    if n > 1 and not is_singular_row(cells, n, legacy=layout.singular_col is None):
        singular = row[layout.singular_col] if layout.singular_col is not None else None
        msgid, msgid_plural = split_plural_source(msgid, singular)
        entry = polib.POEntry(
            msgid=msgid,
            msgid_plural=msgid_plural,
            msgctxt=context,
            obsolete=obsolete,
        )
        entry.msgstr_plural = {pi: row[3 + pi] for pi in range(n)}
        return entry

    return polib.POEntry(
        msgid=msgid,
        msgstr=row[3],
        msgctxt=context,
        obsolete=obsolete,
    )


class Excel2PoConverter(BaseConverter):
    """Convert Excel spreadsheets back to PO files."""

    options: argparse.Namespace

    def __init__(self, options: argparse.Namespace) -> None:
        """Initialize converter and validate output directory."""
        self.options = options

        if options.outdir and not options.outdir.is_dir():
            self.fail(f'The output directory "{options.outdir}" does not exist.')

    def run(self) -> None:
        """Convert all provided xlsx files to PO format."""
        for xlsx_path in self.options.xlsx_file:
            self.convert_xlsx(Path(xlsx_path))

    def convert_xlsx(self, path: Path) -> None:
        """Parse an xlsx file and write a corresponding PO file."""
        wb = load_workbook(str(path), read_only=True, data_only=True)

        # Read custom properties for metadata
        props = {prop.name: prop.value for prop in wb.custom_doc_props}
        language = props.get("Language")

        if not language:
            self.warning(f'No "Language" property found in "{path}". Using filename.')
            language = path.stem.split("_", 1)[-1] if "_" in path.stem else "unknown"

        # Find the translations sheet
        ws = None
        for sheet_name in wb.sheetnames:
            if sheet_name.startswith("Translations"):
                ws = wb[sheet_name]
                break

        if ws is None:
            self.fail(f'No "Translations" sheet found in "{path}".')

        # Parse rows into polib entries
        po = polib.POFile()
        po.metadata = {
            "Content-Type": "text/plain; charset=UTF-8",
            "Language": language,
        }
        # Older exports don't store it; gettext then uses its default rule
        if plural_forms := props.get("PluralForms"):
            po.metadata["Plural-Forms"] = plural_forms

        rows = list(ws.iter_rows())
        if len(rows) < 2:
            self.fail(f'Not enough rows in "{path}".')

        layout = SheetLayout.from_header([c.value for c in rows[0]])
        for cells in rows[1:]:  # Skip header
            entry = row_to_entry(cells, layout)
            if entry is not None:
                po.append(entry)

        wb.close()

        # Write the PO file
        out_filename = self.options.filename.format(lang=language)
        out_path = self.options.outdir / out_filename
        po.save(str(out_path))
        self.ok(f"Created {out_path}")


def main() -> None:  # pragma: no cover - standalone CLI, see pox.cli.main
    """Run the Excel-to-PO CLI command."""
    parser = argparse.ArgumentParser(
        prog="xop-convert",
        formatter_class=ArgumentFormatter,
        description=dedent(
            """
            Convert Excel Spreadsheets back to .po files.

                %(prog)s path/to/translations.xlsx
            """,
        ),
    )
    parser.add_argument(
        nargs="+",
        type=str,
        dest="xlsx_file",
        metavar="PATH_TO_XLSX_FILE",
        help="Space separated path to one or more .xlsx files.",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        default=Path(),
        help="The path to store the generated .po files. Default: .",
    )
    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        default="{lang}.po",
        help=dedent(
            """
            The filename format for the generated .po files. You can use
            the variable `{lang}`.

            Default: {lang}.po
            """,
        ),
    )
    options = parser.parse_args()

    convert = Excel2PoConverter(options=options)
    convert.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write("\nOK, bye \U0001f622\n")
