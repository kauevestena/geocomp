# SPDX-License-Identifier: GPL-2.0-or-later
"""Weighted datum constraints (FR-222), which used to be declared and ignored.

``specs/06-adjustment-core.md`` section 3 lists ``WEIGHTED`` beside ``FIXED``,
``MINIMUM_CONSTRAINT`` and ``INNER_CONSTRAINT``. The model layer implemented it
properly -- :class:`~geocomp.core.models.station.ConstraintSpec` refuses a
weighted constraint with no covariance -- and the adjustment then **dropped it
on the floor**: only ``FIXED`` was ever read, so a weighted station was
estimated as though free and its published coordinates were discarded.

The consequences were not subtle. A network held only by weighted constraints
was rank-deficient rather than constrained, and refused to adjust. A network
with one fixed and several weighted benchmarks quietly used the first and
ignored the rest, so the disagreement between benchmarks -- the very thing a
user holds several of them to see -- could not appear in the residuals. It was
found in phase P5 while checking that a geoid-derived height's uncertainty
reached the adjusted heights: it could not, because the constraint carrying it
was not in the system.

The tests below are chosen to fail loudly if the rows go missing again. The
sandwich in :func:`test_a_constraint_interpolates_between_free_and_fixed` is the
decisive one: a constraint so tight it is effectively fixed and one so loose it
is effectively absent must bracket the ordinary case, which no
constraint-ignoring implementation can do.
"""

from __future__ import annotations

import numpy as np
import pytest

import tests.networks as rd
from geocomp.core.adjustment import Frame
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
)
from geocomp.core.adjustment.normal_equations import CONSTRAINT_ROW_PREFIX
from geocomp.core.adjustment.parameters import ParameterLayout, weighted_constraints
from geocomp.core.errors import ComputationError, DataError
from geocomp.core.models import ConstraintMode, ConstraintSpec, DatumDefinition, Station
from geocomp.core.uncertainty import Covariance
from geocomp.core.units import Unit

OPTIONS = AdjustmentOptions(frame=Frame.HEIGHT_1D, datum=DatumDefinition.CONSTRAINED)


def _weighted(network, station_id: str, height: float, sigma: float) -> None:
    """Replace a station's constraint with a weighted one at *height*."""
    station = network.stations[station_id]
    position = rd._position((0.0, 0.0, height), exact=True)
    network.stations[station_id] = Station(
        id=station.id,
        approx_position=station.approx_position,
        constraint=ConstraintSpec(
            mode=ConstraintMode.WEIGHTED,
            components=frozenset({"up"}),
            position=position,
            covariance=Covariance.diagonal({"up": sigma**2}, {"up": Unit.METRE}),
        ),
        station_type=station.station_type,
    )


def _free(network, station_id: str) -> None:
    station = network.stations[station_id]
    network.stations[station_id] = Station(
        id=station.id,
        approx_position=station.approx_position,
        station_type=station.station_type,
    )


def _solve(network) -> dict[str, float]:
    run = adjust(network, OPTIONS)
    return {
        slot.owner: float(run.parameters[index])
        for index, slot in enumerate(run.layout.slots)
        if slot.kind == "station"
    }


# -- the rows exist at all ------------------------------------------------


def test_a_weighted_constraint_produces_a_row() -> None:
    case = rd.levelling_loop()
    _weighted(case.network, "B", 12.500, 0.010)

    layout = ParameterLayout.build(case.network, Frame.HEIGHT_1D)
    found = weighted_constraints(case.network, layout, Frame.HEIGHT_1D)
    assert [constraint.station_id for constraint in found] == ["B"]
    assert found[0].components == ("up",)
    assert found[0].values == (12.500,)


def test_the_row_reaches_the_design_matrix() -> None:
    case = rd.levelling_loop()
    _weighted(case.network, "B", 12.500, 0.010)
    run = adjust(case.network, OPTIONS)

    constraint_rows = [
        row
        for row, (label, _component) in enumerate(run.system.row_labels)
        if label.startswith(CONSTRAINT_ROW_PREFIX)
    ]
    assert len(constraint_rows) == 1
    row = run.system.design[constraint_rows[0]]
    # The observation equation of a constraint is the identity: one 1.0, in the
    # column of the parameter it constrains, and nothing else.
    assert np.count_nonzero(row) == 1
    assert row[run.layout.station_columns("B")["h"]] == pytest.approx(1.0)


def test_a_weighted_constraint_adds_a_degree_of_freedom() -> None:
    """It is an observation, so it counts as one -- in n and in the redundancy."""
    free = rd.levelling_loop()
    _free(free.network, "A")
    _weighted(free.network, "A", 10.000, 0.010)
    _weighted(free.network, "B", 12.500, 0.010)

    held = rd.levelling_loop()
    run_held = adjust(held.network, OPTIONS)
    run_free = adjust(free.network, OPTIONS)

    # Six lines and one fixed station: 6 rows, 3 parameters, dof 3.
    assert run_held.degrees_of_freedom == 3
    # Six lines and two weighted stations: 8 rows, 4 parameters, dof 4.
    assert run_free.degrees_of_freedom == 4
    assert sum(run_free.redundancy) == pytest.approx(run_free.degrees_of_freedom)


# -- the decisive behavioural tests ---------------------------------------


def test_a_network_held_only_by_weighted_constraints_is_solvable() -> None:
    """Before this, the same network was rank-deficient and refused to adjust.

    Nothing is fixed: the datum comes entirely from the two weighted heights.
    An implementation that ignores weighted constraints has no datum here, so
    this test cannot pass by accident.
    """
    case = rd.levelling_loop()
    _free(case.network, "A")
    _weighted(case.network, "A", 10.000, 0.005)
    _weighted(case.network, "C", 15.000, 0.005)

    heights = _solve(case.network)
    for station_id, truth in case.truth.items():
        assert heights[station_id] == pytest.approx(truth["h"], abs=0.01)


def test_ignoring_the_constraints_would_leave_the_network_undetermined() -> None:
    """The other half of the previous test: the observations alone are not enough.

    Stated as its own test because it is what makes the previous one meaningful
    -- without it, "the network solved" might just mean the observations
    determined everything anyway.
    """
    case = rd.levelling_loop()
    for station_id in ("A", "B", "C", "D"):
        _free(case.network, station_id)
    with pytest.raises(ComputationError) as excinfo:
        adjust(case.network, OPTIONS)
    assert "rank" in excinfo.value.code or "defect" in excinfo.value.code


def test_a_constraint_interpolates_between_free_and_fixed() -> None:
    """A tight constraint behaves as fixed, a loose one as absent.

    The sandwich: hold B at a height 40 mm away from where the network wants it,
    with three uncertainties spanning four orders of magnitude. The adjusted
    height of B must move monotonically from the network's own answer towards
    the constrained value as the constraint tightens, and the extremes must
    match the free and fixed solutions.
    """
    reference = rd.levelling_loop()
    fixed_only = _solve(reference.network)["B"]

    tight = rd.levelling_loop()
    _weighted(tight.network, "B", fixed_only + 0.040, 0.00001)
    loose = rd.levelling_loop()
    _weighted(loose.network, "B", fixed_only + 0.040, 10.0)
    middling = rd.levelling_loop()
    _weighted(middling.network, "B", fixed_only + 0.040, 0.002)

    tight_b = _solve(tight.network)["B"]
    loose_b = _solve(loose.network)["B"]
    middling_b = _solve(middling.network)["B"]

    assert tight_b == pytest.approx(fixed_only + 0.040, abs=1.0e-5)
    assert loose_b == pytest.approx(fixed_only, abs=1.0e-5)
    assert loose_b < middling_b < tight_b


def test_the_constraint_carries_a_residual_saying_how_far_it_moved() -> None:
    """Which is the whole reason to hold a benchmark weighted rather than fixed.

    A published height that the network disagrees with by 40 mm should say so,
    in the residual of its own constraint row, where a user looking for a bad
    benchmark will find it.
    """
    case = rd.levelling_loop()
    settled = _solve(case.network)["B"]
    _weighted(case.network, "B", settled + 0.040, 0.010)

    run = adjust(case.network, OPTIONS)
    results = to_observation_results(run)
    constraint = [r for r in results if r.observation_id == f"{CONSTRAINT_ROW_PREFIX}B"]
    assert len(constraint) == 1
    # Most of the 40 mm disagreement stays in the constraint's residual, since
    # the levelling (2 mm) is far more precise than the constraint (10 mm).
    assert abs(constraint[0].residual) > 0.030
    assert 0.0 < constraint[0].redundancy < 1.0


def test_a_tighter_constraint_gives_a_more_certain_answer() -> None:
    """The constraint's precision reaches the adjusted covariance (FR-204).

    This is the property the geoid work needed: a height held with the geoid
    model's uncertainty folded in must produce a less certain answer than the
    same height held without it.
    """
    def sigma_of(constraint_sigma: float) -> float:
        case = rd.levelling_loop()
        _free(case.network, "A")
        _weighted(case.network, "A", 10.000, constraint_sigma)
        run = adjust(case.network, OPTIONS)
        column = run.layout.station_columns("A")["h"]
        return float(np.sqrt(run.cofactor_parameters[column, column]))

    assert sigma_of(0.001) < sigma_of(0.010) < sigma_of(0.100)


# -- refusals -------------------------------------------------------------


def test_a_singular_constraint_covariance_is_refused() -> None:
    """A zero-variance component is a fixed constraint written as a weighted one.

    Refusing beats substituting a pseudo-inverse, which would silently apply a
    weight the user never asked for.
    """
    case = rd.levelling_loop()
    station = case.network.stations["B"]
    case.network.stations["B"] = Station(
        id="B",
        approx_position=station.approx_position,
        constraint=ConstraintSpec(
            mode=ConstraintMode.WEIGHTED,
            components=frozenset({"up"}),
            position=rd._position((0.0, 0.0, 12.5), exact=True),
            covariance=Covariance.diagonal({"up": 0.0}, {"up": Unit.METRE}),
        ),
        station_type=station.station_type,
    )
    layout = ParameterLayout.build(case.network, Frame.HEIGHT_1D)
    with pytest.raises(DataError) as excinfo:
        weighted_constraints(case.network, layout, Frame.HEIGHT_1D)
    assert excinfo.value.code == "data.weighted_constraint_singular"


def test_a_constraint_on_a_fixed_component_contributes_nothing() -> None:
    """No parameter to constrain, so no row -- rather than an empty one."""
    case = rd.levelling_loop()
    layout = ParameterLayout.build(case.network, Frame.HEIGHT_1D)
    # "A" is fixed in the reference network, so it has no column at all.
    assert not layout.station_columns("A")
    assert weighted_constraints(case.network, layout, Frame.HEIGHT_1D) == []
