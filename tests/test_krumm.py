# SPDX-License-Identifier: GPL-2.0-or-later
"""The Krumm-format reader (``specs/22`` section 2).

Tier 1. The networks here are written in the test, not taken from the corpus:
``tests/test_krumm_corpus.py`` runs the real files when a machine has them, and
these pin the reading rules that a corpus run would only show indirectly -- a
sigma that persists down a column, a section header that decides a unit, a
levelling weight that depends on a length nobody would notice being dropped.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.errors import DataError
from geocomp.core.models import ClusterKind, ConstraintMode, ObservationType
from geocomp.core.units import Unit
from geocomp.io.krumm import GON, read_krumm

TRILATERATION = """\
% a square with a diagonal
[Project]
Four marks and five distances

[Source]
Written for the test, not taken from a book

[Coordinates]
%   x       y
A   0.000   0.000
B 100.000   0.000
C 100.000 100.000
D   0.000 100.000

[Datum]
fix xA yA xB yB

[Sigma0]
1

[Distances]
A B 100.000 0.005
B C 100.001
C D  99.999
D A 100.000
A C 141.421
"""


def write(tmp_path, text, name="network.dat"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


class TestReading:
    def test_the_source_travels_with_the_network(self, tmp_path):
        report = read_krumm(write(tmp_path, TRILATERATION))
        assert report.title == "Four marks and five distances"
        assert report.source.startswith("Written for the test")
        assert report.sigma0 == 1.0
        assert report.network.id == "network"

    def test_x_is_the_easting(self, tmp_path):
        """GNU Gama's converter declares ``axes-xy="en"`` for every one of these
        files. For distances it changes nothing; for an azimuth it is the whole
        answer, so it is pinned here rather than left to the corpus.
        """
        report = read_krumm(write(tmp_path, TRILATERATION))
        position = report.network.stations["B"].approx_position
        assert position.component("easting").value == pytest.approx(100.0)
        assert position.component("northing").value == pytest.approx(0.0)

    def test_a_stated_sigma_persists_down_the_column(self, tmp_path):
        report = read_krumm(write(tmp_path, TRILATERATION))
        sigmas = {
            observation.id: observation.value.std_dev
            for observation in report.network.observations.values()
        }
        assert len(sigmas) == 5
        assert sorted(sigmas.values()) == pytest.approx([0.005] * 5)

    def test_the_datum_holds_the_components_it_names(self, tmp_path):
        report = read_krumm(write(tmp_path, TRILATERATION))
        assert report.free is False
        assert report.datum_stations is None
        held = report.network.stations["A"].constraint
        assert held.mode is ConstraintMode.FIXED
        assert held.components == frozenset({"easting", "northing"})
        assert report.network.stations["C"].constraint.mode is not ConstraintMode.FIXED

    def test_only_one_axis_of_a_station_may_be_held(self, tmp_path):
        """``Hoepke_Distance_fix`` does exactly this, and GNU Gama excludes the
        file from its own suite because gama-local cannot express it.
        """
        text = TRILATERATION.replace("fix xA yA xB yB", "fix xA yA yB")
        report = read_krumm(write(tmp_path, text))
        assert report.network.stations["B"].constraint.components == frozenset({"northing"})


class TestUnits:
    def test_a_plain_section_is_gon_and_a_dms_section_is_not(self, tmp_path):
        text = """\
[Coordinates]
A 0 0
B 100 0
C 0 100

[Datum]
fix A B

[Angles]
B A C 100.0000 0.0010

[Angles,dms,s]
C A B 90-0-0 2
"""
        text = text.replace("90-0-0", "90°0'0\"")
        report = read_krumm(write(tmp_path, text))
        gon_angle, dms_angle = report.network.observations.values()

        assert gon_angle.value.value == pytest.approx(math.pi / 2.0)
        assert gon_angle.value.std_dev == pytest.approx(0.0010 * GON)
        assert dms_angle.value.value == pytest.approx(math.pi / 2.0)
        # ",s" says the sigma is in seconds of arc, not gon.
        assert dms_angle.value.std_dev == pytest.approx(math.radians(2.0 / 3600.0))

    def test_a_dms_value_may_omit_its_minutes_and_seconds(self, tmp_path):
        text = """\
[Coordinates]
A 0 0
B 100 0

[Datum]
fix A

[Azimuth,dms]
A B 240°
"""
        report = read_krumm(write(tmp_path, text))
        (azimuth,) = report.network.observations.values()
        assert azimuth.value.value == pytest.approx(math.radians(240.0))


class TestLevelling:
    TEXT = """\
[Coordinates]
1 68.927
2 60.712
3 63.193

[Datum]
fix 1

[LevelledHeightDifferences]
1 2 -8.206  400.0 0.001
1 3 -5.734 1600.0
"""

    def test_the_sigma_column_is_per_kilometre(self, tmp_path):
        """``sigma * sqrt(L/1000)``, which is why the length column is read.

        Taking the stated 1 mm as each line's own standard deviation weights a
        0.4 km line and a 1.6 km line alike; the published answers were not
        computed that way, and the difference reaches 2 mm in a small network.
        """
        report = read_krumm(write(tmp_path, self.TEXT))
        short, long_line = report.network.observations.values()
        assert short.value.std_dev == pytest.approx(0.001 * math.sqrt(0.4))
        assert long_line.value.std_dev == pytest.approx(0.001 * math.sqrt(1.6))
        assert long_line.value.unit is Unit.METRE

    def test_a_height_network_is_one_dimensional(self, tmp_path):
        assert read_krumm(write(tmp_path, self.TEXT)).dimension == 1

    def test_a_row_without_a_length_is_refused(self, tmp_path):
        text = self.TEXT.replace("1 3 -5.734 1600.0", "1 3 -5.734")
        with pytest.raises(DataError) as caught:
            read_krumm(write(tmp_path, text))
        assert caught.value.code == "data.krumm_row_too_short"


class TestDirections:
    TEXT = """\
[Coordinates]
A 0 0
B 100 0
C 0 100
P 40 40

[Datum]
fix xA yA xB yB xC yC

[Directions]
P A 250.0000 0.0010
P B  50.0000
P C 150.0000
"""

    def test_a_set_shares_a_cluster_and_a_setup(self, tmp_path):
        """Two ids, and they are not the same id.

        The cluster is what FR-104 holds the set's correlation on; the *setup*
        is what the adjustment keys the orientation unknown on. Without the
        setup id every direction is read as an absolute azimuth and the network
        solves to coordinates that are wrong by the unmodelled orientation.
        """
        report = read_krumm(write(tmp_path, self.TEXT))
        directions = [
            observation
            for observation in report.network.observations.values()
            if observation.type is ObservationType.DIRECTION
        ]
        assert len(directions) == 3
        assert {observation.setup_id for observation in directions} == {"P"}
        assert {observation.cluster_id for observation in directions} == {"set:P"}

        (cluster,) = report.network.clusters.values()
        assert cluster.kind is ClusterKind.DIRECTION_SET
        assert len(cluster.observation_ids) == 3

    def test_the_approximate_orientation_is_not_an_observation(self, tmp_path):
        text = self.TEXT + "\n[ApproximateOrientation]\nP 339.4090\n"
        report = read_krumm(write(tmp_path, text))
        assert len(report.network.observations) == 3


class TestFreeNetworks:
    def test_the_names_after_free_are_the_datum_stations(self, tmp_path):
        text = TRILATERATION.replace("fix xA yA xB yB", "free xA yA xB yB xC yC")
        report = read_krumm(write(tmp_path, text))
        assert report.free is True
        assert report.datum_stations == ("A", "B", "C")
        assert report.network.stations["A"].constraint.mode is not ConstraintMode.FIXED

    def test_a_bare_free_means_every_station(self, tmp_path):
        text = TRILATERATION.replace("fix xA yA xB yB", "free")
        report = read_krumm(write(tmp_path, text))
        assert report.free is True
        assert report.datum_stations is None

    def test_a_free_datum_over_unequal_components_is_refused(self, tmp_path):
        text = TRILATERATION.replace("fix xA yA xB yB", "free xA yA xB")
        with pytest.raises(DataError) as caught:
            read_krumm(write(tmp_path, text))
        assert caught.value.code == "data.krumm_free_datum_partial"


class TestRefusals:
    """Every one of these is a file GeoComp will not read, said by name.

    The alternative -- reading the file without the part it cannot represent --
    produces a different network that then gets compared against a published
    answer for a network nobody adjusted.
    """

    def test_a_dynamic_datum(self, tmp_path):
        text = TRILATERATION.replace("fix xA yA xB yB", "dyn xA yA")
        with pytest.raises(DataError) as caught:
            read_krumm(write(tmp_path, text))
        assert caught.value.code == "data.krumm_dynamic_datum_unsupported"

    def test_a_section_that_describes_something_unrepresentable(self, tmp_path):
        text = TRILATERATION + "\n[CorrelatedDistances]\nA B 100.0\n"
        with pytest.raises(DataError) as caught:
            read_krumm(write(tmp_path, text))
        assert caught.value.code == "data.krumm_section_unsupported"
        assert caught.value.context["section"] == "[CorrelatedDistances]"

    def test_a_section_nobody_has_seen(self, tmp_path):
        text = TRILATERATION + "\n[Nonsense]\nA B 1\n"
        with pytest.raises(DataError) as caught:
            read_krumm(write(tmp_path, text))
        assert caught.value.code == "data.krumm_section_unknown"

    def test_instrument_and_target_heights(self, tmp_path):
        text = """\
[Coordinates]
N 0 0 100
1 100 0 110

[Datum]
fix x1 y1 z1

[SpatialDistances]
N 1 100.4988 0.005 1.600 1.572
"""
        with pytest.raises(DataError) as caught:
            read_krumm(write(tmp_path, text))
        assert caught.value.code == "data.krumm_setup_heights_unsupported"

    def test_an_observation_reaching_a_station_with_no_coordinates(self, tmp_path):
        """Krumm's traverses do this on purpose; GNU Gama excludes them too."""
        text = TRILATERATION.replace("A C 141.421", "A Z 141.421")
        with pytest.raises(DataError) as caught:
            read_krumm(write(tmp_path, text))
        assert caught.value.code == "data.krumm_observation_station_unknown"
        assert caught.value.context["received"] == ["Z"]


class TestComments:
    def test_a_hash_inside_a_name_is_not_a_comment(self, tmp_path):
        """``Leick54`` has stations called ``Six#Mile`` and ``Trav-14``."""
        text = """\
[Coordinates]
Six#Mile 0 0     % the name really does contain a hash
Trav-14  100 0
# a whole-line comment

[Datum]
fix Six#Mile

[Distances]
Six#Mile Trav-14 100.000 0.005
"""
        report = read_krumm(write(tmp_path, text))
        assert set(report.network.stations) == {"Six#Mile", "Trav-14"}
        (distance,) = report.network.observations.values()
        assert distance.stations == ("Six#Mile", "Trav-14")


class TestDimension:
    def test_a_plane_network_is_two_dimensional(self, tmp_path):
        assert read_krumm(write(tmp_path, TRILATERATION)).dimension == 2

    def test_a_spatial_distance_makes_it_three(self, tmp_path):
        text = """\
[Coordinates]
A 0 0 100
B 100 0 110

[Datum]
fix xA yA zA

[SpatialDistances]
A B 100.4988 0.005
"""
        assert read_krumm(write(tmp_path, text)).dimension == 3
