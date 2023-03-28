from enum import Enum, auto

from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.styles.fills import FILL_SOLID

FONT_FAMILY = "Tahoma"
FONT_SIZE = 14

WHITE = "FFFFFFFF"


class SpreadsheetStyles(Enum):
    """
    The openpyxl cell styles used in the spreadsheet.
    """

    # The overall headline
    SHEET_HEADLINE = {
        "fill": PatternFill(
            fill_type=FILL_SOLID,
            bgColor="CC0000",
        ),
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

    ID = auto()

    # The translation table header
    HEADER = auto()

    # Same, but slightly light
    HEADER_LIGHT = auto()

    # The "Please fill out" indicator
    FILL_HINT = auto()

    # The context field
    CONTEXT = auto()

    # THe message id (original field)
    MSG_ID = auto()

    # A filled translation field
    MSG_STR = auto()

    # A to be filled translation field
    MSG_STR_EMPTY = auto()

    # An obsolete translation
    MSG_STR_OBSOLETE = auto()
