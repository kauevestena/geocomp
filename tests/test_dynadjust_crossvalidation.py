# SPDX-License-Identifier: GPL-2.0-or-later
"""The in-house core against DynAdjust on one network (specs/07 section 6).

This is what phase P6 is for. The two are independent implementations of the
same least-squares problem, so agreement is evidence about both and a
disagreement is a real finding.

**The comparison itself is tier 1**, and so is the real cross-validation: the
core adjusts the network here, and DynAdjust's answer comes from the committed
output in ``tests/data/dynadjust/output``. Only the end-to-end pipeline test
needs the engine, and it is marked accordingly.

The network is upstream's ``gnss-network`` slice, which is all GNSS baselines
and point observations. That choice is deliberate: both are **linear** in the
coordinates, so the two engines solve the identical problem and any difference
is arithmetic rather than modelling. It also means the core can hold the network
in geocentric metres directly -- ``Frame.SPACE_3D`` is three orthogonal metres
whatever they are called -- so no frame conversion stands between the two
answers to be blamed for a difference.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.models.epoch import Epoch
from geocomp.core.models.position import CoordinateSystem, HeightType, Position
from geocomp.core.models.solution import (
    AdjustedStation,
    AdjustmentStatistics,
    DatumDefinition,
    ObservationResult,
    Solution,
    SolutionKind,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.crossvalidation import compare
from geocomp.engines.dynadjust.read_dynaml import read_dynaml
from geocomp.engines.dynadjust.read_output import AngularFormat, read_xyz
from geocomp.engines.dynadjust.solution import read_solution

DATA = Path(__file__).parent / "data" / "dynadjust"
OUTPUT = DATA / "output"
EPOCH = Epoch.from_datetime(datetime(2020, 1, 1, tzinfo=UTC), label="01.01.2020")

#: How far the perturbed starting coordinates are from the answer, in metres.
#: Five metres is far more than any real approximate coordinate would be out by,
#: and the point is that the core converges to the same place regardless -- so
#: agreement is not an artefact of having been seeded with the answer.
PERTURBATION = 5.0


@pytest.fixture
def network():
    return read_dynaml(DATA / "sample-stn.xml", DATA / "sample-msr.xml").network


@pytest.fixture
def in_house(network):
    """The in-house core's answer, from deliberately wrong starting values."""
    rng = np.random.default_rng(20260829)
    approximate = {
        row.station_id: dict(
            zip(
                ("e", "n", "u"),
                [
                    quantity.value + rng.uniform(-PERTURBATION, PERTURBATION)
                    for quantity in row.position.values
                ],
                strict=True,
            )
        )
        for row in read_xyz(OUTPUT / "sample.xyz")
    }
    run = adjust(network, AdjustmentOptions(frame=Frame.SPACE_3D), approximate=approximate)
    return to_solution(
        run,
        network,
        solution_id="in-house",
        crs="GDA2020",
        epoch=EPOCH,
        datum=DatumDefinition.NONE,
        # The network is held in geocentric metres, and saying so is what lets
        # the comparison compare coordinates instead of refusing to.
        system=CoordinateSystem.CARTESIAN,
        observation_results=to_observation_results(run),
    )


@pytest.fixture
def dynadjust(network):
    return read_solution(
        OUTPUT / "sample.adj",
        network=network,
        apu_path=OUTPUT / "sample.apu",
        cor_path=OUTPUT / "sample.cor",
        angular_format=AngularFormat.HP,
    )


class TestTheTwoEnginesAgree:
    def test_they_solve_the_same_problem(self, in_house, dynadjust) -> None:
        """Counts first: these are properties of the model, not of the
        arithmetic, so any difference means the two were not given the same
        network -- and comparing residuals after that would be meaningless."""
        assert in_house.statistics.degrees_of_freedom == dynadjust.statistics.degrees_of_freedom == 3
        assert in_house.statistics.n_observations == dynadjust.statistics.n_observations == 36
        assert in_house.statistics.n_parameters == dynadjust.statistics.n_parameters == 33

    def test_the_variance_factor_agrees(self, in_house, dynadjust) -> None:
        """DynAdjust prints sigma-zero to three decimals, so this is agreement
        to the precision the file can express."""
        assert in_house.statistics.variance_factor_aposteriori == pytest.approx(
            dynadjust.statistics.variance_factor_aposteriori, abs=5e-4
        )

    def test_the_coordinates_agree_to_a_twentieth_of_a_millimetre(
        self, in_house, dynadjust
    ) -> None:
        """The headline result, and the one that is hard to get by accident.

        Two independent implementations, one of them started five metres from
        the answer, place eleven stations within 0.05 mm of each other.
        """
        result = compare(in_house, dynadjust)
        assert result.largest_coordinate_difference is not None
        assert result.largest_coordinate_difference < 1e-4
        assert len(result.coordinate_differences) == 11

    def test_the_residuals_agree(self, in_house, dynadjust) -> None:
        """A wrong Jacobian or a dropped correlation moves these long before it
        moves the coordinates, so they are the sharper of the two checks."""
        result = compare(in_house, dynadjust)
        assert result.residual_differences
        assert max(result.residual_differences.values()) < 1e-4

    def test_the_comparison_agrees_on_every_quantity(self, in_house, dynadjust) -> None:
        result = compare(in_house, dynadjust)
        assert result.agrees, result.summary()
        assert result.disagreements == ()
        assert all(not item.not_compared for item in result.agreements), result.summary()

    def test_the_summary_names_each_quantity(self, in_house, dynadjust) -> None:
        summary = compare(in_house, dynadjust).summary()
        for quantity in ("degrees of freedom", "variance factor", "coordinates", "residuals"):
            assert quantity in summary


def _solution(
    identifier: str,
    *,
    values: tuple[float, float, float] = (1.0, 2.0, 3.0),
    system: CoordinateSystem = CoordinateSystem.CARTESIAN,
    dof: int = 3,
    variance: float = 1.0,
    residual: float = 0.001,
    station: str = "A",
    observation: str = "obs-1",
) -> Solution:
    position = Position(
        values=tuple(Quantity.exact(value, Unit.METRE) for value in values),  # type: ignore[arg-type]
        system=system,
        crs="GDA2020",
        epoch=EPOCH,
        height_type=HeightType.ELLIPSOIDAL,
    )
    return Solution(
        id=identifier,
        network_id="n",
        kind=SolutionKind.ADJUSTMENT,
        crs="GDA2020",
        epoch=EPOCH,
        adjusted_stations=(AdjustedStation(station_id=station, position=position),),
        observation_results=(
            ObservationResult(observation_id=observation, residual=residual),
        ),
        statistics=AdjustmentStatistics(
            n_observations=6,
            n_parameters=3,
            degrees_of_freedom=dof,
            variance_factor_aposteriori=variance,
        ),
    )


class TestTheComparisonItself:
    def test_two_identical_solutions_agree(self) -> None:
        result = compare(_solution("a"), _solution("b"))
        assert result.agrees
        assert result.largest_coordinate_difference == 0.0

    def test_a_moved_station_disagrees(self) -> None:
        result = compare(_solution("a"), _solution("b", values=(1.0, 2.0, 3.01)))
        assert not result.agrees
        assert [item.quantity for item in result.disagreements] == [
            "coordinates (largest component difference, m)"
        ]
        assert result.coordinate_differences["A"] == pytest.approx(0.01)

    def test_different_degrees_of_freedom_disagree(self) -> None:
        result = compare(_solution("a"), _solution("b", dof=4))
        assert not result.agrees
        assert "degrees of freedom" in [item.quantity for item in result.disagreements]

    def test_the_variance_factor_is_compared_relatively(self) -> None:
        """An absolute tolerance would be wrong at both ends: 1e-4 is a large
        relative error on a variance factor of 1e-3 and a negligible one on 100."""
        assert compare(_solution("a", variance=100.0), _solution("b", variance=100.5)).agrees
        assert not compare(_solution("a", variance=0.001), _solution("b", variance=0.002)).agrees

    def test_mismatched_frames_are_not_compared_rather_than_compared_wrongly(self) -> None:
        """Differencing a geocentric X against a projected easting produces a
        number, and the number means nothing."""
        result = compare(
            _solution("a", system=CoordinateSystem.CARTESIAN),
            _solution("b", system=CoordinateSystem.PROJECTED),
        )
        coordinates = next(
            item for item in result.agreements if item.quantity == "coordinates"
        )
        assert coordinates.not_compared
        assert "frames differ" in coordinates.not_compared
        assert result.coordinate_differences == {}

    def test_not_compared_is_not_the_same_as_disagreeing(self) -> None:
        """Absence of evidence is not evidence: an unconvertible frame must not
        read as a defect in an engine."""
        result = compare(
            _solution("a", system=CoordinateSystem.CARTESIAN),
            _solution("b", system=CoordinateSystem.PROJECTED),
        )
        assert result.agrees
        assert "not compared" in result.summary()

    def test_a_station_in_one_solution_only_is_reported(self) -> None:
        result = compare(_solution("a"), _solution("b", station="B"))
        coordinates = next(
            item for item in result.agreements if item.quantity == "coordinates"
        )
        assert "present in one solution only" in coordinates.not_compared

    def test_different_observations_are_reported_not_paired_by_guesswork(self) -> None:
        result = compare(_solution("a"), _solution("b", observation="obs-2"))
        residuals = next(item for item in result.agreements if item.quantity == "residuals")
        assert "name different observations" in residuals.not_compared

    def test_a_solution_with_no_results_does_not_fake_agreement(self) -> None:
        reference = _solution("a")
        other = _solution("b")
        stripped = Solution(
            id=other.id,
            network_id=other.network_id,
            kind=other.kind,
            crs=other.crs,
            epoch=other.epoch,
            adjusted_stations=other.adjusted_stations,
            statistics=other.statistics,
        )
        residuals = next(
            item for item in compare(reference, stripped).agreements
            if item.quantity == "residuals"
        )
        assert "reports no observation results" in residuals.not_compared

    def test_the_comparison_is_symmetric(self) -> None:
        one = compare(_solution("a"), _solution("b", values=(1.0, 2.0, 3.01)))
        two = compare(_solution("b", values=(1.0, 2.0, 3.01)), _solution("a"))
        assert one.agrees == two.agrees
        assert one.coordinate_differences == two.coordinate_differences
