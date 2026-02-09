"""Unified CLI entry point with subcommands for pox-convert."""

import argparse
import asyncio
import sys
from pathlib import Path

from pox.base import ArgumentFormatter, ConverterError
from pox.cli.pox_convert import Po2ExcelConverter
from pox.cli.xop_convert import Excel2PoConverter
from pox.utils import dedent


def main() -> None:
    """Run the pox-convert CLI with export/import subcommands."""
    parser = argparse.ArgumentParser(
        prog="pox-convert",
        formatter_class=ArgumentFormatter,
        description="Convert PO files to Excel spreadsheets and back.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- export: PO -> Excel ---
    export_parser = subparsers.add_parser(
        "export",
        formatter_class=ArgumentFormatter,
        help="Convert .po files to Excel spreadsheets.",
        description=dedent(
            """
            Convert .po files to Excel Spreadsheets. Set one or more .po files:

                pox-convert export path/to/messages.po

            You may also use globbing:

                pox-convert export locales/**/django.po
            """,
        ),
    )
    export_parser.add_argument(
        nargs="+",
        type=str,
        dest="po_file",
        metavar="PATH_TO_PO_FILE",
        help="Space separated path to one or more .po files.",
    )
    export_parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        default=Path(),
        help="The path to store the generated Excel spreadsheets. Default: .",
    )
    export_parser.add_argument(
        "-f",
        "--filename",
        type=str,
        default="translations_{lang}.xlsx",
        help=dedent(
            """
            The filename format for the generated spreadsheets. You can use the
            variables `{lang}` and `{date}`. The language is obtained from the .po
            file. The date is the current day in the format YYYY-mm-dd.

            Example: "{lang}_{date}.xlsx" will become "pt_br_2023-05-01.xlsx".

            Default: translations_{lang}.xlsx
            """,
        ),
    )
    export_parser.add_argument(
        "-l",
        "--language",
        type=str,
        required=False,
        help=dedent(
            """
            The "Language" for the given PO file, e.g. "pt_BR". This overrides the
            "Language" metadata setting. This can only be used with single PO files.

            Default: None
            """,
        ),
    )
    export_parser.add_argument(
        "--fuzzy",
        type=str,
        choices=["stop", "ignore", "include"],
        default="stop",
        help=dedent(
            """
            Set how to handle fuzzy strings in po files.

            - stop ...: In case of an occurence, stop. It's intended to remove the
                        fuzzy strings before conversion.
            - ignore .: Ignore and skip all fuzzy string.
            - include : Include fuzzy strings in the spreadsheet.

            Default: stop
            """,
        ),
    )
    export_parser.add_argument(
        "--noinput",
        action="store_true",
        default=False,
        help="Do NOT prompt the user for input of any kind.",
    )

    # --- import: Excel -> PO ---
    import_parser = subparsers.add_parser(
        "import",
        formatter_class=ArgumentFormatter,
        help="Convert Excel spreadsheets back to .po files.",
        description=dedent(
            """
            Convert Excel Spreadsheets back to .po files.

                pox-convert import path/to/translations.xlsx
            """,
        ),
    )
    import_parser.add_argument(
        nargs="+",
        type=str,
        dest="xlsx_file",
        metavar="PATH_TO_XLSX_FILE",
        help="Space separated path to one or more .xlsx files.",
    )
    import_parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        default=Path(),
        help="The path to store the generated .po files. Default: .",
    )
    import_parser.add_argument(
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

    if options.command == "export":
        try:
            convert = Po2ExcelConverter(options=options)
        except ConverterError:
            sys.exit(1)

        try:
            asyncio.run(convert.run())
        except* ConverterError:
            sys.exit(1)

    elif options.command == "import":
        try:
            convert = Excel2PoConverter(options=options)
            convert.run()
        except ConverterError:
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write("\nOK, bye\n")
