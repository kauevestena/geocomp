# SPDX-License-Identifier: GPL-2.0-or-later
"""A number a person reads has the decimal separator of the language (FR-094; specs/18 criterion 6)."""

from __future__ import annotations

import math
import threading

import pytest

from geocomp.core.display_format import DisplayFormat
from geocomp.core.number_format import (
    decimal_separator,
    localised,
    numbers_for,
    separator_for,
    set_display_locale,
)


@pytest.fixture(autouse=True)
def _english_afterwards():
    yield
    set_display_locale("en")


@pytest.mark.parametrize(
    ("locale", "separator"),
    [("en", "."), ("pt_BR", ","), ("es", ","), ("pt_PT", ","), ("es_MX", ","), ("de", ".")],
)
def test_each_language_has_its_separator(locale, separator):
    """``de`` is not shipped: an unshipped language reads GeoComp in English,
    and its numbers are English too."""
    assert separator_for(locale) == separator


def test_the_display_language_sets_it_and_a_run_holds_its_own():
    assert decimal_separator() == "."
    set_display_locale("pt_BR")
    assert decimal_separator() == ","
    with numbers_for("en"):
        assert decimal_separator() == "."
    assert decimal_separator() == ","


def test_a_run_on_another_thread_keeps_the_separator_it_started_with():
    """Processing runs an algorithm on a worker thread while the user may change
    the language on the main one."""
    seen = []
    started, changed = threading.Event(), threading.Event()

    def run():
        with numbers_for("pt_BR"):
            started.set()
            changed.wait(5)
            seen.append(decimal_separator())

    worker = threading.Thread(target=run)
    worker.start()
    started.wait(5)
    set_display_locale("en")
    changed.set()
    worker.join(5)
    assert seen == [","]


class TestTheReportsFormatters:
    def test_every_display_format_method_uses_it(self):
        shown = DisplayFormat(angle_format="dms", angle_decimals=1, coordinate_decimals=3)
        with numbers_for("pt_BR"):
            assert shown.coordinate(7395123.45678) == "7395123,457"
            assert shown.distance(12.3456) == "12,346"
            assert shown.small_angle(math.radians(1.24 / 3600.0)) == "1,2"
            assert shown.angle(math.radians(12.5 + 16.24 / 3600.0)) == "12° 30' 16,2\""
        with numbers_for("es"):
            assert DisplayFormat(angle_format="gon").angle(math.pi / 2) == "100,00000 gon"

    def test_english_is_unchanged(self):
        """Every report written before P12c was English, and is the same now."""
        shown = DisplayFormat(coordinate_decimals=3)
        with numbers_for("en"):
            assert shown.coordinate(7395123.45678) == "7395123.457"

    def test_only_the_number_is_changed_by_its_caller(self):
        """``localised`` changes every point it is given, which is why it is
        called on the number alone, never on a sentence holding one."""
        with numbers_for("pt_BR"):
            assert localised("1.5") == "1,5"
            assert localised("2.5e-06") == "2,5e-06"


def test_a_file_is_written_with_a_point_whatever_the_language():
    """FR-095: the formatter for a machine is not the one for a person."""
    pytest.importorskip("qgis")
    from geocomp.algorithms.reporting import exact, format_number

    with numbers_for("pt_BR"):
        assert format_number(0.0021) == "0,0021"
        assert exact(0.0021) == "0.0021"
