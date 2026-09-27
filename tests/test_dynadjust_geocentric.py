# SPDX-License-Identifier: GPL-2.0-or-later
"""The geocentric frame against DynAdjust, on a combined survey (specs/13 section 3).

P6 cross-validated the in-house core on GNSS baselines alone, which are linear
in the coordinates -- so the core could hold them in any three orthogonal metres
and the comparison said nothing about how an angle is modelled on a curved
Earth. This one does. ``tests/combined_network.py`` is a six-station survey
over 3 km with GNSS baselines, an ellipsoidal height, and a total station's
direction sets, zenith angles, slope distances, a horizontal angle and an
azimuth. GeoComp's writer turned it into ``combined-{stn,msr}.xml``; DynAdjust's
answer is the committed ``combined.*``; and the in-house core adjusts **the same
two files**, read back with GeoComp's own DynaML reader, in
``Frame.GEOCENTRIC_3D`` with each station's own vertical. The files round
coordinates, baselines and distances to 0.1 mm, so adjusting the survey itself
would compare two slightly different problems.

**What is compared, and what is not.** Two modelling differences are real and
are recorded in ``specs/07`` section 6.3 rather than tolerated here:

* For a **slope distance** DynAdjust carries the target height along the
  instrument's vertical, not the target's own (0.8 mm on a 2.9 km sight with a
  1.7 m reflector); its zenith distances use each end's own, as GeoComp does
  for every type. The survey is therefore built with ``target=0``, where the
  two coincide; the instrument heights stay, and both carry those the same way.
* DynAdjust adjusts a **direction set** as derived angles and weights them with
  their full banded covariance -- the coordinates agree -- but its chi-square
  adds ``v^2 / sigma^2`` over the angles alone, dropping the correlation between
  consecutive ones. Its sigma zero is therefore not ``v^T P v / r`` of its own
  weights. The test below reproduces DynAdjust's figure from the in-house
  residuals by making exactly that omission, which is what shows it is the
  cause and not a difference of solution.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
)
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.errors import DataError
from geocomp.core.models import ClusterKind, ConstraintMode, DatumDefinition, ObservationType
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.engine import (
    ANGULAR_FORMAT,
    MEASUREMENT_FORMAT,
    DynAdjustEngine,
    DynAdjustJob,
)
from geocomp.engines.dynadjust.read_dynaml import read_dynaml
from geocomp.engines.dynadjust.read_output import match_observations, read_measurements
from geocomp.engines.dynadjust.solution import read_solution

from .combined_network import EPOCH, FRAME, SETUPS, TRUTH, survey
from .conftest import requires_dynadjust

OUTPUT = Path(__file__).parent / "data" / "dynadjust" / "output"

#: How far the in-house starting coordinates are moved from the written ones.
#: The same five metres as the P6 cross-validation, for the same reason: so
#: agreement is not an artefact of having started where DynAdjust did.
PERTURBATION = 5.0

#: DynAdjust prints coordinates to 0.1 mm, so half that is the most two equal
#: answers can differ by on the page; the micrometre is for arithmetic. The
#: largest difference found is 0.2 micrometres beyond the rounding.
PRINTED = 0.5e-4 + 1e-6


def written():
    """The network DynAdjust adjusted, as GeoComp reads its input back."""
    return read_dynaml(OUTPUT / "combined-stn.xml", OUTPUT / "combined-msr.xml").network


def job(network) -> DynAdjustJob:
    return DynAdjustJob(
        network=network,
        name="combined",
        target_frame=FRAME,
        target_epoch=EPOCH,
        iteration_threshold=1e-6,
        maximum_iterations=20,
    )


def _held(network) -> dict[str, np.ndarray]:
    return {
        identifier: np.array([q.value for q in station.constraint.position.values])
        for identifier, station in network.stations.items()
        if station.constraint.mode is ConstraintMode.FIXED
    }


def _coordinates(run, network, station: str) -> np.ndarray:
    """A station's adjusted ECEF position; a held one is where it was held."""
    held = _held(network)
    if station in held:
        return held[station]
    columns = run.layout.station_columns(station)
    return np.array([run.parameters[columns[c]] for c in ("x", "y", "z")])


@pytest.fixture(scope="module")
def network():
    return written()


@pytest.fixture(scope="module")
def in_house(network):
    rng = np.random.default_rng(20260926)
    approximate = {
        identifier: dict(
            zip(
                ("x", "y", "z"),
                (q.value + rng.uniform(-PERTURBATION, PERTURBATION) for q in station.approx_position.values),
                strict=True,
            )
        )
        for identifier, station in network.stations.items()
    }
    return adjust(
        network,
        AdjustmentOptions(frame=Frame.GEOCENTRIC_3D, datum=DatumDefinition.FIXED),
        approximate=approximate,
    )


@pytest.fixture(scope="module")
def dynadjust(network):
    return read_solution(
        OUTPUT / "combined.adj",
        network=network,
        apu_path=OUTPUT / "combined.apu",
        # What ``DynAdjustEngine.parse`` passes, so this reads the file the way
        # a GeoComp-driven run would.
        angular_format=ANGULAR_FORMAT,
        measurement_format=MEASUREMENT_FORMAT,
    )


class TestTheCommittedInput:
    def test_it_is_what_the_writer_makes_of_the_survey(self, tmp_path) -> None:
        """The fixture's input is GeoComp's own DynaML. If the writer changes,
        the output was made from files it no longer writes, and this says so
        before a stale comparison can pass."""
        DynAdjustEngine().prepare(job(survey(target=0.0)), tmp_path)
        for name in ("combined-stn.xml", "combined-msr.xml"):
            assert (tmp_path / name).read_text() == (OUTPUT / name).read_text(), name

    def test_reading_it_back_loses_nothing_the_adjustment_uses(self, network) -> None:
        """Every observation, every set, and the heights the zenith angles and
        slope distances were measured with."""
        original = survey(target=0.0)
        assert len(network.observations) == len(original.observations) == 48
        assert len(network.clusters) == len(original.clusters) == 5
        setups = [
            o
            for o in network.observations.values()
            if o.type in (ObservationType.SLOPE_DISTANCE, ObservationType.ZENITH_ANGLE)
        ]
        assert len(setups) == 28
        assert all(o.instrument_height.value == pytest.approx(1.563) for o in setups)
        assert all(o.target_height.value == 0.0 for o in setups)


class TestTheTwoEnginesAgree:
    def test_they_solve_problems_of_the_same_size(self, in_house, dynadjust) -> None:
        """Degrees of freedom agree; the counts behind them do not, and should
        not. GeoComp models a set of *n* directions as *n* observations and one
        orientation unknown, DynAdjust as *n - 1* derived angles and none: four
        sets, so four more of each here, and the same redundancy."""
        sets = len(SETUPS)
        assert in_house.degrees_of_freedom == dynadjust.statistics.degrees_of_freedom == 38
        assert in_house.system.design.shape[0] == dynadjust.statistics.n_observations + sets
        assert in_house.system.design.shape[1] == dynadjust.statistics.n_parameters + sets

    def test_the_coordinates_agree_to_the_printed_precision(
        self, in_house, network, dynadjust
    ) -> None:
        """The headline: two implementations of angles on the ellipsoid, one
        started 5 m out, placing four free stations as close together as the
        0.1 mm DynAdjust prints can show -- over 3 km, with sights up to 2.9 km
        long."""
        for station in dynadjust.adjusted_stations:
            theirs = np.array([q.value for q in station.position.values])
            difference = np.abs(_coordinates(in_house, network, station.station_id) - theirs)
            assert difference.max() <= PRINTED, (station.station_id, difference)

    def test_the_answer_is_near_the_truth_the_measurements_came_from(
        self, in_house, network
    ) -> None:
        """Not a comparison but a sanity check on the survey: noise of a few
        millimetres and arcseconds cannot move a station decimetres."""
        for station, truth in TRUTH.items():
            assert np.abs(_coordinates(in_house, network, station) - truth).max() < 0.02

    def test_every_residual_dynadjust_reports_agrees(self, in_house, network, dynadjust) -> None:
        """Per observation, to the file's printed precision -- 0.1 mm for the
        linear rows and 0.0001 arcseconds for the angles -- so a sign convention
        or a unit that differed would show at once."""
        ours: dict[str, list[float]] = {}
        for result in to_observation_results(in_house):
            ours.setdefault(result.observation_id, []).append(result.residual)
        theirs: dict[str, list[float]] = {}
        for result in dynadjust.observation_results:
            theirs.setdefault(result.observation_id, []).append(result.residual)
        for identifier, values in theirs.items():
            angular = network.observations[identifier].values[0].unit is Unit.RADIAN
            tolerance = math.radians(0.0002 / 3600.0) if angular else 1e-4
            assert values == pytest.approx(ours[identifier], abs=tolerance), identifier
        # Every row but the derived angles: 9 baseline components, 14 slope
        # distances, 14 zenith angles, an angle, an azimuth and a height.
        assert sum(len(values) for values in theirs.values()) == 40

    def test_dynadjusts_sigma_zero_is_ours_with_the_angle_correlation_dropped(
        self, in_house, network, dynadjust
    ) -> None:
        """The finding, reproduced rather than tolerated.

        From the in-house residuals, each set's derived-angle residuals are the
        differences of consecutive directions'. With their full covariance --
        ``sigma^2`` times the tridiagonal (2, -1) -- their quadratic form is the
        set's share of the in-house ``v^T P v``, and the in-house sigma zero
        follows. With the diagonal alone it is what DynAdjust's chi-square
        sums, and the result matches DynAdjust's printed figure to its last
        digit. The two differ by far more than that digit, so the match says
        which one DynAdjust computed.
        """
        residual = {r.observation_id: r.residual for r in to_observation_results(in_house)}
        full = diagonal = 0.0
        for cluster in network.clusters.values():
            if cluster.kind is not ClusterKind.DIRECTION_SET:
                continue
            members = [network.observations[i] for i in cluster.observation_ids]
            sigma = members[0].values[0].std_dev
            angles = np.diff([residual[m.id] for m in members])
            size = len(angles)
            covariance = sigma**2 * (2.0 * np.eye(size) - np.eye(size, k=1) - np.eye(size, k=-1))
            full += float(angles @ np.linalg.solve(covariance, angles))
            diagonal += float(angles @ angles) / (2.0 * sigma**2)

        dof = in_house.degrees_of_freedom
        quadratic = in_house.variance_factor_aposteriori * dof
        # The full form is the sets' share of v^T P v, so it cannot exceed it.
        assert 0.0 < full < quadratic
        as_dynadjust = (quadratic - full + diagonal) / dof
        printed = dynadjust.statistics.variance_factor_aposteriori
        assert as_dynadjust == pytest.approx(printed, abs=5.5e-4)
        assert abs(in_house.variance_factor_aposteriori - printed) > 0.02


class TestDirectionSetRows:
    def test_they_are_checked_but_produce_no_result(self, network) -> None:
        """A row is the direction as read plus the *derived angle's* correction:
        a difference of two directions' residuals. It is no one direction's."""
        rows = read_measurements(OUTPUT / "combined.adj", angular_format=MEASUREMENT_FORMAT)
        results = match_observations(rows, network)
        directions = {
            identifier
            for identifier, observation in network.observations.items()
            if observation.type is ObservationType.DIRECTION
        }
        assert sum(1 for row in rows if row.code == "D") == 10
        assert directions.isdisjoint(result.observation_id for result in results)
        assert len(results) == len(rows) - 10

    def test_a_set_out_of_order_still_fails(self, network) -> None:
        rows = read_measurements(OUTPUT / "combined.adj", angular_format=MEASUREMENT_FORMAT)
        rows[0], rows[1] = rows[1], rows[0]
        with pytest.raises(DataError) as excinfo:
            match_observations(rows, network)
        assert excinfo.value.code == "data.dynadjust_measurement_station_mismatch"

    def test_the_measurements_are_not_read_in_the_stations_format(self) -> None:
        """What the engine got wrong: one format for both tables. The stations
        are in HP and the measurements in separated fields, so reading the
        latter as HP fails on the first angle."""
        with pytest.raises(DataError) as excinfo:
            read_measurements(OUTPUT / "combined.adj", angular_format=ANGULAR_FORMAT)
        assert excinfo.value.code == "data.dynadjust_output_not_a_number"


@pytest.mark.engines
@requires_dynadjust
class TestAgainstARealEngine:
    """Tier 4: the same comparison with DynAdjust run now, through the engine."""

    def test_the_pipeline_reaches_the_same_answer(self, in_house, network, tmp_path) -> None:
        solution = DynAdjustEngine().adjust(job(survey(target=0.0)), tmp_path)
        assert solution.statistics.converged
        assert solution.statistics.degrees_of_freedom == in_house.degrees_of_freedom
        for station in solution.adjusted_stations:
            theirs = np.array([q.value for q in station.position.values])
            ours = _coordinates(in_house, network, station.station_id)
            assert np.abs(ours - theirs).max() <= PRINTED
