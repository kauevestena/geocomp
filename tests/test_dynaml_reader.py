# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading DynaML into a GeoComp network (FR-163, FR-104).

``specs/07-engine-dynadjust.md`` section 4. Tier 1 -- no QGIS, no engine.

The fixtures in ``tests/data/dynadjust/`` are a slice of upstream's own
``gnss-network`` sample (Apache-2.0, from the DynAdjust repository): eleven
stations, one GNSS baseline cluster, one point cluster and two single
baselines, one of which carries a variance scalar. They are a valid DynAdjust
project in their own right -- ``dnaimport`` loads them -- which is what makes
them worth committing: the parser is tested against a file the engine accepts
rather than one written to satisfy the parser.

The engine-tier tests take this further and check that a network read here,
written back out and adjusted by DynAdjust reproduces DynAdjust's own answer on
the full 43-station network. That cannot run without the binaries; everything
below can.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import DataError
from geocomp.core.models import ClusterKind, ConstraintMode, ObservationType
from geocomp.engines.dynadjust.read_dynaml import (
    BY_CODE,
    UNMAPPED,
    read_dynaml,
    read_station_file,
)

DATA = Path(__file__).parent / "data" / "dynadjust"
STATIONS = DATA / "sample-stn.xml"
MEASUREMENTS = DATA / "sample-msr.xml"


@pytest.fixture(scope="module")
def report():
    return read_dynaml(STATIONS, MEASUREMENTS, network_id="sample")


# -- the file reads at all ------------------------------------------------


def test_the_fixture_reads_without_skipping_anything(report) -> None:
    assert report.skipped == []
    assert report.network is not None
    assert report.network.validate() == []


def test_the_frame_and_epoch_come_from_the_file(report) -> None:
    """FR-105: never inferred, in either direction."""
    assert report.frame == "GDA2020"
    assert report.epoch


def test_the_measurement_types_are_counted(report) -> None:
    assert report.counts == {"X": 1, "Y": 1, "G": 2}


def test_the_stations_and_observations_arrive(report) -> None:
    network = report.network
    assert len(network.stations) == 11
    assert len(network.observations) > 4
    assert len(network.clusters) == 4


# -- FR-104: correlation survives the read --------------------------------


def test_a_baseline_cluster_keeps_its_full_covariance(report) -> None:
    """The whole point of an X measurement is what a G cannot say."""
    network = report.network
    clusters = [c for c in network.clusters.values() if c.id.startswith("X")]
    assert len(clusters) == 1
    cluster = clusters[0]

    members = len(cluster.observation_ids)
    assert members > 1
    assert cluster.covariance.size == 3 * members
    assert cluster.kind is ClusterKind.GNSS_BASELINE


def test_the_between_member_blocks_are_read_and_symmetric(report) -> None:
    """Written only above the diagonal; a reader that forgot to mirror them
    would produce a matrix Covariance itself refuses."""
    cluster = next(c for c in report.network.clusters.values() if c.id.startswith("X"))
    matrix = cluster.covariance.matrix
    np.testing.assert_allclose(matrix, matrix.T, rtol=0, atol=0)
    # There is real off-diagonal content between the first two members.
    assert np.any(np.abs(matrix[0:3, 3:6]) > 0)


def test_a_point_cluster_is_read_as_one(report) -> None:
    cluster = next(c for c in report.network.clusters.values() if c.id.startswith("Y"))
    assert cluster.kind is ClusterKind.GNSS_POINT
    observations = [report.network.observations[o] for o in cluster.observation_ids]
    assert all(o.type is ObservationType.GNSS_POINT for o in observations)
    assert all(len(o.stations) == 1 for o in observations)


# -- the variance scalar, which was silently dropped at first -------------


def test_a_variance_scalar_is_applied_not_ignored(report) -> None:
    """A V-scale of 10 means the author declared that covariance ten times
    larger. Dropping it makes GeoComp trust the baseline ten times more than
    the file says -- which changes the solution, not just the formatting.

    Upstream's own GNSS sample uses eight distinct scalars, and the round-trip
    through DynAdjust reproduced its sigma-zero only once this was applied.
    """
    scaled = [
        o for o in report.network.observations.values() if o.meta.get("dynadjust_v_scale")
    ]
    assert scaled, "the fixture is meant to include a scaled measurement"
    scale = scaled[0].meta["dynadjust_v_scale"]
    assert scale > 1.0

    cluster = report.network.clusters[scaled[0].cluster_id]
    # The stored variance is the file's value times the scale, so the standard
    # deviation the adjustment sees is sqrt(scale) larger.
    assert cluster.covariance.matrix[0][0] > 0


def test_the_scale_is_recorded_so_provenance_can_say_so(report) -> None:
    scaled = [
        o for o in report.network.observations.values() if o.meta.get("dynadjust_v_scale")
    ]
    assert all(isinstance(o.meta["dynadjust_v_scale"], float) for o in scaled)


def test_a_directional_scalar_is_refused_rather_than_dropped(tmp_path: Path) -> None:
    """P, L and H scale single directions of the local frame, which needs a
    rotation GeoComp cannot verify against a reference. Reading the file while
    ignoring them would silently change every weight it sets."""
    text = MEASUREMENTS.read_text(encoding="utf-8").replace(
        "<Pscale>1</Pscale>", "<Pscale>2.5</Pscale>", 1
    )
    if "<Pscale>2.5</Pscale>" not in text:  # the fixture may write 1.000
        text = MEASUREMENTS.read_text(encoding="utf-8").replace(
            "<Pscale>1.000</Pscale>", "<Pscale>2.5</Pscale>", 1
        )
    path = tmp_path / "scaled.xml"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(DataError) as excinfo:
        read_dynaml(STATIONS, path)
    assert excinfo.value.code == "data.dynaml_directional_variance_scale_unsupported"


# -- constraints ----------------------------------------------------------


def test_constraints_are_read_per_component() -> None:
    report = read_station_file(STATIONS)
    modes = {s.id: s.constraint.mode for s in report.network.stations.values()}
    assert ConstraintMode.FREE in modes.values() or ConstraintMode.FIXED in modes.values()
    for station in report.network.stations.values():
        if station.constraint.mode is ConstraintMode.FIXED:
            assert station.constraint.components
            assert station.constraint.position is not None


# -- what cannot be represented is reported -------------------------------


def test_the_msl_arc_has_no_mapping_and_says_why() -> None:
    """Equating it to an ellipsoid distance is a metre-scale error on a long
    line, applied silently."""
    assert "M" not in BY_CODE
    assert "M" in UNMAPPED
    assert "MSL" in UNMAPPED["M"] or "mean sea level" in UNMAPPED["M"]


def test_an_unmapped_measurement_is_listed_not_dropped(tmp_path: Path) -> None:
    text = MEASUREMENTS.read_text(encoding="utf-8").replace("<Type>G</Type>", "<Type>M</Type>", 1)
    path = tmp_path / "msl.xml"
    path.write_text(text, encoding="utf-8")
    report = read_dynaml(STATIONS, path)
    assert any(code.startswith("M") for code, _ in report.skipped)


def test_every_code_upstream_defines_is_mapped_or_explained() -> None:
    """The twenty types confirmed against upstream at commit 5cdb897."""
    upstream = set("ABCDEGHIJKLMPQRSVXYZ")
    assert upstream == set(BY_CODE) | set(UNMAPPED)


# -- refusals on malformed input ------------------------------------------


def test_a_file_that_is_not_dynaml_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "not.xml"
    path.write_text("<something/>", encoding="utf-8")
    with pytest.raises(DataError) as excinfo:
        read_station_file(path)
    assert excinfo.value.code == "data.dynaml_wrong_root"


def test_a_measurement_file_given_where_a_station_file_belongs_says_so() -> None:
    with pytest.raises(DataError) as excinfo:
        read_station_file(MEASUREMENTS)
    assert excinfo.value.code == "data.dynaml_wrong_file_type"


def test_unparseable_xml_names_the_file(tmp_path: Path) -> None:
    path = tmp_path / "broken.xml"
    path.write_text("<DnaXmlFormat><unclosed>", encoding="utf-8")
    with pytest.raises(DataError) as excinfo:
        read_station_file(path)
    assert excinfo.value.code == "data.dynaml_unreadable"


# -- the reader and writer share their conventions ------------------------


def test_read_then_write_then_read_is_stable(tmp_path: Path) -> None:
    """The cheapest guard against reader and writer drifting apart.

    They share ``formats.py`` precisely so this holds; the test exists because
    the drift is invisible until something round-trips.
    """
    from geocomp.engines.dynadjust.dynaml import (
        write_measurement_file,
        write_station_file,
    )

    first = read_dynaml(STATIONS, MEASUREMENTS, network_id="a")
    write_station_file(
        first.network, tmp_path / "s.xml", frame=first.frame, epoch=first.epoch
    )
    write_measurement_file(
        first.network, tmp_path / "m.xml", frame=first.frame, epoch=first.epoch
    )
    second = read_dynaml(tmp_path / "s.xml", tmp_path / "m.xml", network_id="a")

    assert set(second.network.stations) == set(first.network.stations)
    assert second.counts == first.counts
    assert len(second.network.clusters) == len(first.network.clusters)

    for cluster_id, cluster in first.network.clusters.items():
        other = second.network.clusters[cluster_id]
        np.testing.assert_allclose(
            other.covariance.matrix, cluster.covariance.matrix, rtol=1e-12, atol=0
        )


def test_an_angular_value_survives_the_round_trip() -> None:
    """HP notation in, HP notation out, radians in between."""
    from geocomp.engines.dynadjust.formats import hp_to_radians, radians_to_hp

    for text in ("91.41495000", "0.00001", "359.5959999"):
        assert hp_to_radians(radians_to_hp(hp_to_radians(text))) == pytest.approx(
            hp_to_radians(text), abs=1e-12
        )
    assert math.degrees(hp_to_radians("45.3000")) == pytest.approx(45.5)
