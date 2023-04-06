"""
Convert PO to Excel files
"""
import argparse
import asyncio
import glob
import sys
from datetime import UTC, datetime
from pathlib import Path

import polib

from ..base import ArgumentFormatter, BaseConverter
from ..datastructures import (
    Message,
    PluralTranslation,
    SingularTranslation,
    SpreadsheetContext,
)
from ..plurals import get_plural_hints
from ..spreadsheet import SpreadsheetGenerator
from ..utils import dedent
from ..warnings import ConversionError as E
from ..warnings import ConversionErrorDescription as D


class Po2ExcelConverter(BaseConverter):
    options: argparse.Namespace
    po_files: list[Path] = []
    warning_descriptions: list[D] = []

    def __init__(self, options: argparse.Namespace):
        """
        Create a new instance of the .po to Excel converter and do some preflight
        checks, that argparse couldn't catch yet. We do also gather all .po files
        here.
        """
        self.options = options

        # Make sure, the output directory exists and is a directory
        if options.outdir and (not options.outdir.is_dir()):
            self.fail(E.OUTPUT_DIR_DOES_NOT_EXIST.value.format(outdir=options.outdir))

        # Glob and gather all given po files and check for their existence.
        for po_glob in options.po_file:
            for path in glob.glob(po_glob, recursive=True):
                p = Path(path)
                if p.is_dir():
                    self.warning(message=E.FILE_IS_FOLDER.value.format(p=p))
                    continue
                self.po_files.append(p.resolve())

        # The language can only be used for a single po file, otherwise
        # we'd overwrite them all with the same language.
        if options.language and len(self.po_files) > 1:
            self.fail(E.LANGUAGE_WITH_GLOB)

    async def run(self):
        """
        Convert every po file to spreadsheets.
        """
        async with asyncio.TaskGroup() as tg:
            for path in sorted(self.po_files):
                tg.create_task(self.convert_po_file(path))

        if self.warning_descriptions:
            self.display_messages(self.warning_descriptions)

    async def convert_po_file(self, path: Path) -> None:
        """
        Convert the given po file to a spreadsheet.

        This method collects all translation messages from the given po file and
        re-structures them to a "Message" class which is passed to the spreadsheet.
        """
        try:
            pofile = polib.pofile(str(path))
        except UnicodeDecodeError:
            # Can't read the file, probably a binary and not a .po file.
            self.warning(E.FILE_UNREADABLE.value.format(p=path))
            self.warning_descriptions.append(D.DECODE_ERROR)
            return
        except Exception:
            # Any other exception with polib.
            self.warning(E.FILE_UNREADABLE.value.format(p=path))
            return

        # Having a language set is crucial as it determines the filename.
        # If it's not set with --language, it's required to be in the metadata.
        language = self.options.language or pofile.metadata.get("Language")

        if not language:
            self.warning(E.NO_LANGUAGE.value.format(p=path))
            self.warning_descriptions.append(D.MISSING_LANGUAGE)
            return

        # Restructure all polib entries to a defined Message structure
        # we use to convert to a spreadsheet and back.
        messages: list[Message] = []
        item: polib.POEntry

        for item in iter(pofile):
            t: SingularTranslation | PluralTranslation

            # This item has multiple pluralization forms
            if item.msgstr_plural:
                t = PluralTranslation(
                    msgid=item.msgid_plural,
                    msgstr=item.msgstr_plural,
                )
            else:
                t = SingularTranslation(
                    msgid=item.msgid,
                    msgstr=item.msgstr,
                )

            m = Message(
                translation=t,
                context=item.msgctxt,
                comment=item.comment,
                tcomment=item.tcomment,
                obsolete=item.obsolete == 1,
            )

            messages.append(m)

        # Build out a context item with all necessary data to create
        # a spreadsheet.
        context = SpreadsheetContext(
            created=datetime.now(tz=UTC),
            messages=messages,
            language=language,
            plural_form_hints=get_plural_hints(pofile.metadata.get("Plural-Forms")),
        )

        # Convert to a spreadsheet.
        xlsx = SpreadsheetGenerator(outdir=self.options.outdir)
        filename = xlsx.generate(filename=self.options.filename, context=context)

        self.ok(f"Created {filename}")


def main():
    parser = argparse.ArgumentParser(
        prog="pox-convert",
        formatter_class=lambda prog: ArgumentFormatter(prog),
        description="""
            Convert .po files to Excel Spreadsheets. Set one or more .po files:

                %(prog)s path/to/messages.po path/to/other_messages.po

            You may also use globbing:

                %(prog)s locales/**/django.po
            """,
    )
    parser.add_argument(
        nargs="+",
        type=str,
        dest="po_file",
        metavar="PATH_TO_PO_FILE",
        help="Space seperated path to one or more .po files.",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        default=Path("."),
        help="The path to store the generated Excel spreadsheets. Default: .",
    )
    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        default="translations_{lang}.xlsx",
        help=dedent(
            """
            The filename format for the generated spreadsheets. You can use the
            variables `{lang}` and `{date}`. The language is obtained from the .po
            file. The date is the current day in the format YYYY-mm-dd.

            Example: "{lang}_{date}.xlsx" will become "bt_br_2023-05-01.xslx".

            Default: translations_{lang}.xlsx
            """,
        ),
    )
    parser.add_argument(
        "-l",
        "--language",
        type=str,
        required=False,
        help=dedent(
            """
            The "Language" for the given PO file, e.g. "pt_BR". This overrides the
            `"Language"` 'metadata setting. This can only be used with single PO files.

            Default: None
            """,
        ),
    )
    parser.add_argument(
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
    parser.add_argument(
        "--noinput",
        action="store_true",
        default=False,
        help="Do NOT prompt the user for input of any kind.",
    )
    options = parser.parse_args()

    convert = Po2ExcelConverter(options=options)
    asyncio.run(convert.run())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write("\nOK, bye 😢\n")
