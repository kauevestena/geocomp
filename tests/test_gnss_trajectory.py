# SPDX-License-Identifier: GPL-2.0-or-later
"""A processed run as a trajectory (FR-357, FR-356).

``specs/11-module-gnss.md`` section 4.3 and ``specs/08-engine-rtklib.md``
section 7.

**The centrepiece is :class:`TestTheFourFormatsAgree`.** The committed ``.pos``
corpus is *one solution written four ways* -- geodetic, geodetic in degrees,
minutes and seconds, geocentric, and as an ENU baseline -- so a trajectory built
from any of them must be the same trajectory. That identity is what makes the
per-format handling evidence rather than assertion: each format needs a
different operation to yield a coordinate and a local covariance, and three of
the four ways of getting one of them wrong leave every number looking
reasonable.

One of them did. The first version of ``_from_cartesian`` passed ``(n, e, u)``
to :func:`ecef_to_enu_covariance`, whose rotation writes east, north and up in
*that* order -- so it relabelled rows 0 and 1 rather than permuting them, and
the north and east standard deviations came out swapped. Nothing but this
comparison would have noticed.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from geocomp.core.errors import DataError
from geocomp.core.techniques.gnss.trajectory import (
    LOCAL_LABELS,
    TrajectoryPoint,
    reorder_to_local,
)
from geocomp.core.uncertainty import Covariance
from geocomp.core.units import Unit
from geocomp.engines.rtklib.read_pos import PosFormat, read_pos
from geocomp.engines.rtklib.trajectory import trajectory_from_solution
from tests.conftest import REPO_ROOT

POS = REPO_ROOT / "tests" / "data" / "rtklib" / "pos"
FORMATS = ("llh", "llh-dms", "xyz", "enu")


@pytest.fixture(scope="module")
def trajectories() -> dict[str, list[TrajectoryPoint]]:
    return {
        name: trajectory_from_solution(read_pos(POS / f"{name}.pos")) for name in FORMATS
    }


class TestEveryEpochBecomesAPoint:
    @pytest.mark.parametrize("name", FORMATS)
    def test_the_count_matches_the_file(self, name, trajectories):
        assert len(trajectories[name]) == len(read_pos(POS / f"{name}.pos").epochs)

    @pytest.mark.parametrize("name", FORMATS)
    def test_every_point_is_in_the_local_horizon(self, name, trajectories):
        """The whole reason this type exists: one frame, whatever the engine
        wrote, so a `sigma_n` column means one thing across every file."""
        for point in trajectories[name]:
            assert point.covariance.labels == LOCAL_LABELS
            assert point.covariance.units == (Unit.METRE,) * 3

    @pytest.mark.parametrize("name", FORMATS)
    def test_the_quality_travels_with_the_position(self, name, trajectories):
        """FR-603. A coordinate whose solution status is not beside it is one
        whose accuracy is unstated by two orders of magnitude."""
        epochs = read_pos(POS / f"{name}.pos").epochs
        for point, epoch in zip(trajectories[name], epochs, strict=True):
            assert point.quality.time == epoch.time
            assert point.quality.status == epoch.status.name
            assert point.quality.satellites == epoch.satellites

    @pytest.mark.parametrize("name", FORMATS)
    def test_the_position_is_where_the_survey_was(self, name, trajectories):
        """The fixtures are RTKLIB's own Japanese test data, near Tokyo. A
        conversion that lost a factor of 57.3 or a sign would land in the Gulf
        of Guinea and pass every other test here."""
        for point in trajectories[name]:
            assert 35.0 < point.latitude_degrees < 35.5
            assert 139.0 < point.longitude_degrees < 140.0
            assert 0.0 < point.height < 200.0


class TestTheFourFormatsAgree:
    """One solution written four ways is one trajectory."""

    def test_every_format_puts_the_last_epoch_in_the_same_place(self, trajectories):
        reference = trajectories["llh"][-1]
        for name in FORMATS:
            point = trajectories[name][-1]
            # 1e-8 degrees is about 1 mm, which is the precision the files are
            # printed to; the ENU round trip through ECEF is the loosest of the
            # four and still lands inside it.
            assert point.latitude_degrees == pytest.approx(
                reference.latitude_degrees, abs=1e-8
            ), name
            assert point.longitude_degrees == pytest.approx(
                reference.longitude_degrees, abs=1e-8
            ), name
            assert point.height == pytest.approx(reference.height, abs=1e-3), name

    def test_every_format_gives_the_same_north_east_and_up_sigmas(self, trajectories):
        """The check that caught the relabel-instead-of-permute defect. A
        rotation applied with the wrong labels swaps north and east and changes
        nothing else -- both numbers stay the right order of magnitude, and the
        map still draws."""
        reference = trajectories["llh"][-1].sigmas
        for name in FORMATS:
            assert trajectories[name][-1].sigmas == pytest.approx(
                reference, abs=5e-5
            ), name

    def test_the_geocentric_covariance_really_was_rotated(self, trajectories):
        """Guards the test above: were the ECEF matrix passed through
        unrotated, it would have to coincide with the local one by accident."""
        ecef = read_pos(POS / "xyz.pos").last().covariance
        local = trajectories["xyz"][-1].covariance
        assert ecef.labels == ("x", "y", "z")
        assert not np.allclose(np.diag(ecef.matrix), np.diag(local.matrix), atol=1e-8)

    def test_the_sexagesimal_file_is_not_read_as_seven_numbers(self, trajectories):
        """``-g`` writes the latitude and longitude as degrees, minutes and
        seconds, so the raw position is seven columns whose last three are a
        longitude's minutes, its seconds and the height."""
        raw = read_pos(POS / "llh-dms.pos").last().position
        assert len(raw) == 7
        assert trajectories["llh-dms"][-1].latitude_degrees == pytest.approx(
            trajectories["llh"][-1].latitude_degrees, abs=1e-8
        )


class TestUncertainty:
    def test_drms_is_the_horizontal_root_sum_of_squares(self, trajectories):
        for point in trajectories["llh"]:
            north, east, _up = point.sigmas
            assert point.drms == pytest.approx(math.hypot(north, east))

    def test_the_sigmas_are_the_covariance_diagonal(self, trajectories):
        for point in trajectories["xyz"]:
            expected = np.sqrt(np.diag(point.covariance.matrix))
            assert point.sigmas == pytest.approx(tuple(float(v) for v in expected))

    def test_the_correlations_survive_the_rotation(self, trajectories):
        """FR-201. A covariance reduced to three standard deviations on the way
        into a layer would make every error ellipse drawn from it a circle."""
        matrix = trajectories["xyz"][-1].covariance.matrix
        off_diagonal = matrix[~np.eye(3, dtype=bool)]
        assert np.any(np.abs(off_diagonal) > 1e-9)


class TestTheFrameIsEnforced:
    def test_a_point_refuses_a_covariance_in_another_frame(self):
        """A point whose covariance is geocentric would give a `sigma_n` column
        holding an X uncertainty -- right order of magnitude, wrong axis."""
        ecef = read_pos(POS / "xyz.pos").last().covariance
        with pytest.raises(DataError) as raised:
            TrajectoryPoint(
                latitude=0.6,
                longitude=2.4,
                height=70.0,
                covariance=ecef,
                quality=trajectory_from_solution(read_pos(POS / "llh.pos"))[0].quality,
            )
        assert raised.value.code == "data.trajectory_point_frame"

    def test_reordering_refuses_a_geocentric_covariance(self):
        """A permutation is not a rotation, and confusing the two is exactly
        how north and east get swapped."""
        ecef = read_pos(POS / "xyz.pos").last().covariance
        with pytest.raises(DataError) as raised:
            reorder_to_local(ecef)
        assert raised.value.code == "data.trajectory_covariance_not_local"

    def test_reordering_permutes_rather_than_recomputes(self):
        """The ENU path's operation: the same three axes in another order, so
        every entry must survive exactly, correlations included."""
        enu = read_pos(POS / "enu.pos").last().covariance
        assert enu.labels == ("e", "n", "u")
        local = reorder_to_local(enu)
        assert local.labels == LOCAL_LABELS
        assert local.matrix[0, 0] == enu.matrix[1, 1]
        assert local.matrix[1, 1] == enu.matrix[0, 0]
        assert local.matrix[0, 1] == enu.matrix[1, 0]
        assert local.matrix[2, 2] == enu.matrix[2, 2]

    def test_an_already_local_covariance_is_returned_unchanged(self):
        matrix = np.diag([1.0, 2.0, 3.0])
        covariance = Covariance(
            matrix=matrix, labels=LOCAL_LABELS, units=(Unit.METRE,) * 3
        )
        assert reorder_to_local(covariance) is covariance


class TestTheEnuFormatNeedsItsBase:
    def test_an_enu_solution_without_a_reference_refuses(self, tmp_path):
        """Three offsets from nowhere are not a position, and placing them at
        the geocentre would put the trajectory off the coast of Africa rather
        than failing."""
        text = (POS / "enu.pos").read_text(encoding="utf-8")
        stripped = "\n".join(
            line for line in text.splitlines() if not line.startswith("% ref pos")
        )
        path = tmp_path / "no-ref.pos"
        path.write_text(stripped + "\n", encoding="utf-8")

        solution = read_pos(path)
        assert solution.format is PosFormat.ENU
        assert solution.reference_position is None
        with pytest.raises(DataError) as raised:
            trajectory_from_solution(solution)
        assert raised.value.code == "data.pos_without_reference_position"
