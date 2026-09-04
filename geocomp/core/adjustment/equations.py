# SPDX-License-Identifier: GPL-2.0-or-later
"""Observation equations and their analytic Jacobians.

``specs/06-adjustment-core.md`` section 2. For each observation type: the
computed value at the current approximate parameters, and the row (or rows) of
the design matrix **A**.

Dispatch is through the observation type registry in
:mod:`geocomp.core.models.observation`, so adding a type means adding a registry
entry and one function here -- not editing the design-matrix builder
(``specs/03-architecture.md`` section 4).

**Every Jacobian in this module has a test against complex-step
differentiation** (``tests/test_equations.py``). That is not routine diligence:
a sign error in a Jacobian raises nothing, produces no obviously silly number,
and yields a coordinate that is wrong by an amount nobody can see. The
machinery in :mod:`geocomp.core.differentiation` exists for exactly this check.

Angles follow the survey convention: azimuth is measured **from north, clockwise**,
so ``azimuth = atan2(dE, dN)``; zenith angles are measured from the local
vertical.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from geocomp.core.adjustment.parameters import Frame, ParameterLayout
from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.models import Observation, ObservationType
from geocomp.core.units import wrap_to_pi

__all__ = ["SUPPORTED_TYPES", "EquationRow", "evaluate", "supports"]


@dataclass(frozen=True)
class EquationRow:
    """One row of the linearised system.

    Attributes:
        computed: The observation value predicted by the current parameters.
        partials: Column index to partial derivative. Sparse by nature -- an
            observation touches at most a handful of the unknowns.
        component: Which component of a multi-component observation this is.
    """

    computed: float
    partials: dict[int, float]
    component: str = ""

    def to_dense(self, size: int) -> np.ndarray:
        row = np.zeros(size)
        for column, value in self.partials.items():
            row[column] = value
        return row


#: Coordinates of a station, taking fixed components from the layout and
#: estimated ones from the current parameter vector.
def _coordinates(
    station_id: str, layout: ParameterLayout, x: np.ndarray
) -> dict[str, float]:
    values: dict[str, float] = {}
    for component in layout.frame.components:
        column = layout.column(station_id, component)
        if column is None:
            values[component] = layout.fixed_values[(station_id, component)]
        else:
            values[component] = float(x[column])
    return values


def _accumulate(
    partials: dict[int, float], layout: ParameterLayout, station_id: str, terms: dict[str, float]
) -> None:
    """Add derivative *terms* for a station, skipping components held fixed.

    A fixed component contributes to the computed value but has no column, so
    its derivative has nowhere to go -- which is exactly right: it is not being
    estimated.
    """
    for component, derivative in terms.items():
        column = layout.column(station_id, component)
        if column is not None:
            partials[column] = partials.get(column, 0.0) + derivative


# -- 1D: heights and gravity ---------------------------------------------


def _difference_1d(
    observation: Observation, layout: ParameterLayout, x: np.ndarray, component: str
) -> list[EquationRow]:
    """A difference between two station values: ``to - from``."""
    origin, target = observation.stations
    start = _coordinates(origin, layout, x)[component]
    end = _coordinates(target, layout, x)[component]

    partials: dict[int, float] = {}
    _accumulate(partials, layout, origin, {component: -1.0})
    _accumulate(partials, layout, target, {component: +1.0})
    return [EquationRow(end - start, partials)]


def _absolute_1d(
    observation: Observation, layout: ParameterLayout, x: np.ndarray, component: str
) -> list[EquationRow]:
    """A station's value observed directly."""
    (station_id,) = observation.stations
    value = _coordinates(station_id, layout, x)[component]
    partials: dict[int, float] = {}
    _accumulate(partials, layout, station_id, {component: 1.0})
    return [EquationRow(value, partials)]


def _height_difference(observation, layout, x):
    component = "h" if layout.frame is Frame.HEIGHT_1D else "u"
    return _difference_1d(observation, layout, x, component)


def _height(observation, layout, x):
    component = "h" if layout.frame is Frame.HEIGHT_1D else "u"
    return _absolute_1d(observation, layout, x, component)


def _gravity(observation, layout, x):
    return _absolute_1d(observation, layout, x, "g")


def _gravity_difference(observation, layout, x):
    """Gravity difference, plus the drift term when a drift unknown exists.

    ``specs/12-module-gravimetry.md`` section 4.3: drift and gravity differences
    are not separable by pre-correction alone, so the drift rate is estimated
    jointly. The elapsed time since the session datum is carried on the
    observation as ``meta["drift_hours"]``, and the drift owner as
    ``meta["drift_owner"]``.
    """
    rows = _difference_1d(observation, layout, x, "g")
    owner = observation.meta.get("drift_owner")
    if owner is None:
        return rows

    column = layout.column(owner, "drift")
    if column is None:
        return rows

    hours = float(observation.meta.get("drift_hours", 0.0))
    row = rows[0]
    partials = dict(row.partials)
    partials[column] = partials.get(column, 0.0) + hours
    return [EquationRow(row.computed + hours * float(x[column]), partials)]


# -- 2D and 3D geometry --------------------------------------------------


def _plan_delta(
    observation: Observation, layout: ParameterLayout, x: np.ndarray, indices: tuple[int, int] = (0, 1)
) -> tuple[dict[str, float], dict[str, float], float, float, float]:
    """Return both stations' coordinates and the planimetric deltas."""
    origin_id, target_id = observation.stations[indices[0]], observation.stations[indices[1]]
    origin = _coordinates(origin_id, layout, x)
    target = _coordinates(target_id, layout, x)
    de = target["e"] - origin["e"]
    dn = target["n"] - origin["n"]
    distance = math.hypot(de, dn)
    if distance == 0.0:
        raise ComputationError(
            "coincident_stations",
            observation=observation.id,
            stations=[origin_id, target_id],
            expected="distinct approximate coordinates; the derivative is singular here",
        )
    return origin, target, de, dn, distance


def _horizontal_distance(observation, layout, x):
    origin_id, target_id = observation.stations
    _, _, de, dn, distance = _plan_delta(observation, layout, x)

    partials: dict[int, float] = {}
    _accumulate(partials, layout, origin_id, {"e": -de / distance, "n": -dn / distance})
    _accumulate(partials, layout, target_id, {"e": +de / distance, "n": +dn / distance})
    return [EquationRow(distance, partials)]


def _azimuth_terms(de: float, dn: float) -> tuple[float, dict[str, float], dict[str, float]]:
    """Azimuth from north clockwise, and its partials w.r.t. both stations.

    alpha = atan2(dE, dN), so d(alpha)/d(dE) = dN / d^2 and
    d(alpha)/d(dN) = -dE / d^2.
    """
    squared = de * de + dn * dn
    azimuth = math.atan2(de, dn)
    at_origin = {"e": -dn / squared, "n": +de / squared}
    at_target = {"e": +dn / squared, "n": -de / squared}
    return azimuth, at_origin, at_target


def _azimuth(observation, layout, x):
    origin_id, target_id = observation.stations
    _, _, de, dn, _ = _plan_delta(observation, layout, x)
    azimuth, at_origin, at_target = _azimuth_terms(de, dn)

    partials: dict[int, float] = {}
    _accumulate(partials, layout, origin_id, at_origin)
    _accumulate(partials, layout, target_id, at_target)
    return [EquationRow(azimuth, partials)]


def _direction(observation, layout, x):
    """A direction: an azimuth less the unknown orientation of its setup.

    The orientation unknown is what makes a set of directions a cluster rather
    than a set of independent azimuths (FR-104). Its owner is the setup id.
    """
    origin_id, target_id = observation.stations
    _, _, de, dn, _ = _plan_delta(observation, layout, x)
    azimuth, at_origin, at_target = _azimuth_terms(de, dn)

    partials: dict[int, float] = {}
    _accumulate(partials, layout, origin_id, at_origin)
    _accumulate(partials, layout, target_id, at_target)

    orientation = 0.0
    owner = observation.setup_id or observation.meta.get("orientation_owner")
    if owner is not None:
        column = layout.column(owner, "orientation")
        if column is not None:
            orientation = float(x[column])
            partials[column] = partials.get(column, 0.0) - 1.0

    return [EquationRow(azimuth - orientation, partials)]


def _horizontal_angle(observation, layout, x):
    """The angle at a station between a backsight and a foresight.

    Computed as the difference of two azimuths, which is why its Jacobian is the
    difference of two azimuth Jacobians. The station occupied appears in both,
    so its partials combine rather than replace -- ``_accumulate`` adds.
    """
    at_id, from_id, to_id = observation.stations

    _, _, de_from, dn_from, _ = _plan_delta(observation, layout, x, indices=(0, 1))
    _, _, de_to, dn_to, _ = _plan_delta(observation, layout, x, indices=(0, 2))

    azimuth_from, at_occupied_from, at_backsight = _azimuth_terms(de_from, dn_from)
    azimuth_to, at_occupied_to, at_foresight = _azimuth_terms(de_to, dn_to)

    partials: dict[int, float] = {}
    _accumulate(partials, layout, at_id, {k: -v for k, v in at_occupied_from.items()})
    _accumulate(partials, layout, from_id, {k: -v for k, v in at_backsight.items()})
    _accumulate(partials, layout, at_id, at_occupied_to)
    _accumulate(partials, layout, to_id, at_foresight)

    return [EquationRow(wrap_to_pi(azimuth_to - azimuth_from), partials)]


def _slope_distance(observation, layout, x):
    origin_id, target_id = observation.stations
    origin = _coordinates(origin_id, layout, x)
    target = _coordinates(target_id, layout, x)
    de, dn, du = target["e"] - origin["e"], target["n"] - origin["n"], target["u"] - origin["u"]
    distance = math.sqrt(de * de + dn * dn + du * du)
    if distance == 0.0:
        raise ComputationError(
            "coincident_stations", observation=observation.id, stations=[origin_id, target_id]
        )

    unit = {"e": de / distance, "n": dn / distance, "u": du / distance}
    partials: dict[int, float] = {}
    _accumulate(partials, layout, origin_id, {k: -v for k, v in unit.items()})
    _accumulate(partials, layout, target_id, unit)
    return [EquationRow(distance, partials)]


def _zenith_angle(observation, layout, x):
    """Zenith angle from the local vertical: ``z = atan2(d_horizontal, du)``."""
    zenith, terms = _vertical_geometry(observation, layout, x)
    partials: dict[int, float] = {}
    origin_id, target_id = observation.stations
    _accumulate(partials, layout, origin_id, {k: -v for k, v in terms.items()})
    _accumulate(partials, layout, target_id, terms)
    return [EquationRow(zenith, partials)]


def _vertical_angle(observation, layout, x):
    """Vertical angle from the horizon: ``v = pi/2 - z``.

    The same sight as a zenith angle, counted from the other end, so the value
    is the complement and every partial derivative is negated. Kept as its own
    type rather than converted on the way in because the *observation* is what
    the instrument recorded, and a solution that reports a residual against a
    zenith angle nobody measured is harder to check against a field book.
    """
    zenith, terms = _vertical_geometry(observation, layout, x)
    partials: dict[int, float] = {}
    origin_id, target_id = observation.stations
    _accumulate(partials, layout, origin_id, terms)
    _accumulate(partials, layout, target_id, {k: -v for k, v in terms.items()})
    return [EquationRow(math.pi / 2.0 - zenith, partials)]


def _vertical_geometry(observation, layout, x):
    """The zenith angle of a sight and its partials at the *target*."""
    origin_id, target_id = observation.stations
    origin = _coordinates(origin_id, layout, x)
    target = _coordinates(target_id, layout, x)
    de, dn, du = target["e"] - origin["e"], target["n"] - origin["n"], target["u"] - origin["u"]
    horizontal = math.hypot(de, dn)
    squared = de * de + dn * dn + du * du
    if squared == 0.0 or horizontal == 0.0:
        raise ComputationError(
            "degenerate_zenith_angle",
            observation=observation.id,
            stations=[origin_id, target_id],
            expected="a sight that is neither zero length nor exactly vertical",
        )

    # dz/d(du) = -h / s^2 ;  dz/d(de) = du * de / (s^2 * h)
    return math.atan2(horizontal, du), {
        "e": du * de / (squared * horizontal),
        "n": du * dn / (squared * horizontal),
        "u": -horizontal / squared,
    }


def _gnss_baseline(observation, layout, x):
    """A GNSS baseline: three coordinate differences, one row each.

    The three rows are correlated through the cluster's 3x3 covariance, which
    the weight matrix carries (FR-104). The equations themselves are simple; the
    correctness is in not decomposing the cluster.
    """
    origin_id, target_id = observation.stations
    origin = _coordinates(origin_id, layout, x)
    target = _coordinates(target_id, layout, x)

    rows: list[EquationRow] = []
    for component, name in zip(layout.frame.components, ("dx", "dy", "dz"), strict=True):
        partials: dict[int, float] = {}
        _accumulate(partials, layout, origin_id, {component: -1.0})
        _accumulate(partials, layout, target_id, {component: +1.0})
        rows.append(EquationRow(target[component] - origin[component], partials, name))
    return rows


def _gnss_point(observation, layout, x):
    """A GNSS point solution: the three coordinates observed directly."""
    (station_id,) = observation.stations
    coordinates = _coordinates(station_id, layout, x)

    rows: list[EquationRow] = []
    for component, name in zip(layout.frame.components, ("x", "y", "z"), strict=True):
        partials: dict[int, float] = {}
        _accumulate(partials, layout, station_id, {component: 1.0})
        rows.append(EquationRow(coordinates[component], partials, name))
    return rows


#: Observation type to equation function. A type absent from this table is not
#: yet supported by the in-house core; :func:`evaluate` says so by name rather
#: than failing obscurely.
_EQUATIONS = {
    ObservationType.HEIGHT_DIFFERENCE: _height_difference,
    ObservationType.ORTHOMETRIC_HEIGHT: _height,
    ObservationType.ELLIPSOIDAL_HEIGHT: _height,
    ObservationType.HORIZONTAL_DISTANCE: _horizontal_distance,
    ObservationType.ELLIPSOID_DISTANCE: _horizontal_distance,
    ObservationType.AZIMUTH: _azimuth,
    ObservationType.ASTRONOMIC_AZIMUTH: _azimuth,
    ObservationType.DIRECTION: _direction,
    ObservationType.HORIZONTAL_ANGLE: _horizontal_angle,
    ObservationType.SLOPE_DISTANCE: _slope_distance,
    ObservationType.ZENITH_ANGLE: _zenith_angle,
    ObservationType.VERTICAL_ANGLE: _vertical_angle,
    ObservationType.GNSS_BASELINE: _gnss_baseline,
    ObservationType.GNSS_POINT: _gnss_point,
    ObservationType.GRAVITY: _gravity,
    ObservationType.GRAVITY_DIFFERENCE: _gravity_difference,
}

SUPPORTED_TYPES = frozenset(_EQUATIONS)


def supports(observation_type: ObservationType) -> bool:
    return observation_type in _EQUATIONS


def evaluate(
    observation: Observation, layout: ParameterLayout, x: np.ndarray
) -> list[EquationRow]:
    """Computed value and design-matrix row(s) for *observation*.

    Raises:
        ValidationError: if the type has no equation yet, or cannot contribute
            to this frame's dimensionality -- rejected here rather than silently
            ignored (FR-227).
    """
    equation = _EQUATIONS.get(observation.type)
    if equation is None:
        raise ValidationError(
            "observation_type_not_supported",
            observation=observation.id,
            type=observation.type.value,
            expected=sorted(t.value for t in SUPPORTED_TYPES),
        )

    dimension = layout.frame.dimension
    if dimension not in observation.spec.dimensionality:
        raise ValidationError(
            "observation_wrong_dimensionality",
            observation=observation.id,
            type=observation.type.value,
            frame=layout.frame.value,
            expected=f"a type valid in {dimension}D: {sorted(observation.spec.dimensionality)}",
        )

    if layout.frame is Frame.GRAVITY_1D and observation.type not in (
        ObservationType.GRAVITY,
        ObservationType.GRAVITY_DIFFERENCE,
    ):
        raise ValidationError(
            "observation_not_a_gravity_type",
            observation=observation.id,
            type=observation.type.value,
            expected="GRAVITY or GRAVITY_DIFFERENCE in a gravity network",
        )

    return equation(observation, layout, x)
