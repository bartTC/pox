from pathlib import Path
from typing import Any

from openpyxl.packaging.custom import StringProperty
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from . import __version__
from .datastructures import Message, SpreadsheetContext
from .styles import SpreadsheetStyles as S


class SpreadsheetGenerator:
    outdir: Path

    def __init__(self, outdir: Path):
        self.outdir = outdir

    def get_tabledata(
        self,
        messages: list[Message],
    ) -> list[Any]:
        """
        Generate a Matrix array of messages for a table:

        id  Context     Singular Form   Translation
         1              Hello World     Hallo Welt
         2  Keep short  Sausage         Wurst
         3  obsolete    ~~Nudel~~       ~~Noodle~~

        And attach a format to each cell.
        """
        # The number of plural forms define the overall columns. Plural forms 0
        # would mean we have only singular, but `plural forms 1` would also do,
        # since the first plural form is the singular form.
        #
        # id | singular | translation | space | plural |  plural translation * n
        # ^    ^          form idx 0    ^       ^         form idx 1+
        fill_out_above = [
            ("", None),
            ("", None),
            ("", None),
            ("Please fill out the yellow fields ⤵️", S.FILL_HINT),
        ]

        fill_out_below = [
            ("", None),
            ("", None),
            ("", None),
            ("Please fill out the yellow fields ⤴", S.FILL_HINT),
        ]

        header = [
            ("id", S.HEADER_LIGHT),
            ("Context", S.HEADER),
            ("Singular Form", S.HEADER),
            ("Translation", S.HEADER),
        ]

        data = []
        for i, m in enumerate(messages):
            msg_str_style = S.MSG_STR
            if m.obsolete:
                msg_str_style = S.MSG_STR_OBSOLETE
            elif m.translation.msgstr == "":
                msg_str_style = S.MSG_STR_EMPTY

            if m.is_plural:
                pass

            else:
                data.append(
                    (
                        (i + 1, S.ID),
                        ("obsolete" if m.obsolete else m.context, S.CONTEXT),
                        (m.translation.msgid, S.MSG_ID),
                        (m.translation.msgstr, msg_str_style),
                    ),
                )

        return [
            fill_out_above,
            header,
            *data,
            fill_out_below,
        ]

    def generate(self, filename: str, context: SpreadsheetContext) -> Path:
        """
        Generates the
        """
        wb = Workbook()

        # Attach the language as a custom property
        props = [
            StringProperty(name="Language", value=context.language),
            StringProperty(name="PoxConvert", value=__version__),
        ]

        for p in props:
            wb.custom_doc_props.append(p)

        # Delete the auto generated "Sheet" worksheet
        wb.remove_sheet(wb.worksheets[0])

        # Create two sheets, "Translations" to hold the actual translations
        # and "Metadata" to store some extra data not needed for translation,
        # but might be useful upon parsing.
        ws: Worksheet = wb.create_sheet(f"Translations ({context.language})", index=0)
        wm: Worksheet = wb.create_sheet("Metadata", index=1)

        # Remove all gridlines right away
        ws.sheet_view.showGridLines = False
        wm.sheet_view.showGridLines = False

        # Generate the main spreadsheet for singular translations
        data = self.get_tabledata(
            messages=context.messages,
        )

        for row in data:
            ws.append([i[0] for i in row])

        # Write out the Excel spreadsheet and return its generated filename.
        fn_path = self.outdir / filename.format(
            lang=context.language,
            date=context.created.strftime("%Y-%m-%d"),
        )
        wb.save(fn_path)
        return fn_path
