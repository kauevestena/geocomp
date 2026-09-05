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
