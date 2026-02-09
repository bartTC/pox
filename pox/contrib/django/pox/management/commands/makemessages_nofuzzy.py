"""Django management command to make messages without fuzzy matching."""

from typing import ClassVar

from django.core.management.commands import makemessages


class Command(makemessages.Command):
    """Like Django's `makemessages` but this one explicitly avoids fuzzy matches."""

    msgmerge_options: ClassVar[list[str]] = [
        *makemessages.Command.msgmerge_options,
        "--no-fuzzy-matching",
    ]
