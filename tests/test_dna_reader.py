# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading DynAdjust's column-oriented DNA files (FR-163).

``specs/07-engine-dynadjust.md`` section 4.1. GeoComp writes DynaML but reads
both, because a user with an existing DynAdjust project has ``.stn`` and
``.msr`` files and should not have to convert them before GeoComp will show
them.

**The strongest test here is that the two readers agree.** DNA and DynaML carry
the same network in formats with nothing in common -- one fixed-width columns,
the other XML, with different cluster layouts -- so reading upstream's sample
both ways and comparing is close to an independent implementation check. It is
also how the column mistakes below were found, since a wrong column reads as
data rather than as a parse failure.

Fixtures are a slice of upstream's `gnss-network` sample (Apache-2.0, see
THIRD_PARTY.md), and `dnaimport` loads them, so they are files the engine
accepts rather than files written to satisfy the parser.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import DataError
from geocomp.core.models import ClusterKind
from geocomp.engines.dynadjust.read_dna import read_dna, read_dna_stations
from geocomp.engines.dynadjust.read_dynaml import read_dynaml

DATA = Path(__file__).parent / "data" / "dynadjust"


@pytest.fixture(scope="module")
def dna():
    return read_dna(DATA / "sample.stn", DATA / "sample.msr", network_id="s")


@pytest.fixture(scope="module")
def dynaml():
    return read_dynaml(DATA / "sample-stn.xml", DATA / "sample-msr.xml", network_id="s")


# -- the header (Guide Table B.1) -----------------------------------------


def test_the_header_fields_land_in_the_right_columns(dna) -> None:
    """Guessed boundaries put the frame at 'DA2020    01.0'.

    Wrong in the way fixed-width parsing is always wrong: it reads as data, not
    as a failure, so nothing downstream notices until a frame comparison
    silently disagrees.
    """
    assert dna.frame == "GDA2020"
    assert dna.epoch == "01.01.2020"


def test_a_file_without_the_dna_header_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "bare.stn"
    path.write_text("STN1                 FFF XYZ 1.0 2.0 3.0\n", encoding="utf-8")
    with pytest.raises(DataError) as excinfo:
        read_dna_stations(path)
    assert excinfo.value.code == "data.dna_header_missing"


# -- the two readers must agree -------------------------------------------


def test_both_readers_find_the_same_measurements(dna, dynaml) -> None:
    assert dna.counts == dynaml.counts == {"X": 1, "Y": 1, "G": 2}
    assert dna.skipped == [] and dynaml.skipped == []


def test_both_readers_find_the_same_stations(dna, dynaml) -> None:
    assert set(dna.network.stations) <= set(dynaml.network.stations)
    assert len(dna.network.clusters) == len(dynaml.network.clusters)


def test_the_cluster_covariances_are_identical(dna, dynaml) -> None:
    """Bit-identical, from two formats with nothing in common.

    This is what makes the pair a real check rather than two views of the same
    parser: a column mistake in one cannot survive agreement with the other.
    """
    for code in ("X", "Y"):
        a = next(c for c in dna.network.clusters.values() if c.id.startswith(code))
        b = next(c for c in dynaml.network.clusters.values() if c.id.startswith(code))
        assert a.covariance.size == b.covariance.size
        np.testing.assert_array_equal(a.covariance.matrix, b.covariance.matrix)


# -- the DNA cluster layout, which differs from DynaML's ------------------


def test_a_cluster_is_one_cluster_not_one_per_member(dna) -> None:
    """DNA repeats the measurement code on every member's header line.

    Only the first carries the count, and a member is three component lines
    followed by three per *subsequent* member for the cross-covariance. A
    reader that assumed three lines per member walks into the next block: the
    first draft turned one X cluster into four and one Y into six, and only the
    DynaML reader's disagreement made that visible.
    """
    x = [c for c in dna.network.clusters.values() if c.id.startswith("X")]
    y = [c for c in dna.network.clusters.values() if c.id.startswith("Y")]
    assert len(x) == 1 and len(y) == 1
    assert len(x[0].observation_ids) > 1
    assert x[0].kind is ClusterKind.GNSS_BASELINE
    assert y[0].kind is ClusterKind.GNSS_POINT


def test_the_cross_covariance_blocks_are_read(dna) -> None:
    """Off-diagonal content between members, which is the point of a cluster."""
    cluster = next(c for c in dna.network.clusters.values() if c.id.startswith("X"))
    matrix = cluster.covariance.matrix
    assert np.any(np.abs(matrix[0:3, 3:6]) > 0)
    np.testing.assert_allclose(matrix, matrix.T, rtol=0, atol=0)


def test_the_covariance_is_positive_semidefinite(dna) -> None:
    """Reading the cross blocks from the value column instead of the variance
    columns produces a matrix that is not, which is how that bug was caught --
    Covariance refused it rather than a wrong answer surviving."""
    for cluster in dna.network.clusters.values():
        eigenvalues = np.linalg.eigvalsh(cluster.covariance.matrix)
        assert eigenvalues.min() > -1e-12


# -- the variance scalar, in this format too ------------------------------


def test_the_variance_scalar_is_applied(dna) -> None:
    scaled = [
        o for o in dna.network.observations.values() if o.meta.get("dynadjust_v_scale")
    ]
    assert scaled
    assert all(o.meta["dynadjust_v_scale"] > 1.0 for o in scaled)


def test_a_directional_scalar_is_refused(tmp_path: Path) -> None:
    text = DATA.joinpath("sample.msr").read_text(encoding="utf-8")
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line[:1] in "GXY" and line[1:2] == " ":
            lines[index] = line[:72] + f"{2.5:>10.2f}" + line[82:]
            break
    path = tmp_path / "scaled.msr"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(DataError) as excinfo:
        read_dna(DATA / "sample.stn", path)
    assert excinfo.value.code == "data.dna_directional_variance_scale_unsupported"


# -- line endings ---------------------------------------------------------


def test_crlf_and_lf_are_both_read(tmp_path: Path) -> None:
    """Upstream ships a CRLF .stn beside an LF .msr.

    A reader that trusts one strips the last character of every fixed-width
    field on the other, which for a station name is a different station.
    """
    original = DATA.joinpath("sample.stn").read_text(encoding="utf-8")
    crlf = tmp_path / "crlf.stn"
    crlf.write_bytes(original.replace("\n", "\r\n").encode("utf-8"))

    plain = read_dna_stations(DATA / "sample.stn")
    windows = read_dna_stations(crlf)
    assert set(plain.network.stations) == set(windows.network.stations)
    assert all(not name.endswith("\r") for name in windows.network.stations)


# -- station coordinates --------------------------------------------------


def test_stations_read_with_their_coordinates(dna) -> None:
    assert len(dna.network.stations) == 10
    for station in dna.network.stations.values():
        assert station.approx_position is not None
        assert any(q.value != 0.0 for q in station.approx_position.values)


# -- the terrestrial half, which the GNSS sample never reaches -------------


TERRESTRIAL = DATA / "output"


@pytest.fixture(scope="module")
def terrestrial_dna():
    return read_dna(
        TERRESTRIAL / "terrestrial.stn", TERRESTRIAL / "terrestrial.msr", network_id="t"
    )


@pytest.fixture(scope="module")
def terrestrial_dynaml():
    return read_dynaml(
        TERRESTRIAL / "terrestrial-stn.xml",
        TERRESTRIAL / "terrestrial-msr.xml",
        network_id="t",
    )


def _by_type(report):
    return {(o.type.name, o.stations): o for o in report.network.observations.values()}


class TestTheTerrestrialMeasurements:
    """The half of ``read_dna.py`` that had no fixture until the pre-P7 review.

    ``sample.stn``/``sample.msr`` is upstream's GNSS network: every measurement
    in it is an ``X``, ``Y`` or ``G`` cluster of Cartesian components, so the
    angle columns, the linear value and deviation columns, the direction-set
    block and the setup-height columns were all unreachable from the suite. The
    module sat at 65% and **four defects were in the missed lines**, each of
    which this class would have caught the day it was written:

    1. The HP string built from the three angle columns kept the seconds' own
       decimal point -- ``171.2033.58000`` -- so *every* angular measurement in
       a DNA file was refused as malformed.
    2. The linear value and deviation were read from columns 63-82 and 83-102;
       they are 63-76 and 91-99. The deviation field started eight columns early
       and read ``0.005  1``: the deviation, and the first digit of the
       instrument height.
    3. Instrument and target heights went into ``Observation.meta`` as bare
       floats, where the adjustment never looks -- the defect P6 found and fixed
       on the DynaML side, left standing here.
    4. Every direction after the first in a set came back with an **empty**
       target station: they carry it in columns 43-62, not 23-42.

    ``terrestrial-{stn,msr}.xml`` are ours; ``terrestrial.{stn,msr}`` are what
    ``dnaimport --export-dna-files`` made of them, so the columns are DynAdjust's
    own and ``scripts/check_dynadjust_fixtures.py`` re-checks them against a
    live engine.
    """

    def test_every_terrestrial_type_is_read(self, terrestrial_dna):
        assert terrestrial_dna.counts == {"D": 1, "S": 1, "V": 1, "A": 1, "L": 1, "H": 1}
        assert terrestrial_dna.skipped == []

    def test_the_two_readers_agree_observation_for_observation(
        self, terrestrial_dna, terrestrial_dynaml
    ):
        """The check that makes this a real fixture rather than a second view of
        one parser: two formats with nothing in common, read to the same
        network."""
        dna_observations, xml_observations = _by_type(terrestrial_dna), _by_type(terrestrial_dynaml)
        assert set(dna_observations) == set(xml_observations)
        for key, observation in dna_observations.items():
            other = xml_observations[key]
            assert observation.values[0].value == pytest.approx(other.values[0].value, abs=1e-12)
            assert observation.values[0].std_dev == pytest.approx(
                other.values[0].std_dev, rel=1e-12
            )
            assert observation.values[0].unit is other.values[0].unit

    def test_an_angle_is_assembled_from_its_three_columns(self, terrestrial_dna):
        """Defect 1. ``171 20 33.5800`` in columns 77-80, 81-82 and 83-90."""
        angle = _by_type(terrestrial_dna)[("HORIZONTAL_ANGLE", ("OCC", "RO", "TGT2"))]
        expected = math.radians(171.0 + 20.0 / 60.0 + 33.58 / 3600.0)
        assert angle.values[0].value == pytest.approx(expected, abs=1e-12)

    def test_an_angular_deviation_is_seconds_of_arc(self, terrestrial_dna):
        angle = _by_type(terrestrial_dna)[("HORIZONTAL_ANGLE", ("OCC", "RO", "TGT2"))]
        assert angle.values[0].std_dev == pytest.approx(math.radians(3.5 / 3600.0), rel=1e-12)

    def test_a_linear_value_and_its_deviation_come_from_the_right_columns(
        self, terrestrial_dna
    ):
        """Defect 2. The row also carries setup heights, which is what made the
        old deviation field read ``0.005  1`` and refuse the file."""
        distance = _by_type(terrestrial_dna)[("SLOPE_DISTANCE", ("OCC", "TGT1"))]
        assert distance.values[0].value == pytest.approx(6714.9420, abs=1e-9)
        assert distance.values[0].std_dev == pytest.approx(0.005, rel=1e-12)

    def test_a_negative_linear_value_keeps_its_sign(self, terrestrial_dna):
        difference = _by_type(terrestrial_dna)[("HEIGHT_DIFFERENCE", ("OCC", "TGT2"))]
        assert difference.values[0].value == pytest.approx(-15.0, abs=1e-9)

    def test_setup_heights_reach_the_observation_not_the_metadata(self, terrestrial_dna):
        """Defect 3. In ``meta`` the adjustment never sees them, and a slope
        distance measured instrument-to-reflector is reduced as though both
        stood on their marks."""
        distance = _by_type(terrestrial_dna)[("SLOPE_DISTANCE", ("OCC", "TGT1"))]
        assert distance.instrument_height is not None
        assert distance.instrument_height.value == pytest.approx(1.523)
        assert distance.target_height.value == pytest.approx(1.684)
        assert distance.height_offset == pytest.approx(1.684 - 1.523)

    def test_a_type_the_heights_do_not_move_does_not_get_them(self, terrestrial_dna):
        angle = _by_type(terrestrial_dna)[("HORIZONTAL_ANGLE", ("OCC", "RO", "TGT2"))]
        assert angle.instrument_height is None and angle.target_height is None

    def test_a_real_height_on_an_unaffected_type_is_refused_not_dropped(self, tmp_path):
        """The DynaML reader's rule, applied here: a blank or a zero is the
        format's filler; a metre of instrument height on a direction is a metre
        of error nobody would see."""
        rows = (TERRESTRIAL / "terrestrial.msr").read_text(encoding="utf-8").splitlines()
        patched = []
        for row in rows:
            if row.startswith("L "):
                # Columns 100-106 are the instrument height. The exported row is
                # already padded past them, so this overwrites rather than
                # appends -- putting the value where the reader looks.
                row = f"{row:<113}"
                row = row[:99] + f"{1.500:>7.3f}" + row[106:]
            patched.append(row)
        path = tmp_path / "heights.msr"
        path.write_text("\n".join(patched) + "\n", encoding="utf-8")
        with pytest.raises(DataError) as caught:
            read_dna(TERRESTRIAL / "terrestrial.stn", path, network_id="t")
        assert caught.value.code == "data.dna_setup_height_on_an_unaffected_type"

    def test_a_direction_set_is_one_cluster_of_three(self, terrestrial_dna):
        network = terrestrial_dna.network
        assert len(network.clusters) == 1
        cluster = next(iter(network.clusters.values()))
        assert cluster.kind is ClusterKind.DIRECTION_SET
        assert len(cluster.observation_ids) == 3

    def test_every_direction_names_a_station_that_exists(self, terrestrial_dna):
        """Defect 4, and the shape of it: the observations were built without
        complaint, pointing at a station named ``''``."""
        network = terrestrial_dna.network
        directions = [o for o in network.observations.values() if o.type.name == "DIRECTION"]
        assert len(directions) == 3
        for observation in directions:
            assert observation.stations[0] == "OCC"
            assert observation.stations[1] in network.stations, observation.stations

    def test_the_reference_direction_is_zero_and_the_others_are_not(self, terrestrial_dna):
        by_target = {
            o.stations[1]: o.values[0].value
            for o in terrestrial_dna.network.observations.values()
            if o.type.name == "DIRECTION"
        }
        assert by_target["RO"] == pytest.approx(0.0, abs=1e-12)
        assert by_target["TGT1"] == pytest.approx(
            math.radians(63.0 + 36.0 / 60.0 + 12.47 / 3600.0), abs=1e-12
        )
        assert by_target["TGT2"] == pytest.approx(
            math.radians(171.0 + 20.0 / 60.0 + 33.58 / 3600.0), abs=1e-12
        )

    def test_the_stations_read_with_their_hp_coordinates(self, terrestrial_dna):
        station = terrestrial_dna.network.stations["OCC"]
        latitude = station.approx_position.values[0].value
        assert math.degrees(latitude) == pytest.approx(-(37.0 + 47.0 / 60.0 + 48.0 / 3600.0))
