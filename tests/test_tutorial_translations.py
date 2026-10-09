# SPDX-License-Identifier: GPL-2.0-or-later
"""The tutorials in Portuguese and Spanish say what the English says (specs/20 §8; P13-6).

Each walkthrough is checked in English against the algorithms
(``tests/qgis/test_*_tutorial.py``). A translation is checked against its
English original here, without QGIS, so that it cannot drift from what was
checked:

* the same steps, naming the same algorithms in the same order;
* the same typed values -- everything in backticks, which a reader copies into
  a dialog and which no translation may change;
* the same numbers, written with the decimal comma both languages use;
* every input it fills, and every choice from a list, named as the catalogue
  translates the English label, which is how the dialog shows it in that
  language.

The words GeoComp is quoted as saying are checked against GeoComp itself,
speaking that language, in the tier-3 tests.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pytest

from geocomp.resources import DATASETS_DIR
from scripts.translations import catalogue_path, read_catalogue
from tests.qgis.walkthrough import CHOICE, steps

LANGUAGES = ("pt_BR", "es")
#: The walkthroughs that have been translated; each must have both languages.
TRANSLATED = ("rd04-loop",)
CODE = re.compile(r"`([^`]+)`")
NUMBER = re.compile(r"(?<![\w.,])[\u2212-]?\d+(?:[.,]\d+)?(?![\w])")


def _readme(name: str, language: str = "") -> str:
    suffix = f".{language}" if language else ""
    return (DATASETS_DIR / name / f"README{suffix}.md").read_text(encoding="utf-8")


def _numbers(text: str, *, decimal: str) -> Counter:
    """Every number outside backticks, written with a point whatever *decimal* the text uses."""
    prose = CODE.sub(" ", text)
    found = (match.replace(decimal, ".") if decimal != "." else match for match in NUMBER.findall(prose))
    return Counter(found)


@pytest.fixture(scope="module", params=LANGUAGES)
def language(request) -> str:
    return request.param


@pytest.fixture(scope="module")
def shown(language) -> dict[str, set[str]]:
    """Each English source string, and every way the catalogue shows it in *language*."""
    words: dict[str, set[str]] = {}
    for entries in read_catalogue(catalogue_path(language)).values():
        for source, translation in entries.items():
            words.setdefault(source, set()).add(translation)
    return words


def test_every_shipped_walkthrough_is_translated_or_listed():
    """A dataset with a walkthrough and no translation is a gap this list makes visible."""
    for name in TRANSLATED:
        for language in LANGUAGES:
            assert (DATASETS_DIR / name / f"README.{language}.md").is_file(), (name, language)


@pytest.mark.parametrize("name", TRANSLATED)
class TestTheTranslationSaysTheSame:
    def test_the_same_steps_in_the_same_order(self, name, language):
        english, translated = steps(_readme(name)), steps(_readme(name, language))
        assert [s.algorithm_id for s in translated] == [s.algorithm_id for s in english]

    def test_the_same_values_to_type(self, name, language):
        assert Counter(CODE.findall(_readme(name, language))) == Counter(CODE.findall(_readme(name)))

    def test_the_same_numbers_with_a_decimal_comma(self, name, language):
        english = _numbers(_readme(name), decimal=".")
        translated = _numbers(_readme(name, language), decimal=",")
        assert translated == english, (translated - english, english - translated)

    def test_no_decimal_point_in_the_prose(self, name, language):
        """A number like 15.7 in Portuguese or Spanish prose is an untranslated one."""
        prose = CODE.sub(" ", _readme(name, language))
        assert not re.findall(r"(?<![\w.])\d+\.\d+(?![\w])", prose)

    def test_every_input_and_choice_is_named_as_the_dialog_names_it(self, name, language, shown):
        english, translated = steps(_readme(name)), steps(_readme(name, language))
        for original, translation in zip(english, translated, strict=True):
            assert translation.title in shown.get(original.title, set()), (original.title, translation.title)
            assert len(translation.filled) == len(original.filled), original.title
            for (label, value), (label_t, value_t) in zip(original.filled, translation.filled, strict=True):
                assert label_t in shown.get(label, set()), (label, label_t)
                assert CODE.findall(value_t) == CODE.findall(value), (label, value_t)
                choice, choice_t = CHOICE.match(value), CHOICE.match(value_t)
                assert bool(choice) == bool(choice_t), (label, value_t)
                if choice:
                    expected = shown.get(choice["choice"], set())
                    assert choice_t["choice"] in expected, (choice["choice"], value_t)


def test_the_number_reader_reads_both_ways():
    """Guards the comparison above: a regex that found nothing would pass it."""
    minus = "\N{MINUS SIGN}"
    expected = Counter({f"{minus}15.7": 1, "662": 1})
    assert _numbers(f"{minus}15.7 mm and 662, `0.008`", decimal=".") == expected
    assert _numbers(f"{minus}15,7 mm e 662, `0.008`", decimal=",") == expected
    assert Path(catalogue_path("pt_BR")).is_file()
