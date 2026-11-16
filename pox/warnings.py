"""Warning and error enumerations for pox conversions."""

import enum

from .utils import dedent


class ConversionError(enum.Enum):
    """Error messages for conversion failures."""

    LANGUAGE_WITH_GLOB = (
        'The "language" argument can only be used with a single po file.'
    )
    FILE_UNREADABLE = 'The po file "{p}" is unreadable.'
    FILE_IS_FOLDER = 'The po file "{p}" is a folder. Only set .po files.'
    NO_MATCH = 'No files match "{p}".'
    NO_PO_FILES = "No po files found."
    SAME_OUTPUT = (
        'Skipped "{p}": "{other}" already writes "{out}". '
        "Use {{lang}} in the filename, or check the Language headers."
    )
    OUTPUT_DIR_DOES_NOT_EXIST = 'The  output directory "{outdir}" does not exist '
    NO_LANGUAGE = 'The po file "{p}" has no "Language" set in it\'s metadata.'


class ConversionErrorDescription(enum.Enum):
    """Detailed descriptions for conversion errors."""

    DECODE_ERROR = dedent(
        """
        The po file is unreadable.

        The given file is not readable or not a .po file. Please make sure the
        file exists and you have read permission.
        """,
    )

    MISSING_LANGUAGE = dedent(
        """
        File has no "Language" set in it's metadata:

        When converting multiple .po files, it's required that each file has
        a "Language" set in it's metadata. This example has the language
        "pt_BR" (Portuguese/Brazilian) set:

          "Project-Id-Version: PACKAGE VERSION\\n"
          "Language-Team: LANGUAGE <LL@li.org>\\n"
          "Language: pt_BR\\n"

        See https://www.gnu.org/software/gettext/manual/html_node/Header-Entry.html.

        You can bypass this by providing a `--language` argument, however
        this works only for single po files:

          pox-convert export path/to/messages.po --language=pt_BR
        """,
    )
