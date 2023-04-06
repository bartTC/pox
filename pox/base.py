import argparse
import sys
from enum import Enum

from .utils import box_message
from .warnings import ConversionError as E
from .warnings import ConversionErrorDescription as ED

# Width of the help description
ARGPARSE_TERMINAL_WIDTH = 78

# Indention of the help text.
ARGPARSE_HELP_POSITION = 5


class ArgumentFormatter(
    argparse.RawTextHelpFormatter,
):
    def __init__(self, prog: str, **kwargs):
        kwargs.setdefault("width", ARGPARSE_TERMINAL_WIDTH)
        kwargs.setdefault("max_help_position", ARGPARSE_HELP_POSITION)
        super().__init__(prog, **kwargs)


class BaseConverter:
    def fail(self, message: str | E, icon: str | None = "❌️") -> None:
        icon = f"{icon} " if icon else ""
        message = message.value if isinstance(message, Enum) else message
        sys.stderr.write(f"{icon}{message}\n")
        sys.stderr.flush()
        sys.exit(1)

    def warning(self, message: str | E, icon: str | None = "⚠️") -> None:
        icon = f"{icon} " if icon else ""
        message = message.value if isinstance(message, Enum) else message
        sys.stderr.write(f"{icon}{message}\n")
        sys.stderr.flush()

    def ok(self, message: str | E, icon: str | None = "✅") -> None:
        icon = f"{icon} " if icon else ""
        message = message.value if isinstance(message, Enum) else message
        sys.stdout.write(f"{icon}{message}\n")
        sys.stdout.flush()

    def display_messages(self, messages: list[ED]) -> None:
        issues = "\n\n".join([box_message(w.value) for w in set(messages)])
        sys.stderr.write(
            f"\n⚠️ There have been issues during the conversion:\n\n{issues}\n",
        )
