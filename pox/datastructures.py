from dataclasses import dataclass
from datetime import datetime
from functools import cached_property


@dataclass(frozen=True)
class SingularTranslation:
    msgid: str
    msgstr: str


@dataclass(frozen=True)
class PluralTranslation:
    msgid: str
    msgstr: dict[int, str]


@dataclass(frozen=True)
class Message:
    translation: SingularTranslation | PluralTranslation
    context: str | None
    comment: str | None  # Code comment
    tcomment: str | None  # Translator comment
    obsolete: bool

    @cached_property
    def is_plural(self):
        return isinstance(self.translation, PluralTranslation)


@dataclass
class SpreadsheetContext:
    language: str
    messages: list[Message]
    created: datetime
    plural_form_hints: dict[int, str] | None
