from enum import Enum

from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.styles.fills import FILL_SOLID

FONT_FAMILY = "Tahoma"
FONT_SIZE = 14

WHITE = "FFFFFFFF"
BLACK = "FF000000"
LIGHT_GRAY = "FFF2F2F2"
MEDIUM_GRAY = "FFD9D9D9"
DARK_GRAY = "FF595959"
YELLOW = "FFFFFFCC"
RED_BG = "FFCC0000"
OBSOLETE_GRAY = "FFBFBFBF"

DEFAULT_ALIGNMENT = Alignment(
    horizontal="left",
    vertical="center",
    wrap_text=False,
    shrinkToFit=False,
)


class SpreadsheetStyles(Enum):
    """
    The openpyxl cell styles used in the spreadsheet.
    """

    SHEET_HEADLINE = {
        "fill": PatternFill(fill_type=FILL_SOLID, fgColor=RED_BG),
        "font": Font(
            name=FONT_FAMILY,
            size=22,
            bold=True,
            italic=False,
            color=WHITE,
        ),
        "alignment": Alignment(
            horizontal="left",
            vertical="center",
            wrap_text=False,
            shrinkToFit=False,
        ),
    }

    ID = {
        "font": Font(name=FONT_FAMILY, size=FONT_SIZE, color=DARK_GRAY),
        "alignment": DEFAULT_ALIGNMENT,
    }

    HEADER = {
        "fill": PatternFill(fill_type=FILL_SOLID, fgColor=MEDIUM_GRAY),
        "font": Font(name=FONT_FAMILY, size=FONT_SIZE, bold=True, color=BLACK),
        "alignment": DEFAULT_ALIGNMENT,
    }

    HEADER_LIGHT = {
        "fill": PatternFill(fill_type=FILL_SOLID, fgColor=LIGHT_GRAY),
        "font": Font(name=FONT_FAMILY, size=FONT_SIZE, bold=True, color=DARK_GRAY),
        "alignment": DEFAULT_ALIGNMENT,
    }

    FILL_HINT = {
        "font": Font(name=FONT_FAMILY, size=FONT_SIZE, italic=True, color=DARK_GRAY),
        "alignment": DEFAULT_ALIGNMENT,
    }

    CONTEXT = {
        "fill": PatternFill(fill_type=FILL_SOLID, fgColor=LIGHT_GRAY),
        "font": Font(name=FONT_FAMILY, size=FONT_SIZE, italic=True, color=DARK_GRAY),
        "alignment": DEFAULT_ALIGNMENT,
    }

    MSG_ID = {
        "font": Font(name=FONT_FAMILY, size=FONT_SIZE, color=BLACK),
        "alignment": DEFAULT_ALIGNMENT,
    }

    MSG_STR = {
        "font": Font(name=FONT_FAMILY, size=FONT_SIZE, color=BLACK),
        "alignment": Alignment(
            horizontal="left",
            vertical="center",
            wrap_text=True,
            shrinkToFit=False,
        ),
    }

    MSG_STR_EMPTY = {
        "fill": PatternFill(fill_type=FILL_SOLID, fgColor=YELLOW),
        "font": Font(name=FONT_FAMILY, size=FONT_SIZE, color=BLACK),
        "alignment": DEFAULT_ALIGNMENT,
    }

    MSG_STR_OBSOLETE = {
        "font": Font(
            name=FONT_FAMILY,
            size=FONT_SIZE,
            italic=True,
            color=OBSOLETE_GRAY,
        ),
        "alignment": DEFAULT_ALIGNMENT,
    }
