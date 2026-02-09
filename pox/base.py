"""Base classes for pox converters."""

import argparse
import sys
from enum import Enum
from typing import Any

from .utils import box_message
from .warnings import ConversionError as E

# Width of the help description
ARGPARSE_TERMINAL_WIDTH = 78

# Indention of the help text.
ARGPARSE_HELP_POSITION = 5


class ArgumentFormatter(
    argparse.RawTextHelpFormatter,
):
    """Format argparse help with fixed width and help position."""

    def __init__(self, prog: str, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize formatter with default width and help position."""
        kwargs.setdefault("width", ARGPARSE_TERMINAL_WIDTH)
        kwargs.setdefault("max_help_position", ARGPARSE_HELP_POSITION)
        super().__init__(prog, **kwargs)


class ConverterError(Exception):
    """Raised to abort conversion with an error message."""


class BaseConverter:
    """Provide common logging and error handling for converters."""

    def fail(self, message: str | E, icon: str | None = "❌️") -> None:
        """Print an error message and raise ConverterError."""
        icon = f"{icon} " if icon else ""
        message = message.value if isinstance(message, Enum) else message
        sys.stderr.write(f"{icon}{message}\n")
        sys.stderr.flush()
        raise ConverterError(message)

    def warning(self, message: str | E, icon: str | None = "⚠️") -> None:
        """Print a warning message to stderr."""
        icon = f"{icon} " if icon else ""
        message = message.value if isinstance(message, Enum) else message
        sys.stderr.write(f"{icon}{message}\n")
        sys.stderr.flush()

    def ok(self, message: str | E, icon: str | None = "✅") -> None:
        """Print a success message to stdout."""
        icon = f"{icon} " if icon else ""
        message = message.value if isinstance(message, Enum) else message
        sys.stdout.write(f"{icon}{message}\n")
        sys.stdout.flush()

    def display_messages(self, messages: list[E]) -> None:
        """Display accumulated warning messages."""
        issues = "\n\n".join([box_message(w.value) for w in set(messages)])
        sys.stderr.write(
            f"\n⚠️ There have been issues during the conversion:\n\n{issues}\n",
        )
