"""
po File Plural Form Mapping.

This list contains the plural forms for languages with more than 2 forms (i.e. more
than singular and plural). In a spreadsheet, those forms are separated into multiple
rows and have the plural hint next to it, to indicate which plural form the editor
should translate.

Those indications are programmatically generated using a safe plural formula parser.

See https://www.gnu.org/software/gettext/manual/html_node/Plural-forms.html
"""

import re

from pox.plural_parser import group

RE_PLURAL_COUNT = re.compile(r"nplurals=(?P<num>\d+);")

MAX_RANGE_PARTS = 2


def _format_values(values: list[int], has_more: bool) -> str:
    """Collapse consecutive integers into range notation: [1,2,3,5] → '1-3, 5'."""
    if not values:
        return ""
    parts: list[str] = []
    start = prev = values[0]
    for v in values[1:]:
        if v == prev + 1:
            prev = v
        else:
            parts.append(str(start) if start == prev else f"{start}-{prev}")
            start = prev = v
    parts.append(str(start) if start == prev else f"{start}-{prev}")
    truncated = len(parts) > MAX_RANGE_PARTS or has_more
    result = ", ".join(parts[:MAX_RANGE_PARTS])
    if truncated:
        result += ", ..."
    return result


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

    try:
        hints = {}
        for g in group(plural_form, per_group=1000):
            formatted = _format_values(g["values"], g["has_more"])
            is_singular = 1 in g["values"]
            label = "Singular" if is_singular else "Plural"
            hints[g["group"]] = f"{label}, n = {formatted}"
    except (ValueError, TypeError, KeyError):
        num = int(match.groupdict()["num"])
        return {i: f"Plural Form {i + 1}" for i in range(num)}
    else:
        return hints
