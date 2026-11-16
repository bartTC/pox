"""Data structures for pox translations."""

from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property


@dataclass(frozen=True)
class SingularTranslation:
    """Represent a singular translation entry."""

    msgid: str
    msgstr: str


@dataclass(frozen=True)
class PluralTranslation:
    """Represent a plural translation entry."""

    msgid: str
    msgid_plural: str
    msgstr: dict[int, str]


@dataclass(frozen=True)
class Message:
    """Represent a single translatable message."""

    translation: SingularTranslation | PluralTranslation
    context: str | None
    comment: str | None  # Code comment
    tcomment: str | None  # Translator comment
    obsolete: bool
    occurrences: tuple[tuple[str, str], ...] = ()  # (file, line) of "#:" lines
    flags: tuple[str, ...] = ()  # "#," flags, without "fuzzy"

    @cached_property
    def is_plural(self) -> bool:
        """Return whether this message has plural forms."""
        return isinstance(self.translation, PluralTranslation)


@dataclass
class SpreadsheetContext:
    """Hold context data for spreadsheet generation."""

    language: str
    messages: list[Message]
    created: datetime
    plural_form_hints: dict[int, str] | None
    # The PO file's header fields, stored so the import can restore them
    metadata: dict[str, str] = field(default_factory=dict)
