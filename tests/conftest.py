"""Shared fixtures and helpers for pox tests."""

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
def singular_po() -> Path:
    """Return path to the singular PO fixture."""
    return FIXTURES / "singular.po"


@pytest.fixture
def plurals_po() -> Path:
    """Return path to the plurals PO fixture."""
    return FIXTURES / "plurals.po"


@pytest.fixture
def fuzzy_po() -> Path:
    """Return path to the fuzzy PO fixture."""
    return FIXTURES / "fuzzy.po"


@pytest.fixture
def obsolete_po() -> Path:
    """Return path to the obsolete PO fixture."""
    return FIXTURES / "obsolete.po"


@pytest.fixture
def no_language_po() -> Path:
    """Return path to the no-language PO fixture."""
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
def plurals_polish_po() -> Path:
    """Return path to the Polish plurals PO fixture."""
    return FIXTURES / "plurals_polish.po"


@pytest.fixture
def mixed_empty_po() -> Path:
    """Return path to the mixed-empty PO fixture."""
    return FIXTURES / "mixed_empty.po"


def _generate_xlsx(tmp_path: Path, po_path: Path) -> Path:
    """Generate an xlsx from a PO fixture file."""
    context = build_context(po_path)
    gen = SpreadsheetGenerator(outdir=tmp_path)
    return gen.generate(filename="test_{lang}.xlsx", context=context)


@pytest.fixture
def singular_xlsx(tmp_path: Path, singular_po: Path) -> Path:
    """Generate an xlsx from the singular PO fixture."""
    return _generate_xlsx(tmp_path, singular_po)


@pytest.fixture
def plurals_xlsx(tmp_path: Path, plurals_po: Path) -> Path:
    """Generate an xlsx from the plurals PO fixture."""
    return _generate_xlsx(tmp_path, plurals_po)


@pytest.fixture
def no_language_xlsx(tmp_path: Path, no_language_po: Path) -> Path:
    """Generate an xlsx from the no-language PO fixture."""
    return _generate_xlsx(tmp_path, no_language_po)
