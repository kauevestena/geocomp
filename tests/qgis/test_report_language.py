# SPDX-License-Identifier: GPL-2.0-or-later
"""A whole report, read in each language (specs/18 criterion 2; P13-34).

``test_language.py`` switches the language and reads single labels and
findings back. What a reader opens is the report, so these run the tutorial's
adjustment end to end, once in English and once in each language, and compare
the three HTML files: each declares the language it is in, and no heading,
column or note of the English report is left in English in the others.

Held to what a person reads. Names the survey gives (stations, instruments),
numbers and units are the same in every language and are not compared; a word
that is the same in two languages (*Station*, in Portuguese and Spanish both
*Estação*, *Estación*, but *GNSS* in all three) is excused only if the
catalogue itself says so.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

from tests.qgis.test_language import LANGUAGES, _Installed
from tests.qgis.test_tutorial import INNER, NETWORK, TUTORIAL_ALGORITHM, _network, _run

pytestmark = pytest.mark.qgis

#: The tags whose text is the report's own words: titles, headings and column heads.
_LABELS = {"title", "h1", "h2", "h3", "th", "legend", "caption"}


class _Report(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.labels: list[str] = []
        self._open: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "html":
            self.lang = dict(attrs).get("lang")
        self._open.append(tag)

    def handle_endtag(self, tag):
        while self._open and self._open.pop() != tag:
            pass

    def handle_data(self, data):
        text = " ".join(data.split())
        if text and self._open and self._open[-1] in _LABELS:
            self.labels.append(text)


def _read(path: Path) -> _Report:
    report = _Report()
    report.feed(path.read_text(encoding="utf-8"))
    return report


@pytest.fixture(scope="module")
def reports(geocomp_provider, tmp_path_factory) -> dict[str, _Report]:
    """The tutorial's adjustment, reported once in each of the three languages."""
    directory = tmp_path_factory.mktemp("report-language")
    put = _run(TUTORIAL_ALGORITHM, {"DATASET": 0, "DESTINATION": str(directory)})
    installed = Path(put["OUTPUT_DIRECTORY"])
    imported = _run(
        "geocomp:totalstation_import_fieldbook",
        {
            "SOURCE": str(installed / "raw_data.csv"),
            "MAPPING": str(installed / "mapping.json"),
            "PROFILES": str(installed / "profiles.json"),
            "OUTPUT_READINGS": str(installed / "readings.json"),
        },
    )
    reduced = _run(
        "geocomp:totalstation_preprocess",
        {
            "READINGS": imported["OUTPUT_READINGS"],
            "PROFILES": str(installed / "profiles.json"),
            "OUTPUT_REDUCED": str(installed / "reduced.json"),
        },
    )
    made: dict[str, _Report] = {}
    for locale in ("en", *LANGUAGES):
        path = installed / f"report-{locale}.html"
        parameters = _network(installed, reduced, f"solution-{locale}", datum=INNER, OUTPUT_HTML=str(path))
        if locale == "en":
            _run(NETWORK, parameters)
        else:
            with _Installed(locale):
                _run(NETWORK, parameters)
        made[locale] = _read(path)
    return made


def test_each_report_declares_its_language(reports):
    assert {locale: report.lang for locale, report in reports.items()} == {
        "en": "en",
        "pt_BR": "pt-BR",
        "es": "es",
    }


@pytest.mark.parametrize("locale", LANGUAGES)
def test_a_report_has_the_same_headings_in_every_language(reports, locale):
    assert len(reports[locale].labels) == len(reports["en"].labels)


@pytest.mark.parametrize("locale", LANGUAGES)
def test_no_heading_is_left_in_english(reports, locale):
    from tests.qgis.test_language import _catalogue

    catalogue = _catalogue(locale)
    kept = {source for context in catalogue.values() for source, text in context.items() if source == text}
    english = reports["en"].labels
    left = [
        label
        for label, shown in zip(english, reports[locale].labels, strict=True)
        if label == shown and re.search(r"[A-Za-z]{4,}", label) and label not in kept
    ]
    assert not left, f"still English in {locale}: {left}"
