from datetime import UTC, datetime
from pathlib import Path

import polib
import pytest

from pox.datastructures import (
    Message,
    PluralTranslation,
    SingularTranslation,
    SpreadsheetContext,
)
from pox.plurals import get_plural_hints
from pox.spreadsheet import SpreadsheetGenerator

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def singular_po():
    return FIXTURES / "singular.po"


@pytest.fixture
def plurals_po():
    return FIXTURES / "plurals.po"


@pytest.fixture
def fuzzy_po():
    return FIXTURES / "fuzzy.po"


@pytest.fixture
def obsolete_po():
    return FIXTURES / "obsolete.po"


@pytest.fixture
def no_language_po():
    return FIXTURES / "no_language.po"


def build_context(po_path: Path) -> SpreadsheetContext:
    """Build a SpreadsheetContext from a PO file, mimicking pox_convert logic."""
    pofile = polib.pofile(str(po_path))
    messages = []

    for item in pofile:
        if item.msgstr_plural:
            t = PluralTranslation(
                msgid=item.msgid_plural,
                msgstr=item.msgstr_plural,
            )
        else:
            t = SingularTranslation(
                msgid=item.msgid,
                msgstr=item.msgstr,
            )

        messages.append(
            Message(
                translation=t,
                context=item.msgctxt,
                comment=item.comment,
                tcomment=item.tcomment,
                obsolete=item.obsolete == 1,
            ),
        )

    return SpreadsheetContext(
        created=datetime.now(tz=UTC),
        messages=messages,
        language=pofile.metadata.get("Language", "en"),
        plural_form_hints=get_plural_hints(pofile.metadata.get("Plural-Forms")),
    )


@pytest.fixture
def plurals_polish_po():
    return FIXTURES / "plurals_polish.po"


@pytest.fixture
def mixed_empty_po():
    return FIXTURES / "mixed_empty.po"


@pytest.fixture
def singular_xlsx(tmp_path, singular_po):
    """Generate an xlsx from the singular PO fixture."""
    context = build_context(singular_po)
    gen = SpreadsheetGenerator(outdir=tmp_path)
    return gen.generate(filename="test_{lang}.xlsx", context=context)


@pytest.fixture
def plurals_xlsx(tmp_path, plurals_po):
    """Generate an xlsx from the plurals PO fixture."""
    context = build_context(plurals_po)
    gen = SpreadsheetGenerator(outdir=tmp_path)
    return gen.generate(filename="test_{lang}.xlsx", context=context)
