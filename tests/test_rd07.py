# SPDX-License-Identifier: GPL-2.0-or-later
"""RD-07: a real CG-5 survey and pyGrav's published solution (``specs/22`` section 5.6).

Neither reference can be committed -- pyGrav states no licence, and the CG-5
file came from it -- so the comparisons run where ``scripts/check_rd07.py
--fetch`` has put them, named by ``GEOCOMP_RD07_DATA``, and skip with that
reason everywhere else. The ``reference`` workflow sets it.

What runs everywhere is the half that needs no fetched data: that GeoComp's
adjustment *is* the model the published solution came from, minus the one term
GeoComp deliberately does not add, checked on a survey that is vendored.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.check_rd07 import (
    CG5_MAX_UGAL,
    CG5_RMS_UGAL,
    MACHINE_UGAL,
    PYGRAV_DAYS,
    PublishedDay,
    compare_cg5_tide,
    compare_pygrav,
    geocomp_solution,
    pygrav_model,
    read_cg5,
    read_pygrav,
    verify,
)

VENDORED = Path(__file__).parent / "data" / "rd07" / "gsadjust"
FETCHED = os.environ.get("GEOCOMP_RD07_DATA")

requires_fetched = pytest.mark.skipif(
    not FETCHED,
    reason=(
        "RD-07's CG-5 survey and pyGrav results cannot be redistributed; "
        "scripts/check_rd07.py --fetch puts them in a directory named by GEOCOMP_RD07_DATA"
    ),
)


def _usgs_day() -> PublishedDay:
    """USGS Test 2 in pyGrav's input shape: one loop, rows ``(station, mGal, sd, day)``.

    Station names become numbers because pyGrav's model holds station "1" at
    zero; ``sta1`` is the loop's first station, as station 1 is in pyGrav's.
    """
    rows = []
    for line in (VENDORED / "Test2.txt").read_text().splitlines():
        fields = line.split()
        hours, minutes, seconds = (int(v) for v in fields[4].split(":"))
        day = 735000.0 + (hours * 3600 + minutes * 60 + seconds) / 86400.0
        rows.append((fields[0].removeprefix("sta"), float(fields[5]), 0.003, day))
    return PublishedDay("usgs-test2", (tuple(rows),), {}, (), 0.0)


class TestGeoCompIsThePublishedModel:
    def test_to_machine_precision_without_the_datum_free_term(self):
        day = _usgs_day()
        model, drifts, sd = pygrav_model(day.loops, sst=False)
        result = geocomp_solution(day)
        for station, value in model.items():
            assert abs(result.gravity(station).value / 1e-5 - value) * 1000 < MACHINE_UGAL
        (estimate,) = result.drift.values()
        assert estimate.coefficients[0].value / 1e-5 == pytest.approx(drifts[0], abs=1e-9)
        assert result.run.variance_factor_aposteriori ** 0.5 == pytest.approx(sd, rel=1e-9)

    def test_the_datum_free_term_is_what_it_is_said_to_be(self):
        """pyGrav's S S^T: a unit-weight pseudo-observation that the station
        values sum to zero. It moves every value a little, and it moves the
        station held at zero off zero -- which is how it was found."""
        day = _usgs_day()
        with_sst, _, _ = pygrav_model(day.loops, sst=True)
        without, _, _ = pygrav_model(day.loops, sst=False)
        assert without["1"] == pytest.approx(0.0, abs=1e-12)
        assert with_sst["1"] != pytest.approx(0.0, abs=1e-6)


@pytest.fixture(scope="module")
def data() -> Path:
    return Path(FETCHED or ".")


@requires_fetched
class TestAgainstTheFetchedReferences:
    def test_the_files_are_the_pinned_ones(self, data):
        assert verify(data) == []

    def test_longman_reproduces_the_cg5_firmware(self, data):
        survey = read_cg5(data / "cg5" / "CG-5_TestData.txt")
        assert survey.tide_applied
        comparison = compare_cg5_tide(survey)
        assert comparison.readings == 2096
        assert comparison.max_ugal <= CG5_MAX_UGAL
        assert comparison.rms_ugal <= CG5_RMS_UGAL
        assert abs(comparison.mean_ugal) < 0.1

    @pytest.mark.parametrize("day", sorted(PYGRAV_DAYS))
    def test_pygravs_published_solution_is_reproduced(self, data, day):
        comparison = compare_pygrav(read_pygrav(day, data / "pygrav" / day / "LSresults_tot.dat"))
        assert comparison.model_vs_published_ugal <= comparison.envelope_ugal
        assert comparison.geocomp_vs_model_ugal <= MACHINE_UGAL
        assert comparison.geocomp_vs_published_ugal <= comparison.envelope_ugal + comparison.sst_effect_ugal
