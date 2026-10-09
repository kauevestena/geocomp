# SPDX-License-Identifier: GPL-2.0-or-later
"""FR-090: the plugin must be *completely* available in all three languages.

``specs/18-i18n-and-profiles.md`` section 1: partial translation is worse than
none -- a dialog half in Spanish and half in English is harder to use than one
consistently in either. So completeness is a test, not an aspiration.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from scripts.translations import (
    TARGET_LOCALES,
    catalogue_path,
    completeness,
    extract_sources,
    read_catalogue,
)


@pytest.fixture(scope="module")
def sources():
    return extract_sources()


def test_sources_are_extracted(sources):
    """Guards the extractor: if it silently found nothing, every other
    assertion in this module would pass vacuously."""
    total = sum(len(entries) for entries in sources.values())
    assert total > 50, f"only {total} source strings extracted; the extractor is probably broken"


@pytest.mark.parametrize("locale", TARGET_LOCALES)
def test_catalogue_exists_and_is_valid_xml(locale):
    path = catalogue_path(locale)
    assert path.exists(), f"missing catalogue for {locale}"
    root = ET.parse(path).getroot()
    assert root.tag == "TS"
    assert root.get("language") == locale


@pytest.mark.parametrize("locale", TARGET_LOCALES)
def test_every_source_string_is_translated(locale, sources):
    catalogue = read_catalogue(catalogue_path(locale))
    untranslated: list[str] = []
    for context, strings in sources.items():
        entries = catalogue.get(context, {})
        for source in strings:
            if not entries.get(source):
                untranslated.append(f"[{context}] {source[:70]!r}")

    assert not untranslated, (
        f"{locale} is missing {len(untranslated)} translation(s). "
        "Run: python3 scripts/update_translations.py\n" + "\n".join(untranslated)
    )


@pytest.mark.parametrize("locale", TARGET_LOCALES)
def test_catalogue_has_no_stale_entries(locale, sources):
    """A translation for a string the code no longer contains makes the
    completeness figure lie."""
    catalogue = read_catalogue(catalogue_path(locale))
    stale = [
        f"[{context}] {source[:70]!r}"
        for context, entries in catalogue.items()
        for source in entries
        if source not in sources.get(context, set())
    ]
    assert not stale, "Stale catalogue entries:\n" + "\n".join(stale)


@pytest.mark.parametrize("locale", TARGET_LOCALES)
def test_catalogue_reports_complete(locale):
    translated, total = completeness(read_catalogue(catalogue_path(locale)))
    assert translated == total, f"{locale}: {translated}/{total}"


@pytest.mark.parametrize("locale", TARGET_LOCALES)
def test_placeholders_survive_translation(locale, sources):
    """A translation that drops a %1 loses the value the message was about,
    and one that invents a %4 renders a literal '%4' to the user."""
    catalogue = read_catalogue(catalogue_path(locale))
    problems: list[str] = []
    for context, entries in catalogue.items():
        for source, translation in entries.items():
            if not translation:
                continue
            expected = {token for token in ("%1", "%2", "%3", "%4") if token in source}
            actual = {token for token in ("%1", "%2", "%3", "%4") if token in translation}
            if expected != actual:
                problems.append(
                    f"[{context}] {source[:50]!r}: expected {sorted(expected)}, got {sorted(actual)}"
                )
    assert not problems, "Placeholder mismatch:\n" + "\n".join(problems)


@pytest.mark.parametrize("locale", TARGET_LOCALES)
def test_a_label_a_message_quotes_is_the_label_shown(locale):
    """A message that names a control by its label sends the reader looking for those words.

    Found in P13-6, translating the levelling walkthrough: the network's refusal
    told a Portuguese reader to turn on 'Ajustar linhas que falharam na
    tolerância' in the run or in Global Settings, and Global Settings labels the
    same setting 'Ajustar linhas que não cumpriram a tolerância'. English used
    one label in both places, so nothing in English could show it.

    So: wherever an English string quotes another English string that is a
    label -- capitalised, as dialog labels are, unlike the lowercase keys of a
    document a message may also quote -- the label has one translation across
    every context, and the message quotes that translation.
    """
    catalogue = read_catalogue(catalogue_path(locale))
    shown: dict[str, set[str]] = {}
    for entries in catalogue.values():
        for source, translation in entries.items():
            shown.setdefault(source, set()).add(translation)
    labels = [s for s in shown if 3 <= len(s) <= 80 and s[0].isupper() and "%" not in s and "'" not in s]
    checked, problems = 0, []
    for context, entries in catalogue.items():
        for source, translation in entries.items():
            for label in labels:
                if f"'{label}'" not in source:
                    continue
                checked += 1
                if len(shown[label]) > 1:
                    problems.append(f"{label!r} is shown as {sorted(shown[label])}")
                elif not any(f"'{word}'" in translation for word in shown[label]):
                    problems.append(f"[{context}] {source[:50]!r} does not quote {sorted(shown[label])}")
    assert checked >= 5, "the check found almost nothing to check; the label filter is wrong"
    assert not problems, "\n".join(problems)


#: English strings that mean different things in different places, and may be
#: translated differently there. Everything else reads the same in every dialog.
TRANSLATED_BY_CONTEXT = {
    "(none)": "a spin box's empty value, whose gender is the quantity's: a tolerance, a constant",
    "Differences": "height differences in levelling, and between two runs in DynAdjust's comparison",
    "GPS broadcast navigation": "a choice in a list, and a product kind in the middle of a sentence",
    "GLONASS broadcast navigation": "a choice in a list, and a product kind in the middle of a sentence",
    "Layout": "how a level book's columns are arranged, and a QGIS print layout",
    "To": "where a levelling line ends, and the frame a transformation goes to",
    "Uncheckable": "a column counting observations, and one observation's decision",
}


def _shown(locale: str) -> dict[str, set[str]]:
    shown: dict[str, set[str]] = {}
    for entries in read_catalogue(catalogue_path(locale)).values():
        for source, translation in entries.items():
            shown.setdefault(source, set()).add(translation)
    return shown


@pytest.mark.parametrize("locale", TARGET_LOCALES)
def test_one_english_string_reads_the_same_in_every_dialog(locale):
    """A reader who learns a label in one dialog looks for the same words in the next.

    Found in P13-7, translating the integration walkthrough: the integration and
    levelling dialogs offered 'Estimate a variance component per technique' as
    'um componente' and 'uma componente' in Portuguese, 'un' and 'una' in Spanish.
    The same check found eight more labels worded two ways, and 'Property' spelt
    'Propriedad' in two Spanish dialogs and 'Propiedad' in six.

    A string listed in TRANSLATED_BY_CONTEXT says what it means in each place.
    """
    shown = _shown(locale)
    catalogue = read_catalogue(catalogue_path(locale))
    repeated = sum(1 for source in shown if sum(source in entries for entries in catalogue.values()) > 1)
    assert repeated >= 100, f"only {repeated} strings are in two contexts or more; the read is wrong"
    problems = [
        f"{source!r} is shown as {sorted(translations)}"
        for source, translations in shown.items()
        if len(translations) > 1 and source not in TRANSLATED_BY_CONTEXT
    ]
    assert not problems, "\n".join(problems)


def test_every_string_translated_by_context_still_differs():
    """An exception no catalogue needs any more is removed, so the list stays a list of reasons."""
    differing = {
        source
        for locale in TARGET_LOCALES
        for source, translations in _shown(locale).items()
        if len(translations) > 1
    }
    assert not sorted(set(TRANSLATED_BY_CONTEXT) - differing)


def test_qm_files_are_not_committed():
    """.qm are build artefacts generated at packaging (specs/18 section 4).
    Committing them means shipping a stale translation nobody notices."""
    from scripts.translations import I18N_DIR

    committed = sorted(path.name for path in I18N_DIR.glob("*.qm"))
    assert not committed, f"compiled catalogues must not be committed: {committed}"
