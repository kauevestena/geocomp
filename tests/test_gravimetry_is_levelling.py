# SPDX-License-Identifier: GPL-2.0-or-later
"""A gravimetric network is a levelling network with a different unit.

The observation equation of a gravity difference and that of a height
difference are the **same equation**: an observed difference between two
station parameters, with partials of -1 and +1. GeoComp already implements them
as one function -- ``_difference_1d`` in ``core/adjustment/equations.py``,
called with the component ``"g"`` or ``"h"`` -- and this module makes that
identity executable rather than a comment.

Why it earns a test file of its own:

**It is a correctness statement.** If the two ever diverge, one of them is
wrong, and the wrong one produces a plausible adjustment that nobody would
question. Locking the identity down means a change to levelling that breaks
gravimetry fails here rather than in P8.

**It is a planning fact, and it corrects a specification.** ADR-0002 justified
the in-house core partly on "gravimetry has no alternative", which is true of
the *corrections* and of jointly estimated drift, and false of the *adjustment*:
DynAdjust adjusts 1D difference networks, so a drift-corrected gravimetric
network is one of them under a relabelling. That makes P8 far cheaper than
planned, and it gives the cross-validation in P6 a gravimetric case it was
assumed not to have.

**It is the reason a combined adjustment is possible at all** (P9): heights and
gravity enter the same normal matrix because they are the same kind of unknown
observed the same way.
"""

from __future__ import annotations

import numpy as np
import pytest

from geocomp.core.adjustment.equations import evaluate
from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
from geocomp.core.adjustment.parameters import Frame, ParameterLayout
from geocomp.core.models import (
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
from geocomp.core.units import Unit

#: The same topology and the same numbers, read once as metres of height and
#: once as milligal of gravity. Only the unit and the type differ.
STATIONS = {"A": 10.000, "B": 12.500, "C": 15.000, "D": 11.250}
LINES = (("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("A", "C"), ("B", "D"))
SIGMA = 0.002
#: Deterministic, and the same for both networks: the point is that identical
#: inputs give identical answers, so the noise must be identical too.
NOISE = (0.0011, -0.0007, 0.0019, -0.0013, 0.0004, -0.0021)


def _position(value: float, unit: Unit, *, exact: bool) -> Position:
    quantity = Quantity.exact(value, unit) if exact else Quantity.from_std_dev(value, 0.5, unit)
    zero = Quantity.exact(0.0, unit)
    return Position(
        values=(zero, zero, quantity),
        system=CoordinateSystem.PROJECTED,
        crs="EPSG:31982",
        height_type=HeightType.ORTHOMETRIC,
    )


def _network(observation_type: ObservationType, unit: Unit, network_id: str) -> Network:
    """The same network twice, differing only in observation type and unit.

    The *positions* are metre-typed in both, because that is how the model
    stores a gravity station's value: ``ParameterLayout`` maps ``GRAVITY_1D``
    onto the position's ``up`` component, and ``Position`` enforces metres on
    it. See ``test_the_unit_of_a_gravity_parameter_is_a_known_wart`` below.
    """
    network = Network(id=network_id, crs="EPSG:31982")
    network.add_station(
        Station(
            id="A",
            approx_position=_position(STATIONS["A"], Unit.METRE, exact=True),
            constraint=ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"up"}),
                position=_position(STATIONS["A"], Unit.METRE, exact=True),
            ),
        )
    )
    for name in ("B", "C", "D"):
        network.add_station(
            Station(
                id=name,
                approx_position=_position(STATIONS[name] + 0.05, Unit.METRE, exact=False),
            )
        )
    for index, (origin, target) in enumerate(LINES):
        value = STATIONS[target] - STATIONS[origin] + NOISE[index]
        network.add_observation(
            Observation(
                id=f"L{index}",
                type=observation_type,
                stations=(origin, target),
                values=(Quantity.from_std_dev(value, SIGMA, unit),),
            )
        )
    return network


@pytest.fixture(scope="module")
def levelling() -> Network:
    return _network(ObservationType.HEIGHT_DIFFERENCE, Unit.METRE, "levels")


@pytest.fixture(scope="module")
def gravimetry() -> Network:
    return _network(ObservationType.GRAVITY_DIFFERENCE, Unit.ACCELERATION, "gravity")


def _design(network: Network, frame: Frame) -> np.ndarray:
    """The design matrix of a network, evaluated at its approximate values."""
    layout = ParameterLayout.build(network, frame)
    x = np.zeros(len(layout.slots))
    for index, slot in enumerate(layout.slots):
        station = network.stations[slot.owner]
        x[index] = station.approx_position.values[2].value

    rows = []
    for observation in network.observations.values():
        for row in evaluate(observation, layout, x):
            dense = np.zeros(len(layout.slots))
            for column, partial in row.partials.items():
                dense[column] = partial
            rows.append(dense)
    return np.array(rows)


class TestTheEquationIsOneEquation:
    def test_the_two_design_matrices_are_identical(self, levelling, gravimetry):
        """Element for element. Not "similar": the same matrix."""
        assert np.array_equal(
            _design(levelling, Frame.HEIGHT_1D), _design(gravimetry, Frame.GRAVITY_1D)
        )

    def test_each_row_is_a_difference_of_two_parameters(self, levelling):
        """-1 at the origin, +1 at the target, zero elsewhere. That is the whole
        model, and it is why the two techniques coincide.

        A line touching the fixed station shows only one of the two: a held
        station has no parameter, so it has no column to carry its partial."""
        design = _design(levelling, Frame.HEIGHT_1D)
        assert len(design) == len(LINES)
        for row in design:
            partials = sorted(value for value in row if value)
            assert partials in ([-1.0, 1.0], [-1.0], [1.0])
        assert any(len([v for v in row if v]) == 2 for row in design)

    def test_the_two_are_dispatched_to_the_same_implementation(self):
        """The identity is structural, not coincidental: both types resolve to
        ``_difference_1d`` with a different component name. A future change
        that gave one its own implementation would break this."""
        import inspect

        from geocomp.core.adjustment import equations

        height = inspect.getsource(equations._height_difference)
        gravity = inspect.getsource(equations._gravity_difference)
        assert "_difference_1d" in height
        assert "_difference_1d" in gravity


class TestTheAdjustmentsCoincide:
    @pytest.fixture(scope="class")
    def runs(self, levelling, gravimetry):
        return (
            adjust(
                levelling, AdjustmentOptions(frame=Frame.HEIGHT_1D, datum=DatumDefinition.FIXED)
            ),
            adjust(
                gravimetry,
                AdjustmentOptions(frame=Frame.GRAVITY_1D, datum=DatumDefinition.FIXED),
            ),
        )

    def test_the_estimates_agree_to_machine_precision(self, runs):
        heights, gravities = runs
        assert np.allclose(heights.parameters, gravities.parameters, rtol=0.0, atol=1e-12)

    def test_the_residuals_agree(self, runs):
        heights, gravities = runs
        assert np.allclose(heights.residuals, gravities.residuals, rtol=0.0, atol=1e-12)

    def test_the_variance_factor_agrees(self, runs):
        """Which means every statistic built on it agrees too: the global test,
        the standardised residuals, the redundancy numbers."""
        heights, gravities = runs
        assert heights.variance_factor_aposteriori == pytest.approx(
            gravities.variance_factor_aposteriori, rel=1e-12
        )

    def test_the_redundancy_is_the_same(self, runs):
        heights, gravities = runs
        assert heights.degrees_of_freedom == gravities.degrees_of_freedom


class TestWhatIsActuallyDifferent:
    """The techniques are not the same technique. What separates them is the
    corrections, the drift, and the datum -- never the observation equation."""

    def test_a_gravity_network_will_not_accept_a_height_difference(self):
        """The frames are kept apart deliberately: mixing metres and mGal in one
        normal matrix without a declared relationship would be an error the
        arithmetic could not detect."""
        from geocomp.core.errors import GeoCompError

        network = _network(ObservationType.HEIGHT_DIFFERENCE, Unit.METRE, "wrong-frame")
        with pytest.raises(GeoCompError):
            adjust(network, AdjustmentOptions(frame=Frame.GRAVITY_1D))

    def test_a_gravity_parameter_is_carried_in_a_metre_typed_slot(self):
        """The frame knows a gravity parameter is an acceleration. Its *value*
        is nonetheless carried in the ``up`` component of a ``Position``, which
        enforces metres -- so the number arrives through a field that describes
        it wrongly.

        The arithmetic is unaffected: the frame never mixes the two, and the
        equivalence above holds exactly. But it is a place the model says
        something untrue, and giving gravity its own parameter carrier is P8's
        work. Asserted rather than fixed, so the day it *is* fixed this fails
        and points at itself."""
        from geocomp.core.adjustment.parameters import _constraint_name
        from geocomp.core.models import CoordinateSystem

        assert Frame.GRAVITY_1D.component_units == (Unit.ACCELERATION,)
        assert _constraint_name("g", Frame.GRAVITY_1D) == "up"
        assert CoordinateSystem.PROJECTED.component_units[2] is Unit.METRE

    def test_drift_is_the_part_a_levelling_engine_cannot_do(self):
        """A gravity difference may carry a jointly estimated drift term, which
        adds a column no levelling network has. That -- not the difference
        equation -- is what an external 1D engine would be unable to reproduce
        (``specs/12`` section 4.3)."""
        import inspect

        from geocomp.core.adjustment import equations

        source = inspect.getsource(equations._gravity_difference)
        assert "drift" in source
