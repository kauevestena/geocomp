# SPDX-License-Identifier: GPL-2.0-or-later
"""Switching the language translates GeoComp, whatever QGIS's own is (specs/18 criteria 2 and 3).

The catalogues are complete (``tests/structural/test_translations.py``), but a
complete catalogue translates nothing if a string is looked up under a context
it was not filed under -- which P12c's audit found twice: "Requirement" in every
algorithm's help, and every Processing group's name, had never been translated.
So these switch the language and read GeoComp back.

The translator is built from the ``.ts`` catalogue rather than a compiled
``.qm``: the QGIS image CI runs in need not have ``lrelease``, and what is under
test is where GeoComp looks its words up, not Qt's file format.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis

LANGUAGES = ("pt_BR", "es")


def _catalogue(locale: str) -> dict[str, dict[str, str]]:
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "scripts"))
    try:
        from translations import read_catalogue
    finally:
        sys.path.pop(0)
    return read_catalogue(root / "geocomp" / "i18n" / f"geocomp_{locale}.ts")


class _Installed:
    """The catalogue for *locale*, installed for the length of a ``with``."""

    def __init__(self, locale: str):
        from qgis.PyQt.QtCore import QTranslator

        catalogue = _catalogue(locale)

        class FromCatalogue(QTranslator):
            def translate(self, context, source, disambiguation=None, n=-1):
                # None, not "": an empty string is a translation, to Qt.
                return catalogue.get(context, {}).get(source) or None

        self.translator = FromCatalogue()
        self.catalogue = catalogue

    def __enter__(self):
        from qgis.PyQt.QtCore import QCoreApplication

        QCoreApplication.installTranslator(self.translator)
        return self.catalogue

    def __exit__(self, *exc):
        from qgis.PyQt.QtCore import QCoreApplication

        QCoreApplication.removeTranslator(self.translator)


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


def _words(algorithm) -> list[str]:
    """Every word an algorithm shows a user, before its help."""
    words = [algorithm.displayName(), algorithm.group()]
    if algorithm.shortDescription():
        words.append(algorithm.shortDescription())
    words += [p.description() for p in algorithm.parameterDefinitions()]
    words += [o.description() for o in algorithm.outputDefinitions()]
    return words


def _translations(catalogue, source: str) -> set[str]:
    """What *source* may be shown as: its translation in any context that files it.

    Shared helpers -- the layer outputs, the PostgreSQL connection parameters
    -- translate their words under their own context, which is right; what is
    wrong is a word shown untranslated, or one no context files at all.
    """
    return {m[source] for m in catalogue.values() if m.get(source)}


def _fresh(algorithm_id: str):
    from qgis.core import QgsApplication

    # create() runs initAlgorithm, so the labels are read in the language
    # installed now, not the one the registered instance was built in.
    return QgsApplication.processingRegistry().algorithmById(algorithm_id).create({})


@pytest.mark.parametrize("locale", LANGUAGES)
def test_every_algorithm_speaks_the_language(locale):
    from geocomp.registry import ALGORITHMS

    wrong = []
    for spec in ALGORITHMS:
        english = _words(_fresh(spec.id))
        with _Installed(locale) as catalogue:
            shown = _words(_fresh(spec.id))
        for source, text in zip(english, shown, strict=True):
            expected = _translations(catalogue, source)
            if not expected:
                wrong.append(f"{spec.id}: {source!r} is in no catalogue context")
            elif text not in expected:
                wrong.append(f"{spec.id}: {source!r} shown as {text!r}")
    assert not wrong, f"{len(wrong)} words:\n" + "\n".join(wrong)


@pytest.mark.parametrize("locale", LANGUAGES)
def test_every_help_speaks_the_language(locale):
    """The help is where "Requirement" stayed English in every algorithm."""
    from geocomp.registry import ALGORITHMS

    untranslated = []
    for spec in ALGORITHMS:
        english = _fresh(spec.id).shortHelpString()
        with _Installed(locale):
            shown = _fresh(spec.id).shortHelpString()
        body = _fresh(spec.id).help_body()
        if body in shown or "Requirement:" in shown or shown == english:
            untranslated.append(spec.id)
    assert not untranslated, f"help left in English: {untranslated}"


@pytest.mark.parametrize("locale", LANGUAGES)
def test_the_menu_speaks_the_language(locale):
    """Every entry of the GeoComp menu, the algorithms' included."""
    from qgis.PyQt.QtWidgets import QMenuBar

    from geocomp.gui.menu import GeoCompMenu

    def entries() -> list[str]:
        bar = QMenuBar()
        menu = GeoCompMenu(None, run_algorithm=lambda _id: None, open_settings=lambda: None)
        built = menu.build(bar)
        texts = []

        def walk(container):
            for action in container.actions():
                if action.isSeparator():
                    continue
                texts.append(action.text())
                if action.menu() is not None:
                    walk(action.menu())

        texts.append(built.title())
        walk(built)
        menu.unload()
        return texts

    english = entries()
    with _Installed(locale) as catalogue:
        shown = entries()
    sources = {source for messages in catalogue.values() for source in messages}
    unchanged = [
        source
        for source, text in zip(english, shown, strict=True)
        if text == source
        and source in sources
        and any(m.get(source) not in (None, source) for m in catalogue.values())
    ]
    assert len(shown) == len(english) > 40
    assert not unchanged, f"left in English: {unchanged}"


def test_geocomps_language_overrides_qgiss():
    """Criterion 3: the language in Global Settings wins over QGIS's own."""
    from qgis.core import QgsSettings

    from geocomp.i18n import resolve_locale
    from geocomp.plugin import _language_override
    from geocomp.services.settings_service import SETTINGS_PREFIX

    settings = QgsSettings()
    keys = ("locale/overrideFlag", "locale/userLocale", f"{SETTINGS_PREFIX}/interface.language")
    saved = {key: settings.value(key) for key in keys}
    try:
        settings.setValue("locale/overrideFlag", True)
        settings.setValue("locale/userLocale", "es_ES")
        settings.setValue(f"{SETTINGS_PREFIX}/interface.language", "pt_BR")
        assert resolve_locale(_language_override()) == "pt_BR"
        settings.setValue(f"{SETTINGS_PREFIX}/interface.language", "system")
        assert resolve_locale(_language_override()) == "es"
    finally:
        for key, value in saved.items():
            if value is None:
                settings.remove(key)
            else:
                settings.setValue(key, value)
