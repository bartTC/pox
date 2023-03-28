from django.core.management.commands import makemessages


class Command(makemessages.Command):
    """
    Like Django's `makemessages` but this one explicitly avoids fuzzy matches.
    """

    msgmerge_options = makemessages.Command.msgmerge_options + ["--no-fuzzy-matching"]
