# SPDX-License-Identifier: GPL-2.0-or-later
"""The core's enums in words, in the language (P12c-42; FR-091).

Until P12c-42 a Portuguese report's datum read "minimum_constraint" and its
frame "plane_2d": the enum's value, shown as it stood. ``geocomp.algorithms.labels``
says each in words; the structural test holds every report and log line to it.
"""

from __future__ import annotations

import pytest

from tests.conftest import requires_qgis
from tests.qgis.test_language import LANGUAGES, _Installed

pytestmark = [pytest.mark.qgis, requires_qgis]


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    """A running application, without which no translator is consulted."""
    return geocomp_provider


def test_every_member_of_every_enum_shown_has_words():
    from geocomp.algorithms import labels

    words = labels._labels()
    missing = [
        f"{enum.__name__}.{member.name}" for enum in labels.LABELLED for member in enum if member not in words
    ]
    assert not missing, missing


@pytest.mark.parametrize("locale", LANGUAGES)
def test_the_words_are_the_languages(locale):
    from geocomp.algorithms.labels import defect_words, in_words
    from geocomp.core.adjustment.datum import DatumDefect, DefectComponent
    from geocomp.core.adjustment.parameters import Frame
    from geocomp.core.models.solution import DatumDefinition

    defect = DatumDefect(Frame.PLANE_2D, (DefectComponent.TRANSLATION_E, DefectComponent.SCALE))
    with _Installed(locale) as catalogue:
        datum = in_words(DatumDefinition.MINIMUM_CONSTRAINT)
        described = defect_words(defect)
    words = catalogue["GeoCompLabels"]
    assert datum == words["minimum constraints"]
    assert described == (
        words["%1 (%2)"]
        .replace("%1", "2")
        .replace("%2", f"{words['translation in easting']}, {words['scale']}")
    )
    assert "minimum_constraint" not in datum and "translation_e" not in described


def test_the_global_test_says_which_way_it_failed_and_what_to_check():
    from types import SimpleNamespace

    from geocomp.algorithms.reporting import global_test_failed
    from tests.structural.test_message_templates import _REMEDY

    large = global_test_failed(SimpleNamespace(statistic=30.0, critical_high=20.0))
    small = global_test_failed(SimpleNamespace(statistic=1.0, critical_high=20.0))
    assert "too large" in large and "too small" in small
    assert _REMEDY.search(large) and _REMEDY.search(small)


def test_a_skipped_dynadjust_stage_says_why_in_words():
    from geocomp.algorithms.engines.dynadjust_adjust import skipped_stage
    from geocomp.engines.dynadjust.engine import Stage

    stage = Stage("dnasegment", included=False, reason="12 stations adjust simultaneously",
                  code="simultaneous", context={"stations": 12, "threshold": 5000})
    assert skipped_stage(stage) == "Skipping dnasegment: 12 stations adjust simultaneously."
    # A job an older release prepared has no code: said without the why, not in English.
    old = Stage("dnageoid", included=False, reason="every height is ellipsoidal; no geoid is involved")
    assert skipped_stage(old) == "Skipping dnageoid."
