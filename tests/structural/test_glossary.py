# SPDX-License-Identifier: GPL-2.0-or-later
"""The translations use the glossary's terms (specs/18 criterion 4; FR-093).

``specs/00-glossary.md`` is normative for translators, and until P12c nothing
held a translation to it. The first run of :mod:`scripts.check_glossary` found
61 Portuguese and 67 Spanish strings that departed from it. The largest group
was the levelling strings, which rendered *setup* as *estação*/*estación*. The
glossary keeps that word for *station*, so a levelling dialog called a mark and
an instrument position by the same name. The total-station strings had always
said *estacionamento*.
"""

from __future__ import annotations

import pytest

from scripts.check_glossary import (
    GLOSSARY,
    LANGUAGES,
    NOT_CHECKED,
    PAIRED,
    departures,
    terms,
    uses,
)


@pytest.mark.parametrize("locale", LANGUAGES)
def test_every_translation_uses_the_glossary(locale):
    found = departures(locale)
    assert not found, f"{len(found)} departures; run scripts/check_glossary.py {locale}:\n" + (
        "\n".join(f"[{d.context}] {d.term!r}: {d.translation[:80]!r}" for d in found[:20])
    )


def test_the_glossary_is_read():
    """Guards the parser: a glossary read as empty would pass every check."""
    found = terms()
    english = {term.english for term in found}
    assert len(found) > 80
    assert {"Setup", "Station", "Datum defect", "Resection", "fixed solution"} <= english
    assert all(term.renderings["pt_BR"] and term.renderings["es"] for term in found)


def test_the_exceptions_are_glossary_terms_with_reasons():
    text = GLOSSARY.read_text(encoding="utf-8")
    for term, reason in NOT_CHECKED.items():
        assert f"| {term} |" in text or f"/ {term} |" in text, term
        assert len(reason) > 20, term
    for row in PAIRED:
        assert f"| {row} |" in text, row


@pytest.mark.parametrize(
    ("rendering", "translation", "expected"),
    [
        ("Estação", "Estações ajustadas", True),
        ("Elipse de erro", "As elipses de erro", True),
        ("Deficiência de datum", "Deficiência de datum: 3", True),
        ("Estacionamento", "Maior desequilíbrio por estação", False),
        ("Interseção à ré", "Interseção inversa", False),
        ("Altura de la señal", "altura de la senal", True),
    ],
)
def test_the_match_allows_inflection_not_another_word(rendering, translation, expected):
    assert uses(rendering, translation) is expected
