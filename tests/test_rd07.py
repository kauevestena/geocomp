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

    def test_the_production_reader_reads_it_and_settles_its_clock(self, data):
        """Phase P8b's CG-5 reader, on the real survey the script's parser was
        checked against: the same readings, and the clock's reading stated in
        the notes with how well the firmware's tide agrees under it. The file's
        GMT difference is zero, so UTC is an assumption, and the note says so."""
        from geocomp.io.gravimeter_files import read_cg5 as read_production

        path = data / "cg5" / "CG-5_TestData.txt"
        script = read_cg5(path)
        read = read_production(path.read_text(encoding="latin-1"), replace_tide=True)
        assert len(read.readings) == len(script.readings) == 2096
        for mine, theirs in zip(read.readings, script.readings, strict=True):
            assert mine.station == theirs.station
            assert mine.instant == theirs.instant
            assert mine.tide_applied is False
            assert mine.value.value == pytest.approx(
                (theirs.gravity_mgal - theirs.tide_mgal) * 1e-5, abs=1e-12
            )
        (clock,) = [note for note in read.notes if "GMT difference" in note]
        assert "taken as UTC" in clock and "agrees with Longman's" in clock

    @pytest.mark.parametrize("day", sorted(PYGRAV_DAYS))
    def test_the_survey_runs_through_the_algorithms_path(self, data, day):
        """Phase P8b's exit, on the real file: reader, reduction and network --
        the path both algorithms take -- adjust each day of the survey, and
        land near pyGrav's published stations.

        Near, not on: GeoComp gives each day one linear drift, where pyGrav
        split each day by hand into eight loops with a drift apiece and
        rejected readings, so this is a check that the chain works on a real
        CG-5 file and not a precision claim. Observed with a 5 microgal floor:
        3.0, 5.9, 3.7 and 4.3 microgal at worst, 1.5 to 3.3 of GeoComp's own
        sigmas; and the global test fails on three of the four days, because
        one drift a day is too simple a model for this instrument.
        """
        from geocomp.core.instruments import ProfileLibrary
        from geocomp.core.instruments.gravimeter import GravimeterProfile
        from geocomp.core.techniques.gravimetry import (
            adjust_gravity_network,
            build_gravity_network,
            reduce_readings,
        )
        from geocomp.core.uncertainty import Quantity
        from geocomp.core.units import Unit
        from geocomp.io.gravimeter_files import read_cg5 as read_production

        text = (data / "cg5" / "CG-5_TestData.txt").read_text(encoding="latin-1")
        survey = read_production(text, additive_sigma=5e-8)
        library = ProfileLibrary()
        library.add_gravimeter(GravimeterProfile(id=survey.instruments[0]))
        reduced = [
            r for r in reduce_readings(list(survey.readings), library) if r.reading.session.endswith(day)
        ]
        result = adjust_gravity_network(
            build_gravity_network(reduced, library, held={"1": Quantity.exact(0.0, Unit.ACCELERATION)})
        )
        published = read_pygrav(day, data / "pygrav" / day / "LSresults_tot.dat").stations
        adjusted = {s.station_id: s.gravity.value / 1e-5 for s in result.solution.adjusted_stations}
        assert set(adjusted) == set(published) - {"1"}
        worst = max(abs(adjusted[station] - published[station]) for station in adjusted)
        assert worst * 1000.0 < 10.0

    @pytest.mark.parametrize("day", sorted(PYGRAV_DAYS))
    def test_pygravs_published_solution_is_reproduced(self, data, day):
        comparison = compare_pygrav(read_pygrav(day, data / "pygrav" / day / "LSresults_tot.dat"))
        assert comparison.model_vs_published_ugal <= comparison.envelope_ugal
        assert comparison.geocomp_vs_model_ugal <= MACHINE_UGAL
        assert comparison.geocomp_vs_published_ugal <= comparison.envelope_ugal + comparison.sst_effect_ugal
