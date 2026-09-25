# SPDX-License-Identifier: GPL-2.0-or-later
"""Gravity's place in the data model (``specs/04`` section 2.4, ``specs/12`` section 5).

Phase P8 moved a station's gravity out of the ``up`` slot of its position,
where every earlier phase carried it and where ``Position`` enforces metres.
These tests pin the replacement down: what a gravity constraint accepts and
refuses, that it survives serialisation, that the adjustment reads it and
nothing else, and the drift term the observation equation now carries.
"""

from __future__ import annotations

import numpy as np
import pytest

from geocomp.core.adjustment import approximate_values
from geocomp.core.adjustment.equations import evaluate
from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
from geocomp.core.adjustment.parameters import (
    Frame,
    ParameterLayout,
    drift_component,
    is_drift_component,
)
from geocomp.core.errors import ValidationError
from geocomp.core.models import (
    AdjustedStation,
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    DatumDefinition,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import METRES_PER_SECOND_SQUARED_PER_MGAL as MGAL
from geocomp.core.units import Unit

#: m/s^2. The order of the values involved; the arithmetic cares about differences.
G0 = 9.78


def _location(easting: float = 0.0, northing: float = 0.0, up: float = 0.0) -> Position:
    return Position(
        values=(
            Quantity.exact(easting, Unit.METRE),
            Quantity.exact(northing, Unit.METRE),
            Quantity.exact(up, Unit.METRE),
        ),
        system=CoordinateSystem.PROJECTED,
        crs="EPSG:31982",
        height_type=HeightType.ORTHOMETRIC,
    )


def _held(value: float, mode: ConstraintMode = ConstraintMode.FIXED, sigma: float = 0.0):
    gravity = (
        Quantity.from_std_dev(value, sigma, Unit.ACCELERATION)
        if sigma
        else Quantity.exact(value, Unit.ACCELERATION)
    )
    return ConstraintSpec(mode=mode, components=frozenset({"gravity"}), gravity=gravity)


def _difference(oid: str, origin: str, target: str, value: float, sigma: float, **meta):
    return Observation(
        id=oid,
        type=ObservationType.GRAVITY_DIFFERENCE,
        stations=(origin, target),
        values=(Quantity.from_std_dev(value, sigma, Unit.ACCELERATION),),
        meta=meta,
    )


class TestTheGravityConstraint:
    def test_needs_no_position(self):
        """A station of known gravity is held in gravity; where it is on the map
        is a separate fact."""
        constraint = _held(G0)
        assert constraint.position is None
        Station(id="A", constraint=constraint)

    def test_is_an_acceleration(self):
        with pytest.raises(ValidationError) as caught:
            ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"gravity"}),
                gravity=Quantity.exact(G0, Unit.METRE),
            )
        assert caught.value.code == "validation.gravity_constraint_unit"

    def test_the_component_needs_a_value(self):
        with pytest.raises(ValidationError) as caught:
            ConstraintSpec(mode=ConstraintMode.FIXED, components=frozenset({"gravity"}))
        assert caught.value.code == "validation.gravity_constraint_without_value"

    def test_a_value_needs_the_component(self):
        """A value that constrains nothing would be silently ignored."""
        with pytest.raises(ValidationError) as caught:
            ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"up"}),
                position=_location(),
                gravity=Quantity.exact(G0, Unit.ACCELERATION),
            )
        assert caught.value.code == "validation.gravity_value_without_gravity_component"

    def test_weighted_needs_an_uncertainty(self):
        with pytest.raises(ValidationError) as caught:
            _held(G0, ConstraintMode.WEIGHTED)
        assert caught.value.code == "validation.weighted_gravity_constraint_without_uncertainty"

    def test_a_free_station_carries_no_gravity(self):
        with pytest.raises(ValidationError):
            ConstraintSpec(gravity=Quantity.exact(G0, Unit.ACCELERATION))

    def test_positional_components_still_need_a_position(self):
        with pytest.raises(ValidationError) as caught:
            ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"gravity", "up"}),
                gravity=Quantity.exact(G0, Unit.ACCELERATION),
            )
        assert caught.value.code == "validation.constraint_without_position"

    def test_survives_serialisation(self):
        constraint = _held(G0, ConstraintMode.WEIGHTED, sigma=5e-8)
        assert ConstraintSpec.from_dict(constraint.to_dict()) == constraint


class TestTheAdjustedGravity:
    def test_is_an_acceleration(self):
        with pytest.raises(ValidationError) as caught:
            AdjustedStation(
                station_id="A", position=_location(), gravity=Quantity.exact(G0, Unit.METRE)
            )
        assert caught.value.code == "validation.adjusted_gravity_unit"

    def test_survives_serialisation(self):
        station = AdjustedStation(
            station_id="A",
            position=_location(10.0, 20.0),
            gravity=Quantity.from_std_dev(G0, 3e-8, Unit.ACCELERATION),
        )
        assert AdjustedStation.from_dict(station.to_dict()) == station


def _triangle(*, b_constraint: ConstraintSpec | None = None) -> Network:
    network = Network(id="triangle", crs="EPSG:31982")
    network.add_station(Station(id="A", approx_position=_location(), constraint=_held(G0)))
    network.add_station(
        Station(
            id="B",
            approx_position=_location(100.0),
            constraint=b_constraint or ConstraintSpec(),
        )
    )
    network.add_station(Station(id="C", approx_position=_location(0.0, 100.0)))
    network.add_observation(_difference("AB", "A", "B", 1.0 * MGAL, 0.01 * MGAL))
    network.add_observation(_difference("BC", "B", "C", -2.0 * MGAL, 0.01 * MGAL))
    network.add_observation(_difference("CA", "C", "A", 1.0 * MGAL, 0.01 * MGAL))
    return network


class TestTheAdjustmentReadsGravityAndNothingElse:
    def test_a_height_is_never_a_gravity_seed(self):
        """Before P8 the seeding read a constraint's ``up`` for a gravity network
        too, so a station held in *height* seeded its gravity with a height in
        metres."""
        benchmark = ConstraintSpec(
            mode=ConstraintMode.FIXED,
            components=frozenset({"up"}),
            position=_location(100.0, 0.0, 812.5),
        )
        start = approximate_values(_triangle(b_constraint=benchmark), Frame.GRAVITY_1D)
        assert start.values["B"]["g"] == pytest.approx(G0 + 1.0 * MGAL)

    def test_a_fixed_gravity_is_held_exactly(self):
        run = adjust(_triangle(), AdjustmentOptions(frame=Frame.GRAVITY_1D, datum=DatumDefinition.FIXED))
        layout = ParameterLayout.build(_triangle(), Frame.GRAVITY_1D)
        assert layout.column("A", "g") is None
        assert layout.fixed_values[("A", "g")] == G0
        assert run.degrees_of_freedom == 1

    def test_a_weighted_gravity_moves_and_counts(self):
        """Weighted is data, not truth: the station keeps a column, its
        constraint is a row, and the redundancy counts it."""
        network = _triangle()
        network.stations["A"] = Station(
            id="A", approx_position=_location(), constraint=_held(G0, ConstraintMode.WEIGHTED, 0.005 * MGAL)
        )
        run = adjust(network, AdjustmentOptions(frame=Frame.GRAVITY_1D, datum=DatumDefinition.CONSTRAINED))
        assert run.layout.column("A", "g") is not None
        assert run.degrees_of_freedom == 1


def _drift_layout(network: Network, degree: int) -> ParameterLayout:
    names = tuple(drift_component(k) for k in range(1, degree + 1))
    return ParameterLayout.build(network, Frame.GRAVITY_1D, auxiliary={"S1": names})


class TestTheDriftTerm:
    def test_names_are_by_degree(self):
        assert drift_component(1) == "drift_1"
        assert is_drift_component("drift_3")
        assert not is_drift_component("drift")
        with pytest.raises(ValidationError):
            drift_component(0)

    def test_coefficients_are_accelerations(self):
        layout = _drift_layout(_triangle(), 2)
        units = dict(zip(layout.labels(), layout.component_units(), strict=True))
        assert units["S1.drift_1"] is Unit.ACCELERATION
        assert units["S1.drift_2"] is Unit.ACCELERATION

    @pytest.mark.parametrize("degree", [1, 2, 3])
    def test_a_difference_sees_the_drift_at_both_readings(self, degree):
        """``tau_to**k - tau_from**k``, not ``(tau_to - tau_from)**k``. They agree
        at degree 1 only; MCGravi and pyGrav implement the second."""
        network = _triangle()
        observation = _difference(
            "AB", "A", "B", 1.0 * MGAL, 0.01 * MGAL,
            drift_owner="S1", drift_elapsed_s=(1800.0, 9000.0), drift_scale_s=3600.0,
        )
        layout = _drift_layout(network, degree)
        x = np.zeros(layout.size)
        (row,) = evaluate(observation, layout, x)
        for k in range(1, degree + 1):
            column = layout.column("S1", drift_component(k))
            assert row.partials[column] == pytest.approx(2.5**k - 0.5**k)

    def test_the_computed_value_includes_the_drift(self):
        network = _triangle()
        observation = _difference(
            "AB", "A", "B", 1.0 * MGAL, 0.01 * MGAL,
            drift_owner="S1", drift_elapsed_s=(0.0, 7200.0), drift_scale_s=3600.0,
        )
        layout = _drift_layout(network, 1)
        x = np.zeros(layout.size)
        x[layout.column("B", "g")] = G0 + 1.0 * MGAL
        x[layout.column("S1", "drift_1")] = 0.01 * MGAL
        (row,) = evaluate(observation, layout, x)
        assert row.computed == pytest.approx(1.0 * MGAL + 2.0 * 0.01 * MGAL)

    def test_an_owner_without_drift_unknowns_is_an_ordinary_difference(self):
        """Which is what a pre-corrected network is."""
        observation = _difference("AB", "A", "B", 1.0 * MGAL, 0.01 * MGAL, drift_owner="S1")
        layout = ParameterLayout.build(_triangle(), Frame.GRAVITY_1D)
        (row,) = evaluate(observation, layout, np.zeros(layout.size))
        # A is held, so only B has a column: the whole row is +1 on B.
        assert row.partials == {layout.column("B", "g"): 1.0}

    def test_missing_times_are_refused(self):
        observation = _difference("AB", "A", "B", 1.0 * MGAL, 0.01 * MGAL, drift_owner="S1")
        layout = _drift_layout(_triangle(), 1)
        with pytest.raises(ValidationError) as caught:
            evaluate(observation, layout, np.zeros(layout.size))
        assert caught.value.code == "validation.gravity_drift_times_missing"

    def test_a_non_positive_scale_is_refused(self):
        observation = _difference(
            "AB", "A", "B", 1.0 * MGAL, 0.01 * MGAL,
            drift_owner="S1", drift_elapsed_s=(0.0, 60.0), drift_scale_s=0.0,
        )
        layout = _drift_layout(_triangle(), 1)
        with pytest.raises(ValidationError) as caught:
            evaluate(observation, layout, np.zeros(layout.size))
        assert caught.value.code == "validation.gravity_drift_scale_invalid"
