# SPDX-License-Identifier: GPL-2.0-or-later
"""A GNSS baseline reaches DynAdjust with its covariance intact.

``specs/11-module-gnss.md`` acceptance criterion 4. This is the seam between the
two engine phases -- P7's baseline construction and P6's DynaML writer -- and
nothing exercised it before, because until P7b nothing built a baseline. The
round trip is the check: a cluster written to a file and read back must be the
same matrix, because everything between the two is positional and a
mispositioned block would raise nothing.

It also pins the **frame guard's other half**. The writer means ECEF by
DynAdjust's definition; a locally rotated baseline written into ``<GPSBaseline>``
would be read back as a geocentric one, silently. Getting only one of the two
guards would leave that reachable.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.models import Network, Station
from geocomp.core.techniques.gnss import (
    rotate_baseline_to_local,
    to_cluster,
)
from geocomp.engines.dynadjust.dynaml import write_measurement_file
from geocomp.engines.dynadjust.read_dynaml import ReadReport, read_measurement_file
from geocomp.engines.rtklib.baseline import baseline_from_solution
from geocomp.engines.rtklib.read_pos import read_pos

POS = Path(__file__).parent / "data" / "rtklib" / "pos"

FRAME = "GDA2020"
EPOCH = "01.01.2020"


@pytest.fixture
def baseline():
    return baseline_from_solution(
        read_pos(POS / "xyz.pos"),
        base_station="3040",
        rover_station="0759",
        baseline_id="b1",
    )


def _network(observations, cluster):
    network = Network(id="n")
    for name in ("3040", "0759"):
        network.add_station(Station(id=name, name=name))
    for observation in observations:
        network.add_observation(observation)
    network.add_cluster(cluster)
    network.require_valid()
    return network


class TestOneBaselineBecomesAGMeasurement:
    def test_it_is_written_as_g_not_x(self, baseline, tmp_path):
        observations, cluster = to_cluster([baseline], cluster_id="c1")
        document = write_measurement_file(
            _network(observations, cluster), tmp_path / "m.xml", frame=FRAME, epoch=EPOCH
        )
        assert document.counts.get("G") == 1
        assert "X" not in document.counts

    def test_the_components_are_the_ecef_vector(self, baseline, tmp_path):
        observations, cluster = to_cluster([baseline], cluster_id="c1")
        path = tmp_path / "m.xml"
        write_measurement_file(
            _network(observations, cluster), path, frame=FRAME, epoch=EPOCH
        )
        text = path.read_text(encoding="utf-8")
        assert "2022.7707" in text
        assert "-468.6291" in text
        assert "2610.2891" in text

    def test_the_covariance_survives_the_round_trip(self, baseline, tmp_path):
        """Written and read back, the 3x3 is the same matrix.

        The writer slices by position and the reader reassembles by position,
        so a block placed one row out would come back transposed or displaced
        with nothing raised anywhere between.
        """
        observations, cluster = to_cluster([baseline], cluster_id="c1")
        path = tmp_path / "m.xml"
        write_measurement_file(
            _network(observations, cluster), path, frame=FRAME, epoch=EPOCH
        )

        read_into = Network(id="back")
        report = read_measurement_file(path, read_into, report=ReadReport(network=read_into))
        assert report.skipped == []
        assert len(read_into.clusters) == 1
        returned = next(iter(read_into.clusters.values()))

        # DynaML writes variances to a fixed precision, so this is "the same
        # matrix to what the file can carry", not bit-for-bit.
        assert np.allclose(
            returned.covariance.matrix, cluster.covariance.matrix, rtol=0, atol=1e-12
        )

    def test_the_off_diagonal_signs_survive(self, baseline, tmp_path):
        """The sign is the half of a covariance a round trip most easily loses,
        and it is what makes an error ellipse lean the right way."""
        observations, cluster = to_cluster([baseline], cluster_id="c1")
        path = tmp_path / "m.xml"
        write_measurement_file(
            _network(observations, cluster), path, frame=FRAME, epoch=EPOCH
        )
        read_into = Network(id="back")
        read_measurement_file(path, read_into, report=ReadReport(network=read_into))
        returned = next(iter(read_into.clusters.values())).covariance.matrix
        assert returned[0, 1] < 0
        assert returned[1, 2] > 0
        assert returned[0, 2] < 0

    def test_the_returned_cluster_is_still_a_baseline_cluster(self, baseline, tmp_path):
        observations, cluster = to_cluster([baseline], cluster_id="c1")
        path = tmp_path / "m.xml"
        write_measurement_file(
            _network(observations, cluster), path, frame=FRAME, epoch=EPOCH
        )
        read_into = Network(id="back")
        read_measurement_file(path, read_into, report=ReadReport(network=read_into))
        returned = next(iter(read_into.clusters.values()))
        assert returned.kind.name == "GNSS_BASELINE"
        assert len(returned.observation_ids) == 1


class TestTwoBaselinesBecomeAnXCluster:
    def test_two_members_are_written_as_x(self, baseline, tmp_path):
        second = baseline_from_solution(
            read_pos(POS / "xyz.pos"),
            base_station="3040",
            rover_station="9999",
            baseline_id="b2",
        )
        observations, cluster = to_cluster([baseline, second], cluster_id="c1")
        network = Network(id="n")
        for name in ("3040", "0759", "9999"):
            network.add_station(Station(id=name, name=name))
        for observation in observations:
            network.add_observation(observation)
        network.add_cluster(cluster)
        network.require_valid()

        document = write_measurement_file(
            network, tmp_path / "m.xml", frame=FRAME, epoch=EPOCH
        )
        assert document.counts.get("X") == 1

    def test_the_six_by_six_round_trips_with_its_zero_blocks(self, baseline, tmp_path):
        second = baseline_from_solution(
            read_pos(POS / "xyz.pos"),
            base_station="3040",
            rover_station="9999",
            baseline_id="b2",
        )
        observations, cluster = to_cluster([baseline, second], cluster_id="c1")
        network = Network(id="n")
        for name in ("3040", "0759", "9999"):
            network.add_station(Station(id=name, name=name))
        for observation in observations:
            network.add_observation(observation)
        network.add_cluster(cluster)
        path = tmp_path / "m.xml"
        write_measurement_file(network, path, frame=FRAME, epoch=EPOCH)

        read_into = Network(id="back")
        read_measurement_file(path, read_into, report=ReadReport(network=read_into))
        returned = next(iter(read_into.clusters.values())).covariance.matrix
        assert returned.shape == (6, 6)
        assert np.allclose(returned, cluster.covariance.matrix, atol=1e-12)
        # The engine supplied no correlation between the two, and the file says
        # so rather than the reader inventing one.
        assert np.allclose(returned[0:3, 3:6], 0.0)


class TestTheWriterRefusesALocalBaseline:
    def test_a_rotated_baseline_is_refused_by_name(self, baseline, tmp_path):
        """The mirror of ``gnss_baseline_not_in_adjustment_frame``.

        Without this, a baseline correctly rotated for the in-house core and
        then handed to DynAdjust would be adjusted as though the rotation had
        never happened.
        """
        local = rotate_baseline_to_local(baseline)
        observations, cluster = to_cluster([local], cluster_id="c1")
        network = _network(observations, cluster)
        with pytest.raises(ValidationError, match="gnss_baseline_not_geocentric"):
            write_measurement_file(
                network, tmp_path / "m.xml", frame=FRAME, epoch=EPOCH
            )
