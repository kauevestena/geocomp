# SPDX-License-Identifier: GPL-2.0-or-later
"""Mutation and false-positive tests for the report language comparison."""

from __future__ import annotations

import pytest

from tests.report_language import Report, retained_english

CATALOGUE = {"Report": {"GNSS": "GNSS", "QGIS": "QGIS", "a priori": "a priori"}}


def test_inline_markup_entities_and_void_tags_do_not_hide_words():
    report = Report(
        '<html lang="es"><head><meta charset="utf-8"><title>A title</title>'
        '<style>p {color:red}</style></head><body><h2>An <b>inline</b> heading</h2>'
        '<p>Read <a href="x">the</a> '
        "whole <em>paragraph</em> &amp; <code>code</code>.<br/>Next line.</p>"
        '<div class="extra note"><b>Note</b>: ordinary text.</div>'
        '<ul><li>A list item.</li></ul></body></html>'
    )
    assert report.lang == "es"
    assert report.blocks == [
        ("label", "A title"),
        ("label", "An inline heading"),
        ("prose", "Read the whole paragraph & code. Next line."),
        ("prose", "Note: ordinary text."),
        ("prose", "A list item."),
    ]


@pytest.mark.parametrize("tag", ["p", 'div class="note"', "li", "h2", "th"])
def test_an_untranslated_block_fails_even_if_not_in_the_catalogue(tag):
    close = tag.split()[0]
    block = Report(f"<{tag}>Check the observations before proceeding.</{close}>")
    assert retained_english(block, block, CATALOGUE)


@pytest.mark.parametrize("markup", ["{}", "<em>{}</em>", '<a href="x">{}</a>'])
def test_a_translated_opening_does_not_hide_an_english_sentence(markup):
    sentence = markup.format("Check the observations before proceeding.")
    english = Report(f"<p>Summary. {sentence}</p>")
    shown = Report(f"<p>Resumen. {sentence}</p>")
    assert retained_english(english, shown, CATALOGUE)


def test_catalogue_approved_technical_terms_are_accepted():
    block = Report("<h2>GNSS</h2><p>QGIS — GNSS — a priori — 12 mm</p>")
    assert not retained_english(block, block, CATALOGUE)


def test_latin_terms_preserved_in_longer_catalogue_entries_are_accepted():
    catalogue = {"Report": {"Variance factor, a priori": "Fator de variância, a priori"}}
    assert not retained_english(Report("<p>a priori</p>"), Report("<p>a priori</p>"), catalogue)
    # Without the catalogue evidence it is not automatically excused.
    assert retained_english(Report("<p>a priori</p>"), Report("<p>a priori</p>"), {})


def test_a_technical_term_does_not_excuse_the_sentence_around_it():
    english = Report("<p>Summary. GNSS observations have not been checked.</p>")
    shown = Report("<p>Resumen. GNSS observations have not been checked.</p>")
    assert retained_english(english, shown, CATALOGUE)


def test_a_short_english_instruction_after_a_translated_opening_fails():
    assert retained_english(
        Report("<p>Summary. Check inputs.</p>"), Report("<p>Resumen. Check inputs.</p>"), CATALOGUE
    )


def test_english_user_data_is_accepted_even_when_it_matches_a_catalogue_source():
    data = (
        "Adjusted stations",
        "/survey/Check the observations.txt",
        "Check the observations before proceeding.",
    )
    catalogue = {"Report": {**CATALOGUE["Report"], "Adjusted stations": "Estaciones ajustadas"}}
    english = Report(f"<h2>{data[0]}</h2><p>{data[1]}</p><li>{data[2]}</li>")
    assert not retained_english(english, english, catalogue, data=data)
    assert retained_english(english, english, catalogue)


def test_user_data_does_not_excuse_untranslated_surrounding_prose():
    block = Report("<p>West station: Check the observations before proceeding.</p>")
    assert retained_english(block, block, CATALOGUE, data=("West station",))


def test_solution_ids_in_a_translated_covariance_notice_are_data():
    ids = ("dam-2025.0-adjustment", "dam-2026.0-adjustment")
    identifiers = ", ".join(ids)
    english = Report(f"<p>Solutions: {identifiers} carry only station blocks.</p>")
    shown = Report(f"<p>Soluções: {identifiers} contêm apenas blocos das estações.</p>")
    assert retained_english(english, shown, CATALOGUE)
    assert not retained_english(english, shown, CATALOGUE, data=ids)


def test_lost_or_reclassified_prose_is_not_silently_zipped_away():
    with pytest.raises(AssertionError):
        retained_english(Report("<h1>T</h1><p>Text.</p>"), Report("<h1>T</h1>"), CATALOGUE)
