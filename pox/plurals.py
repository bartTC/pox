"""
po File Plural Form Mapping.

This list contains the plural forms for languages with more than 2 forms (i.e. more
than singular and plural). In a spreadsheet, those forms are separated into multiple
rows and have the plural hint next to it, to indicate which plural form the editor
should translate.

OPTIMIZE: Those indications can likely be programmatically generated, however it likely
would require executing arbitrary code from a po file.

See https://www.gnu.org/software/gettext/manual/html_node/Plural-forms.html
"""

import re

RE_PLURAL_COUNT = re.compile(r"nplurals=(?P<num>\d+);")


def get_plural_hints(plural_form: str | None) -> dict[int, str] | None:
    """
    Try to get the po file's plural form mapping from above dictionary.

    Remove all whitespace and linebreaks from the key's as well as the given
    po form string, to avoid match errors due to those minor differences.
    """
    default_form = {
        0: "Singular",
        1: "Plural",
    }

    # Pofile contains no plural form, assume that we have a
    # simple Singular/Plural variant.
    if not plural_form:
        return default_form

    match = RE_PLURAL_COUNT.search(plural_form)

    # There is a plural form set, but it does not say the actual count of
    # forms. Probably broken.
    if not match:
        return default_form

    # For now, generate a list of Plural forms.
    # @TODO: Generate a better list in the format "n = 0, 1, 2 ..."
    num = int(match.groupdict()["num"])
    return {i: f"Plural Form {i + 1}" for i in range(num)}
