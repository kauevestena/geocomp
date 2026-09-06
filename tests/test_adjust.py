# SPDX-License-Identifier: GPL-2.0-or-later
"""The *Adjust* format reader and writer (FR-161, specs/17 section 5.2).

Tier 1. The networks here are written in the test rather than taken from the
corpus: ``tests/test_adjust_corpus.py`` exercises the real five, and these pin
the rules a corpus run would only show indirectly -- the station order of an
angle, the weighting of a control station, and the header count that is the
format's own check on a misparse.

**The grammar is inferred from example files, not transcribed from a
specification** (``geocomp/io/adjust.py`` says why, and what makes the inference
solid). That is the reason these tests are written against the conventions
individually: an inferred grammar with one convention wrong still parses, and
produces a network that adjusts.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.errors import DataError
from geocomp.core.models import ConstraintMode, Network, ObservationType, Station
from geocomp.core.units import Unit
from geocomp.io.adjust import read_adjust, write_adjust

#: A traverse of the same shape as the published ones: four weighted control
#: stations, one unknown, one distance and one angle.
SMALL = """\
A LITTLE TRAVERSE
1 1 0 2 3
A 100.0000 200.0000 0.010 0.010
B 100.0000 300.0000 0.010 0.010
P 150.0000 250.0000
A P 70.711 0.004
B A P 45 00 00 9.0
"""


def write(tmp_path, text, name="network.Adat"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


class TestReading:
    def test_the_title_and_counts_come_back(self, tmp_path):
        report = read_adjust(write(tmp_path, SMALL))
        assert report.title == "A LITTLE TRAVERSE"
        assert report.declared == (1, 1, 0)
        assert report.found == (1, 1, 0)
        assert report.counts_agree
        assert report.has_values

    def test_x_is_the_easting(self, tmp_path):
        """Verified against the corpus by arithmetic (specs/22 section 4.1): read
        the other way round, the angles the files state disagree with the angles
        their own coordinates imply."""
        position = read_adjust(write(tmp_path, SMALL)).network.stations["P"].approx_position
        assert position.component("easting").value == pytest.approx(150.0)
        assert position.component("northing").value == pytest.approx(250.0)

    def test_control_is_weighted_rather_than_held(self, tmp_path):
        """The format states two standard deviations per control station.

        Holding such a station exactly would turn a stated uncertainty into an
        assertion of certainty -- the same rule ``specs/07`` section 4.3 applies
        to DynAdjust, in the other direction.
        """
        network = read_adjust(write(tmp_path, SMALL)).network
        constraint = network.stations["A"].constraint
        assert constraint.mode is ConstraintMode.WEIGHTED
        assert constraint.components == frozenset({"easting", "northing"})
        assert constraint.covariance.std_devs() == pytest.approx(
            {"easting": 0.010, "northing": 0.010}
        )
        assert network.stations["P"].constraint.is_free

    def test_control_without_its_sigmas_is_refused(self, tmp_path):
        text = SMALL.replace("A 100.0000 200.0000 0.010 0.010", "A 100.0000 200.0000")
        with pytest.raises(DataError) as caught:
            read_adjust(write(tmp_path, text))
        assert caught.value.code == "data.adjust_control_without_sigmas"

    def test_an_angle_names_the_occupied_station_second(self, tmp_path):
        """``backsight at foresight`` in the file; ``(at, backsight, foresight)``
        in the observation.

        ``equations._horizontal_angle`` takes the occupied station first. Passing
        the row through unchanged computes the angle at the *backsight* -- a
        different angle, and one whose adjustment converges.
        """
        angle = next(
            o for o in read_adjust(write(tmp_path, SMALL)).network.observations.values()
            if o.type is ObservationType.HORIZONTAL_ANGLE
        )
        assert angle.stations == ("A", "B", "P")
        assert angle.value.value == pytest.approx(math.radians(45.0))

    def test_an_angle_sigma_is_seconds_of_arc(self, tmp_path):
        angle = next(
            o for o in read_adjust(write(tmp_path, SMALL)).network.observations.values()
            if o.type is ObservationType.HORIZONTAL_ANGLE
        )
        assert angle.value.std_dev == pytest.approx(math.radians(9.0 / 3600.0))

    def test_a_distance_is_horizontal_and_in_metres(self, tmp_path):
        distance = next(
            o for o in read_adjust(write(tmp_path, SMALL)).network.observations.values()
            if o.type is ObservationType.HORIZONTAL_DISTANCE
        )
        assert distance.stations == ("A", "P")
        assert distance.value.value == pytest.approx(70.711)
        assert distance.value.std_dev == pytest.approx(0.004)
        assert distance.value.unit is Unit.METRE


class TestThePlanHalf:
    """A file without values is an observation programme, not measurements."""

    PLAN = """\
A LITTLE TRAVERSE
1 1 0 2 3
A 100.0000 200.0000 0.010 0.010
B 100.0000 300.0000 0.010 0.010
P 150.0000 250.0000
A P
B A P
"""

    def test_it_yields_stations_and_a_topology_and_no_observations(self, tmp_path):
        report = read_adjust(write(tmp_path, self.PLAN))
        assert not report.has_values
        assert len(report.network.stations) == 3
        assert report.network.observations == {}
        assert report.plan == (("distance", ("A", "P")), ("angle", ("B", "A", "P")))

    def test_the_two_halves_of_a_pair_have_the_same_topology(self, tmp_path):
        """Which is what makes them comparable -- and comparing them is what
        found a real defect in the published corpus (specs/22 section 4.2)."""
        valued = read_adjust(write(tmp_path, SMALL, "v.Adat"))
        plan = read_adjust(write(tmp_path, self.PLAN, "p.Adat"))
        assert valued.plan == plan.plan

    def test_a_file_that_values_only_some_rows_is_refused(self, tmp_path):
        text = self.PLAN.replace("\nA P\n", "\nA P 70.711 0.004\n")
        with pytest.raises(DataError) as caught:
            read_adjust(write(tmp_path, text))
        assert caught.value.code == "data.adjust_file_half_valued"


class TestTheHeaderIsTheFormatsOwnCheck:
    """The counts are what turns a misparse into a failure rather than a network.

    An inferred grammar needs this: without it, a reader that split the sections
    wrongly would produce observations that are merely wrong.
    """

    def test_a_disagreement_is_refused_and_names_both(self, tmp_path):
        text = SMALL.replace("1 1 0 2 3", "2 1 0 2 3")
        with pytest.raises(DataError) as caught:
            read_adjust(write(tmp_path, text))
        assert caught.value.code == "data.adjust_declared_counts_disagree"
        assert caught.value.context["declared"]["distances"] == 2
        assert caught.value.context["found"]["distances"] == 1

    def test_it_can_be_accepted_deliberately(self, tmp_path):
        """One published file fails this for a knowable reason, and its
        observations are still there (specs/22 section 4.2)."""
        text = SMALL.replace("1 1 0 2 3", "2 1 0 2 3")
        report = read_adjust(write(tmp_path, text), accept_count_mismatch=True)
        assert report.declared == (2, 1, 0)
        assert report.found == (1, 1, 0)
        assert not report.counts_agree

    def test_azimuths_are_refused_rather_than_guessed(self, tmp_path):
        """No example of an azimuth row exists, so its layout cannot be pinned."""
        text = SMALL.replace("1 1 0 2 3", "1 1 1 2 3")
        with pytest.raises(DataError) as caught:
            read_adjust(write(tmp_path, text))
        assert caught.value.code == "data.adjust_azimuths_unsupported"

    def test_an_unknown_station_is_refused(self, tmp_path):
        text = SMALL.replace("A P 70.711 0.004", "A Z 70.711 0.004")
        with pytest.raises(DataError) as caught:
            read_adjust(write(tmp_path, text))
        assert caught.value.code == "data.adjust_observation_station_unknown"
        assert caught.value.context["received"] == ["Z"]

    def test_minutes_of_sixty_are_refused(self, tmp_path):
        text = SMALL.replace("45 00 00 9.0", "45 60 00 9.0")
        with pytest.raises(DataError) as caught:
            read_adjust(write(tmp_path, text))
        assert caught.value.code == "data.adjust_angle_out_of_range"


class TestWriting:
    """FR-161 is interoperability, so the format is written as well as read."""

    def test_a_network_round_trips(self, tmp_path):
        original = read_adjust(write(tmp_path, SMALL))
        path = write_adjust(original.network, tmp_path / "out.Adat", title=original.title)
        again = read_adjust(path)

        assert again.title == original.title
        assert again.declared == original.declared == again.found
        assert set(again.network.stations) == set(original.network.stations)
        for station_id, station in original.network.stations.items():
            back = again.network.stations[station_id]
            for component in ("easting", "northing"):
                assert back.approx_position.component(component).value == pytest.approx(
                    station.approx_position.component(component).value
                )
            assert back.constraint.mode is station.constraint.mode

        pairs = {
            (o.type, o.stations): o.value
            for o in original.network.observations.values()
        }
        for observation in again.network.observations.values():
            before = pairs[(observation.type, observation.stations)]
            assert observation.value.value == pytest.approx(before.value, abs=5e-6)
            assert observation.value.std_dev == pytest.approx(before.std_dev, rel=1e-3)

    def test_a_type_the_format_cannot_hold_is_refused(self, tmp_path):
        """Writing the file without it would export a different network."""
        from geocomp.core.models import Observation
        from geocomp.core.uncertainty import Quantity

        network = read_adjust(write(tmp_path, SMALL)).network
        network.add_observation(
            Observation(
                id="z1",
                type=ObservationType.ZENITH_ANGLE,
                stations=("A", "P"),
                values=(Quantity.from_std_dev(1.57, 1e-5, Unit.RADIAN),),
            )
        )
        with pytest.raises(DataError) as caught:
            write_adjust(network, tmp_path / "out.Adat")
        assert caught.value.code == "data.adjust_cannot_express_observation"
        assert "zenith_angle" in caught.value.context["received"]

    def test_seconds_that_round_to_sixty_carry(self, tmp_path):
        """The defect specs/07 section 5.5 records in DynAdjust's own printer,
        avoided here: 59.999 seconds must not be written as 60."""
        from geocomp.core.models import Observation
        from geocomp.core.uncertainty import Quantity

        network = Network(id="carry", crs="LOCAL")
        for station in read_adjust(write(tmp_path, SMALL)).network.stations.values():
            network.add_station(
                Station(
                    id=station.id,
                    approx_position=station.approx_position,
                    constraint=station.constraint,
                )
            )
        network.add_observation(
            Observation(
                id="a1",
                type=ObservationType.HORIZONTAL_ANGLE,
                stations=("A", "B", "P"),
                values=(
                    # 44 deg 59' 59.999" -- which rounds to 60.00 seconds at the
                    # precision the writer prints, and must carry rather than
                    # be written as a minute of sixty.
                    Quantity.from_std_dev(
                        math.radians(45.0 - 0.001 / 3600.0), 1e-6, Unit.RADIAN
                    ),
                ),
            )
        )
        path = write_adjust(network, tmp_path / "carry.Adat")
        angle_row = path.read_text().strip().splitlines()[-1].split()
        assert angle_row[3:6] == ["45", "00", "00.00"]
