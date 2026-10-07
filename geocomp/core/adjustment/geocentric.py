# SPDX-License-Identifier: GPL-2.0-or-later
"""Observation equations in a geocentric frame, each at its own station's vertical.

``specs/06-adjustment-core.md`` section 2.3 and ``specs/13`` section 6. Phase P9a.

``Frame.SPACE_3D`` is flat: one "up" for the whole network, which is exact for
a Krumm example and for a site a few hundred metres across, and wrong for a
combined survey of any size -- the vertical turns by about 32" per kilometre,
and the Earth's surface falls away from the tangent plane by 8 cm at 1 km. A
zenith angle measured there against a single "up" is wrong by the first, and
a height carried across the network by the second.

Here the unknowns are **geocentric X, Y, Z** and every observation that depends
on the vertical is evaluated in the **local east-north-up frame of the station
it was measured at**, from that station's current coordinates. That is the
three-dimensional geodetic model -- Vanicek and Krakiwsky's, Leick's, and
DynAdjust's -- and it has no size limit: curvature is not corrected for, it is
simply never assumed away.

**The vertical is the ellipsoidal normal.** A total station levels to the plumb
line, which differs by the deflection of the vertical -- a few seconds of arc
typically, tens in mountains. No deflection is applied, as in DynAdjust unless
one is supplied; ``specs/13`` section 6 records it.

**The Jacobians are exact, including the turning of the frame.** The local
frame at a station depends on that station's position, so moving the station
rotates every sight measured from it. The derivative of the rotation is
included (through ``d(latitude, longitude)/d(X, Y, Z)``), and so is that of the
instrument and target heights, which lie along each end's own normal. Leaving
them out would still converge -- the computed values are exact -- but the
partials would be wrong by about ``d / R``, and ``TestJacobians`` holds every
equation in the core to its numerical derivative.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from geocomp.core.adjustment.parameters import ParameterLayout, orientation_owner
from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.geodesy.cartesian import (
    cartesian_to_geodetic,
    enu_rotation,
    geodetic_to_cartesian_jacobian,
)
from geocomp.core.geodesy.ellipsoid import Ellipsoid, ellipsoid_by_name
from geocomp.core.models import (
    BaselineFrame,
    HeightType,
    Observation,
    ObservationType,
    baseline_frame,
)
from geocomp.core.units import wrap_to_pi

if TYPE_CHECKING:
    from geocomp.core.adjustment.equations import EquationRow

__all__ = [
    "GEOCENTRIC_TYPES",
    "HEIGHT_TYPE_KEY",
    "UNDULATION",
    "evaluate_geocentric",
    "height_type_of",
]

#: Where a height observation states whether it is ellipsoidal or orthometric,
#: as the levelling network already writes it (a ``HeightType`` name).
HEIGHT_TYPE_KEY = "height_type"
#: The auxiliary parameter holding a station's geoid undulation, which an
#: orthometric observation subtracts. ``undulations.py`` adds one, with the
#: geoid model's value as its prior, wherever an orthometric observation needs it.
UNDULATION = "undulation"

#: The ellipsoid the frame's geodetic latitudes and heights are on. GRS80 is
#: the ellipsoid of ITRF and of SIRGAS 2000; WGS84 differs from it by 0.1 mm in
#: the semi-minor axis.
ELLIPSOID: Ellipsoid = ellipsoid_by_name("GRS80")


@dataclass(frozen=True)
class _Station:
    """A station's position and the local frame at it, with derivatives."""

    position: np.ndarray
    rotation: np.ndarray  # rows east, north, up
    d_rotation_d_latitude: np.ndarray
    d_rotation_d_longitude: np.ndarray
    d_geodetic_d_cartesian: np.ndarray  # rows d(lat), d(lon), d(h) by d(X, Y, Z)
    height: float

    @property
    def up(self) -> np.ndarray:
        return self.rotation[2]

    def d_up(self) -> np.ndarray:
        """d(up)/d(X, Y, Z): how the normal turns as the station moves."""
        return np.outer(self.d_rotation_d_latitude[2], self.d_geodetic_d_cartesian[0]) + np.outer(
            self.d_rotation_d_longitude[2], self.d_geodetic_d_cartesian[1]
        )


def _station(position: np.ndarray) -> _Station:
    latitude, longitude, height = cartesian_to_geodetic(*position, ELLIPSOID)
    sin_lat, cos_lat = math.sin(latitude), math.cos(latitude)
    sin_lon, cos_lon = math.sin(longitude), math.cos(longitude)
    d_latitude = np.array(
        [
            [0.0, 0.0, 0.0],
            [-cos_lat * cos_lon, -cos_lat * sin_lon, -sin_lat],
            [-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat],
        ]
    )
    d_longitude = np.array(
        [
            [-cos_lon, -sin_lon, 0.0],
            [sin_lat * sin_lon, -sin_lat * cos_lon, 0.0],
            [-cos_lat * sin_lon, cos_lat * cos_lon, 0.0],
        ]
    )
    jacobian = geodetic_to_cartesian_jacobian(latitude, longitude, height, ELLIPSOID)
    return _Station(
        position=position,
        rotation=enu_rotation(latitude, longitude),
        d_rotation_d_latitude=d_latitude,
        d_rotation_d_longitude=d_longitude,
        d_geodetic_d_cartesian=np.linalg.inv(jacobian),
        height=height,
    )


def _position(station_id: str, layout, x: np.ndarray) -> np.ndarray:
    values = []
    for component in ("x", "y", "z"):
        column = layout.column(station_id, component)
        values.append(
            layout.fixed_values[(station_id, component)] if column is None else float(x[column])
        )
    return np.array(values)


def _sight(observation: Observation, origin: _Station, target: _Station):
    """The sight in the origin's local frame, and its derivatives by both ends.

    ``l = R_i ((p_j + t u_j) - (p_i + i u_i))``: from the instrument's trunnion
    axis to the target, each offset along its own station's normal.
    """
    instrument = observation.instrument_height.value if observation.instrument_height else 0.0
    target_height = observation.target_height.value if observation.target_height else 0.0
    delta = (target.position + target_height * target.up) - (
        origin.position + instrument * origin.up
    )
    local = origin.rotation @ delta
    d_target = origin.rotation @ (np.eye(3) + target_height * target.d_up())
    d_origin = (
        origin.rotation @ (-np.eye(3) - instrument * origin.d_up())
        + np.outer(origin.d_rotation_d_latitude @ delta, origin.d_geodetic_d_cartesian[0])
        + np.outer(origin.d_rotation_d_longitude @ delta, origin.d_geodetic_d_cartesian[1])
    )
    return local, d_origin, d_target


# -- functions of the local sight ---------------------------------------------


def _slope(local: np.ndarray) -> tuple[float, np.ndarray]:
    distance = float(np.linalg.norm(local))
    return distance, local / distance


def _horizontal(local: np.ndarray) -> tuple[float, np.ndarray]:
    horizontal = math.hypot(local[0], local[1])
    return horizontal, np.array([local[0] / horizontal, local[1] / horizontal, 0.0])


def _zenith(local: np.ndarray) -> tuple[float, np.ndarray]:
    horizontal = math.hypot(local[0], local[1])
    squared = float(local @ local)
    return math.atan2(horizontal, local[2]), np.array(
        [
            local[2] * local[0] / (squared * horizontal),
            local[2] * local[1] / (squared * horizontal),
            -horizontal / squared,
        ]
    )


def _azimuth(local: np.ndarray) -> tuple[float, np.ndarray]:
    squared = local[0] ** 2 + local[1] ** 2
    return math.atan2(local[0], local[1]), np.array(
        [local[1] / squared, -local[0] / squared, 0.0]
    )


# -- the equation rows ---------------------------------------------------------


def _row(layout, partials: dict[int, float], station_id: str, gradient: np.ndarray) -> None:
    for component, derivative in zip(("x", "y", "z"), gradient, strict=True):
        column = layout.column(station_id, component)
        if column is not None:
            partials[column] = partials.get(column, 0.0) + float(derivative)


def _sighted(observation, layout, x, function, *, stations=(0, 1)):
    origin_id, target_id = (observation.stations[i] for i in stations)
    origin = _station(_position(origin_id, layout, x))
    target = _station(_position(target_id, layout, x))
    local, d_origin, d_target = _sight(observation, origin, target)
    if math.hypot(local[0], local[1]) == 0.0 or not np.any(local):
        raise ComputationError(
            "degenerate_sight",
            observation=observation.id,
            stations=[origin_id, target_id],
            expected="a sight that is neither zero length nor exactly vertical",
        )
    value, gradient = function(local)
    partials: dict[int, float] = {}
    _row(layout, partials, origin_id, gradient @ d_origin)
    _row(layout, partials, target_id, gradient @ d_target)
    return value, partials


def _orientation(observation, layout, x, partials) -> float:
    column = layout.column(orientation_owner(observation), "orientation")
    if column is None:
        return 0.0
    partials[column] = partials.get(column, 0.0) - 1.0
    return float(x[column])


def height_type_of(observation: Observation) -> HeightType:
    """Whether a height observation is ellipsoidal or orthometric.

    Read from the type for a height, and stated in ``meta`` for a difference:
    in a geocentric frame the two kinds of difference differ by the change in
    undulation, and a levelled one is not assumed to be either.
    """
    if observation.type is ObservationType.ELLIPSOIDAL_HEIGHT:
        return HeightType.ELLIPSOIDAL
    if observation.type is ObservationType.ORTHOMETRIC_HEIGHT:
        return HeightType.ORTHOMETRIC
    stated = (observation.meta or {}).get(HEIGHT_TYPE_KEY)
    if stated is None:
        raise ValidationError(
            "height_difference_type_unstated",
            observation=observation.id,
            expected=(
                "the height difference's type -- ELLIPSOIDAL or ORTHOMETRIC -- in "
                f"meta['{HEIGHT_TYPE_KEY}']. In a geocentric frame the two differ by the "
                "change in geoid undulation, centimetres over a kilometre, so it is "
                "not guessed"
            ),
        )
    return HeightType[stated] if isinstance(stated, str) else stated


def _heights(observation, layout, x):
    """Ellipsoidal or orthometric height, or a difference of them.

    An orthometric one subtracts each station's undulation *parameter*
    (``h - N``), never a fixed number: the geoid's uncertainty then reaches the
    solution, and the adjustment can move ``N`` where the observations disagree
    with the model (``undulations.py``).
    """
    kind = height_type_of(observation)
    ids = observation.stations
    stations = [_station(_position(s, layout, x)) for s in ids]
    signs = (1.0,) if len(ids) == 1 else (-1.0, 1.0)
    value = sum(sign * station.height for sign, station in zip(signs, stations, strict=True))
    partials: dict[int, float] = {}
    for sign, station_id, station in zip(signs, ids, stations, strict=True):
        _row(layout, partials, station_id, sign * station.d_geodetic_d_cartesian[2])
    if kind is HeightType.ORTHOMETRIC:
        for sign, station_id in zip(signs, ids, strict=True):
            column = layout.column(station_id, UNDULATION)
            if column is None:
                # specs/13 section 3, item 2: without a geoid the difference is
                # the undulation itself -- tens of metres in much of Brazil.
                raise ValidationError(
                    "mixed_height_types",
                    observation=observation.id,
                    expected=(
                        "a geoid model relating this orthometric height to the "
                        "ellipsoidal heights the geocentric frame computes; without "
                        "one the difference is the geoid undulation, which can be "
                        "tens of metres"
                    ),
                )
            value -= sign * float(x[column])
            partials[column] = partials.get(column, 0.0) - sign
    elif kind is not HeightType.ELLIPSOIDAL:
        raise ValidationError(
            "height_type_unsupported",
            observation=observation.id,
            received=kind.name,
            expected="ELLIPSOIDAL or ORTHOMETRIC",
        )
    return [_equation_row(value, partials)]


def _equation_row(value, partials, component=""):
    from geocomp.core.adjustment.equations import EquationRow

    return EquationRow(value, partials, component)


def _slope_distance(observation, layout, x):
    return [_equation_row(*_sighted(observation, layout, x, _slope))]


def _horizontal_distance(observation, layout, x):
    return [_equation_row(*_sighted(observation, layout, x, _horizontal))]


def _zenith_angle(observation, layout, x):
    return [_equation_row(*_sighted(observation, layout, x, _zenith))]


def _vertical_angle(observation, layout, x):
    value, partials = _sighted(observation, layout, x, _zenith)
    return [_equation_row(math.pi / 2.0 - value, {k: -v for k, v in partials.items()})]


def _azimuth_equation(observation, layout, x):
    return [_equation_row(*_sighted(observation, layout, x, _azimuth))]


def _direction(observation, layout, x):
    value, partials = _sighted(observation, layout, x, _azimuth)
    orientation = _orientation(observation, layout, x, partials)
    return [_equation_row(value - orientation, partials)]


def _horizontal_angle(observation, layout, x):
    back, back_partials = _sighted(observation, layout, x, _azimuth, stations=(0, 1))
    fore, fore_partials = _sighted(observation, layout, x, _azimuth, stations=(0, 2))
    partials = dict(fore_partials)
    for column, derivative in back_partials.items():
        partials[column] = partials.get(column, 0.0) - derivative
    return [_equation_row(wrap_to_pi(fore - back), partials)]


def _gnss_baseline(observation, layout, x):
    """ECEF baselines difference the unknowns directly; a ``LOCAL`` one is read
    in the base station's horizon, which is what rotating it there produced."""
    origin_id, target_id = observation.stations
    origin = _position(origin_id, layout, x)
    target = _position(target_id, layout, x)
    rows = []
    if baseline_frame(observation) is BaselineFrame.ECEF:
        for index, name in enumerate(("dx", "dy", "dz")):
            partials: dict[int, float] = {}
            gradient = np.zeros(3)
            gradient[index] = 1.0
            _row(layout, partials, origin_id, -gradient)
            _row(layout, partials, target_id, gradient)
            rows.append(_equation_row(float(target[index] - origin[index]), partials, name))
        return rows
    base = _station(origin)
    delta = target - origin
    local = base.rotation @ delta
    d_origin = (
        -base.rotation
        + np.outer(base.d_rotation_d_latitude @ delta, base.d_geodetic_d_cartesian[0])
        + np.outer(base.d_rotation_d_longitude @ delta, base.d_geodetic_d_cartesian[1])
    )
    for index, name in enumerate(("dx", "dy", "dz")):
        partials = {}
        _row(layout, partials, origin_id, d_origin[index])
        _row(layout, partials, target_id, base.rotation[index])
        rows.append(_equation_row(float(local[index]), partials, name))
    return rows


def _gnss_point(observation, layout, x):
    (station_id,) = observation.stations
    position = _position(station_id, layout, x)
    rows = []
    for index, name in enumerate(("x", "y", "z")):
        partials: dict[int, float] = {}
        gradient = np.zeros(3)
        gradient[index] = 1.0
        _row(layout, partials, station_id, gradient)
        rows.append(_equation_row(float(position[index]), partials, name))
    return rows


_EQUATIONS = {
    ObservationType.SLOPE_DISTANCE: _slope_distance,
    ObservationType.HORIZONTAL_DISTANCE: _horizontal_distance,
    ObservationType.ZENITH_ANGLE: _zenith_angle,
    ObservationType.VERTICAL_ANGLE: _vertical_angle,
    ObservationType.AZIMUTH: _azimuth_equation,
    ObservationType.DIRECTION: _direction,
    ObservationType.HORIZONTAL_ANGLE: _horizontal_angle,
    ObservationType.HEIGHT_DIFFERENCE: _heights,
    ObservationType.ORTHOMETRIC_HEIGHT: _heights,
    ObservationType.ELLIPSOIDAL_HEIGHT: _heights,
    ObservationType.GNSS_BASELINE: _gnss_baseline,
    ObservationType.GNSS_POINT: _gnss_point,
}

#: What the geocentric frame adjusts. Not the ellipsoid distance -- a reduced
#: quantity with no meaning between two points in space -- nor gravity, which
#: is never adjusted with coordinates (``specs/12`` section 7).
GEOCENTRIC_TYPES = frozenset(_EQUATIONS)


def evaluate_geocentric(
    observation: Observation, layout: ParameterLayout, x: np.ndarray
) -> list[EquationRow]:
    """*observation*'s computed value and partials in the geocentric frame.

    An observation type the geocentric frame has no equation for is refused, naming the ones it has.
    """
    equation = _EQUATIONS.get(observation.type)
    if equation is None:
        raise ValidationError(
            "observation_type_not_geocentric",
            observation=observation.id,
            type=observation.type.value,
            expected=sorted(t.value for t in GEOCENTRIC_TYPES),
        )
    return equation(observation, layout, x)
