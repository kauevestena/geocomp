# SPDX-License-Identifier: GPL-2.0-or-later
"""Survey computations: traverse, resection, intersection, radiation.

``specs/09-module-total-station.md`` section 4 (FR-406 to FR-409, FR-411).

All of these are built on the in-house adjustment core
(:mod:`geocomp.core.adjustment`), and all of them also produce approximate
coordinates suitable as starting values for a rigorous network adjustment --
which is the other reason they exist. A traverse that has been "adjusted" by the
compass rule is, for a least-squares network, a set of very good approximate
coordinates.

**The classical rules are offered alongside least squares, and clearly
distinguished** (FR-406). The compass and transit rules are what students are
taught and what many specifications still require; they are not least squares
and they do not produce a rigorous covariance, so their results are labelled
``APPROXIMATE``. Presenting both on the same data is directly pedagogically
valuable: the student sees what the classical rule approximates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.findings import Finding, Severity
from geocomp.core.uncertainty import Covariance, Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit, wrap_to_2pi, wrap_to_pi

__all__ = [
    "DANGER_CIRCLE_TOLERANCE",
    "IntersectionResult",
    "Leg",
    "RadiationResult",
    "ResectionResult",
    "TraverseAdjustment",
    "TraverseKind",
    "TraverseResult",
    "adjust_traverse",
    "forward_intersection",
    "radiate",
    "resection",
]

#: How close to the danger circle counts as on it. Expressed as a relative
#: departure of the occupied point from the circle through the three known
#: points: ``|d(P, centre) - radius| / radius``. One part in a thousand is
#: already enough to make the solution useless, and the threshold is generous
#: rather than tight because the failure is catastrophic and silent.
DANGER_CIRCLE_TOLERANCE = 1.0e-3


class TraverseKind(Enum):
    """Which of the three traverse forms is being computed.

    The distinction is not cosmetic: it decides what misclosure means, and
    whether there is one at all.
    """

    #: Starts and ends on the same known point and orientation. Both misclosures
    #: are checkable.
    CLOSED = "closed"
    #: Starts on one known point and orientation and ends on another
    #: (*enquadrada*). Both misclosures are checkable.
    CONNECTED = "connected"
    #: Starts known, ends nowhere. **No misclosure exists**, which means no
    #: check exists: an open traverse cannot be verified, and GeoComp says so
    #: rather than reporting a misclosure of zero.
    OPEN = "open"


class TraverseAdjustment(Enum):
    """How a traverse's misclosure is distributed.

    ``COMPASS`` (Bowditch) distributes proportionally to leg length; ``TRANSIT``
    proportionally to the leg's latitude and departure. Neither is least
    squares, and neither produces a rigorous covariance.
    """

    COMPASS = "compass"
    TRANSIT = "transit"
    NONE = "none"


@dataclass(frozen=True)
class Leg:
    """One traverse leg: a horizontal angle at the *from* station, then a distance.

    Attributes:
        angle: The angle at ``origin``, measured from the previous station to
            ``target``, clockwise. For the first leg this is the angle from the
            backsight.
    """

    origin: str
    target: str
    angle: Quantity
    distance: Quantity

    def __post_init__(self) -> None:
        if self.angle.unit is not Unit.RADIAN:
            raise ValidationError(
                "leg_angle_wrong_unit",
                leg=f"{self.origin}-{self.target}",
                received=self.angle.unit.name,
                expected=Unit.RADIAN.name,
            )
        if self.distance.unit is not Unit.METRE:
            raise ValidationError(
                "leg_distance_wrong_unit",
                leg=f"{self.origin}-{self.target}",
                received=self.distance.unit.name,
                expected=Unit.METRE.name,
            )


@dataclass(frozen=True)
class TraverseResult:
    """A computed traverse, with its misclosures and its verdict.

    Attributes:
        coordinates: Station id to (easting, northing), after adjustment.
        angular_misclosure: Radians. ``None`` for an open traverse, where none
            exists -- distinct from zero, which would claim a perfect closure.
        linear_misclosure: Metres, the length of the closing vector.
        perimeter: Total measured length. A sum of measured distances, so it
            carries their combined uncertainty rather than being a bare total.
        relative_precision: Perimeter divided by linear misclosure, as the
            denominator surveyors quote: 5000 means 1:5000. ``None`` when there
            is no misclosure to compare, or when it is exactly zero.
        method: Which rule distributed the misclosure.
    """

    kind: TraverseKind
    coordinates: dict[str, tuple[Quantity, Quantity]]
    perimeter: Quantity
    angular_misclosure: float | None
    linear_misclosure: float | None
    relative_precision: float | None
    method: TraverseAdjustment
    findings: tuple[Finding, ...] = ()

    @property
    def is_checkable(self) -> bool:
        """Whether this traverse can be verified at all."""
        return self.kind is not TraverseKind.OPEN


@dataclass(frozen=True)
class ResectionResult:
    """Coordinates of an occupied station from sightings to known points."""

    position: tuple[Quantity, Quantity]
    covariance: Covariance
    orientation: Quantity
    residuals: dict[str, float]
    findings: tuple[Finding, ...] = ()

    @property
    def is_reliable(self) -> bool:
        return not any(f.severity is Severity.BLOCKING for f in self.findings)


@dataclass(frozen=True)
class IntersectionResult:
    """Coordinates of a sighted point from two or more known stations."""

    position: tuple[Quantity, Quantity]
    covariance: Covariance
    residuals: dict[str, float]
    findings: tuple[Finding, ...] = ()


@dataclass(frozen=True)
class RadiationResult:
    """A point fixed in three dimensions from one setup (FR-411).

    The three coordinates come from one pointing and are strongly correlated
    through it, so the full 3x3 covariance is the result and the three
    individual sigmas are a view of it. Treating them as independent is wrong,
    which is why :attr:`covariance` is not optional.
    """

    target: str
    position: tuple[Quantity, Quantity, Quantity]
    covariance: Covariance


# -- traverse ------------------------------------------------------------


def adjust_traverse(
    legs: list[Leg],
    start: tuple[Quantity, Quantity],
    start_azimuth: Quantity,
    *,
    kind: TraverseKind = TraverseKind.CLOSED,
    close_to: tuple[Quantity, Quantity] | None = None,
    close_azimuth: Quantity | None = None,
    method: TraverseAdjustment = TraverseAdjustment.COMPASS,
    angular_tolerance_per_station: float = 1.45e-4,
    relative_precision_limit: float = 5000.0,
) -> TraverseResult:
    """Compute and adjust a traverse by a classical rule (FR-406).

    Args:
        legs: In order. Each carries the angle turned at its origin and the
            distance to its target.
        start / start_azimuth: The known point and the orientation of the first
            backsight.
        close_to / close_azimuth: For a closed or connected traverse, the known
            point and orientation it must arrive at. A closed traverse closes on
            its own start.
        method: Which classical rule distributes the misclosure, or
            :attr:`TraverseAdjustment.NONE` to leave it undistributed and only
            report it.
        angular_tolerance_per_station: The angular misclosure allowed per
            station, radians. The default is 30 arcseconds.
        relative_precision_limit: The linear misclosure must be better than
            1 in this.

    Returns:
        The adjusted coordinates, **labelled approximate**. A classical
        distribution is not least squares: it produces no residuals, no
        redundancy numbers and no rigorous covariance, and the returned
        uncertainties are the misclosure spread over the traverse rather than a
        propagated variance. FR-203 requires that distinction survive to the
        result, so it does.
    """
    if not legs:
        raise ValidationError(
            "traverse_without_legs", expected="at least one leg between two stations"
        )

    if kind is not TraverseKind.OPEN and close_to is None:
        if kind is TraverseKind.CLOSED:
            close_to = start
        else:
            raise ValidationError(
                "connected_traverse_without_closing_point",
                expected="the known point the traverse arrives at",
            )

    findings: list[Finding] = []
    azimuths, positions, perimeter = _run_traverse(legs, start, start_azimuth)

    angular_misclosure = None
    if kind is not TraverseKind.OPEN and close_azimuth is not None:
        angular_misclosure = wrap_to_pi(azimuths[-1] - close_azimuth.value)
        allowed = angular_tolerance_per_station * math.sqrt(len(legs))
        if abs(angular_misclosure) > allowed:
            findings.append(
                Finding(
                    code="angular_misclosure_beyond_tolerance",
                    severity=Severity.WARNING,
                    message=(
                        f"the angular misclosure is "
                        f"{math.degrees(angular_misclosure) * 3600:.1f} arcsec over "
                        f"{len(legs)} station(s), against a tolerance of "
                        f"{math.degrees(allowed) * 3600:.1f} arcsec"
                    ),
                    value=abs(angular_misclosure),
                    threshold=allowed,
                )
            )
        # Distribute the angular misclosure equally before the linear one, which
        # is the classical order: an uncorrected angular error would otherwise
        # be redistributed as if it were a linear one.
        azimuths, positions, perimeter = _run_traverse(
            legs, start, start_azimuth, angular_correction=-angular_misclosure / len(legs)
        )

    linear_misclosure = None
    relative_precision = None
    if close_to is not None:
        closing = (
            positions[-1][0] - close_to[0].value,
            positions[-1][1] - close_to[1].value,
        )
        linear_misclosure = math.hypot(*closing)
        if linear_misclosure > 0.0:
            relative_precision = perimeter.value / linear_misclosure
            if relative_precision < relative_precision_limit:
                findings.append(
                    Finding(
                        code="relative_precision_beyond_tolerance",
                        severity=Severity.WARNING,
                        message=(
                            f"the traverse closes to 1:{relative_precision:.0f} over "
                            f"{perimeter.value:.1f} m, against a required 1:"
                            f"{relative_precision_limit:.0f}"
                        ),
                        value=relative_precision,
                        threshold=relative_precision_limit,
                    )
                )
    else:
        findings.append(
            Finding(
                code="open_traverse_unchecked",
                severity=Severity.WARNING,
                message=(
                    "this traverse does not close on a known point, so no misclosure "
                    "exists and nothing about it can be checked. A blunder anywhere in it "
                    "would be invisible"
                ),
            )
        )

    coordinates = _distribute(legs, positions, _closing_error(positions, close_to), method, perimeter)

    return TraverseResult(
        kind=kind,
        coordinates=coordinates,
        perimeter=perimeter,
        angular_misclosure=angular_misclosure,
        linear_misclosure=linear_misclosure,
        relative_precision=relative_precision,
        method=method,
        findings=tuple(findings),
    )


def _closing_error(
    positions: list[tuple[float, float]], close_to: tuple[Quantity, Quantity] | None
) -> tuple[float, float]:
    """The vector from the computed end point to where it should have been."""
    if close_to is None:
        return 0.0, 0.0
    return close_to[0].value - positions[-1][0], close_to[1].value - positions[-1][1]


def _run_traverse(
    legs: list[Leg],
    start: tuple[Quantity, Quantity],
    start_azimuth: Quantity,
    *,
    angular_correction: float = 0.0,
) -> tuple[list[float], list[tuple[float, float]], Quantity]:
    """Walk the traverse, returning azimuths, positions and the perimeter."""
    azimuth = start_azimuth.value
    easting, northing = start[0].value, start[1].value

    azimuths: list[float] = []
    positions: list[tuple[float, float]] = [(easting, northing)]
    perimeter = Quantity.exact(0.0, Unit.METRE)

    for leg in legs:
        # Forward azimuth = back azimuth + interior angle, brought onto [0, 2pi).
        azimuth = wrap_to_2pi(azimuth + math.pi + leg.angle.value + angular_correction)
        azimuths.append(azimuth)
        easting += leg.distance.value * math.sin(azimuth)
        northing += leg.distance.value * math.cos(azimuth)
        positions.append((easting, northing))
        perimeter = perimeter + leg.distance.detached()

    return azimuths, positions, perimeter


def _distribute(
    legs: list[Leg],
    positions: list[tuple[float, float]],
    closing: tuple[float, float],
    method: TraverseAdjustment,
    perimeter: Quantity,
) -> dict[str, tuple[Quantity, Quantity]]:
    """Spread the linear misclosure over the traverse by the chosen rule.

    Compass (Bowditch): proportionally to the cumulative distance, on the
    assumption that angular and linear errors contribute comparably.

    Transit: proportionally to the cumulative latitude and departure
    separately, on the assumption that the angles are better than the
    distances. Which is right depends on the instrument, which is why both are
    offered rather than one being chosen for the user.
    """
    stations = [legs[0].origin] + [leg.target for leg in legs]
    corrections: list[tuple[float, float]] = [(0.0, 0.0)]

    if method is TraverseAdjustment.NONE or closing == (0.0, 0.0):
        corrections.extend((0.0, 0.0) for _ in legs)
    elif method is TraverseAdjustment.COMPASS:
        travelled = 0.0
        for leg in legs:
            travelled += leg.distance.value
            share = travelled / perimeter.value if perimeter.value else 0.0
            corrections.append((closing[0] * share, closing[1] * share))
    else:
        total_departure = sum(
            abs(positions[i + 1][0] - positions[i][0]) for i in range(len(legs))
        )
        total_latitude = sum(
            abs(positions[i + 1][1] - positions[i][1]) for i in range(len(legs))
        )
        departure = latitude = 0.0
        for index in range(len(legs)):
            departure += abs(positions[index + 1][0] - positions[index][0])
            latitude += abs(positions[index + 1][1] - positions[index][1])
            corrections.append(
                (
                    closing[0] * (departure / total_departure if total_departure else 0.0),
                    closing[1] * (latitude / total_latitude if total_latitude else 0.0),
                )
            )

    # The uncertainty a classical rule can honestly claim: the misclosure it
    # had to absorb, spread over the traverse. It is not a propagated variance
    # and must not be presented as one.
    spread = math.hypot(*closing) / math.sqrt(len(legs)) if legs else 0.0

    adjusted: dict[str, tuple[Quantity, Quantity]] = {}
    for index, station in enumerate(stations):
        easting, northing = positions[index]
        correction = corrections[index]
        sigma = spread * (index / len(legs)) if legs else 0.0
        adjusted[station] = (
            _approximate(easting + correction[0], sigma),
            _approximate(northing + correction[1], sigma),
        )
    return adjusted


def _approximate(value: float, sigma: float) -> Quantity:
    """A coordinate from a classical distribution: approximate, and says so."""
    return Quantity.approximate(
        value, max(sigma, 1e-6), Unit.METRE, Strategy.DOMINANT_TERM
    )


# -- resection -----------------------------------------------------------


def resection(
    known: dict[str, tuple[Quantity, Quantity]],
    directions: dict[str, Quantity],
    *,
    approximate: tuple[float, float] | None = None,
    max_iterations: int = 20,
    convergence: float = 1e-6,
) -> ResectionResult:
    """Coordinates of the occupied station from directions to known points (FR-407).

    The general least-squares solution over *n* points, with the orientation of
    the setup as a third unknown. Three points give a unique solution; more give
    residuals and a covariance.

    **The danger circle is detected, not solved.** When the occupied station
    lies on the circle through three known points, the problem is
    indeterminate -- every point on that circle sees the three in the same
    directions -- and the normal matrix is singular or nearly so. Returning a
    numerically noisy answer there would be worse than refusing, because it
    looks like a coordinate.

    Args:
        directions: Reduced circle readings to each known point. Their common
            unknown orientation is estimated along with the position, which is
            why directions rather than azimuths are the input.
    """
    if len(known) < 3:
        raise ValidationError(
            "resection_needs_three_points",
            received=len(known),
            expected="at least three known points; two directions cannot fix a position "
            "and an orientation",
        )
    missing = sorted(set(directions) - set(known))
    if missing:
        raise ValidationError(
            "resection_direction_to_unknown_point",
            received=missing,
            expected="a known position for every point sighted",
        )

    # Checked up front when an approximate position is available, because that
    # is when a useful message can still be produced -- and because the
    # iteration below will simply fail on a danger-circle geometry, with a
    # message about a singular matrix that says nothing a surveyor can act on.
    findings = list(_danger_circle_findings(known, approximate))
    _refuse_if_on_the_danger_circle(findings)

    x, y = approximate if approximate is not None else _resection_start(known, directions)
    orientation = 0.0

    for _iteration in range(max_iterations):
        design_rows: list[list[float]] = []
        misclosures: list[float] = []
        weights: list[float] = []

        for point, direction in sorted(directions.items()):
            east, north = known[point][0].value, known[point][1].value
            d_east, d_north = east - x, north - y
            squared = d_east**2 + d_north**2
            if squared <= 0.0:
                raise ComputationError(
                    "resection_on_a_known_point",
                    point=point,
                    expected="an occupied station distinct from every point sighted",
                )
            bearing = math.atan2(d_east, d_north)
            # d(bearing)/dx and /dy, then the orientation unknown.
            design_rows.append([-d_north / squared, d_east / squared, -1.0])
            misclosures.append(wrap_to_pi(direction.value - (bearing - orientation)))
            weights.append(1.0 / max(direction.variance, 1e-30))

        design = np.array(design_rows)
        weight = np.diag(weights)
        normal = design.T @ weight @ design
        if not _is_invertible(normal):
            # The singularity has a name in this problem, and naming it is the
            # difference between a message a surveyor can act on and one they
            # cannot. Re-run the geometric check at the current iterate, which
            # by now is close enough to the station for it to be meaningful.
            _refuse_if_on_the_danger_circle(_danger_circle_findings(known, (x, y)))
            raise ComputationError(
                "resection_indeterminate",
                expected=(
                    "a geometry that determines the station. The normal matrix is "
                    "singular and the known points are not on a common circle through the "
                    "station, so check the directions for a blunder"
                ),
            )
        correction = np.linalg.solve(normal, design.T @ weight @ np.array(misclosures))
        x += correction[0]
        y += correction[1]
        orientation += correction[2]
        if max(abs(correction[0]), abs(correction[1])) < convergence:
            break
    else:
        raise ComputationError(
            "resection_did_not_converge",
            iterations=max_iterations,
            expected="a converged solution; check the approximate coordinates and the "
            "directions for a blunder",
        )

    cofactor = np.linalg.inv(normal)
    residuals = {
        point: float(value)
        for point, value in zip(sorted(directions), misclosures, strict=True)
    }

    covariance = Covariance(
        matrix=cofactor[:2, :2],
        labels=("easting", "northing"),
        units=(Unit.METRE, Unit.METRE),
        mode=UncertaintyMode.RIGOROUS,
    )
    return ResectionResult(
        position=(
            covariance.quantity("easting", x),
            covariance.quantity("northing", y),
        ),
        covariance=covariance,
        orientation=Quantity.from_std_dev(
            wrap_to_2pi(orientation), math.sqrt(max(cofactor[2, 2], 0.0)), Unit.RADIAN
        ),
        residuals=residuals,
        findings=tuple(findings),
    )


def _refuse_if_on_the_danger_circle(findings: list[Finding]) -> None:
    """Turn a blocking geometric finding into a refusal.

    ``specs/09`` section 4.2 requires the danger circle be "detected and
    reported, not returned as a numerically noisy answer". Every point on that
    circle sees the three known points in the same directions, so there is no
    answer to return -- and a number that looks like a coordinate is worse than
    no coordinate.
    """
    for finding in findings:
        if finding.severity is Severity.BLOCKING:
            raise ComputationError(
                f"resection_{finding.code}",
                stations=list(finding.stations),
                expected=finding.message,
            )


def _danger_circle_findings(
    known: dict[str, tuple[Quantity, Quantity]], approximate: tuple[float, float] | None
) -> list[Finding]:
    """Report a resection whose geometry is on or near the danger circle.

    Checked on the *approximate* position, before iterating, because that is
    when a useful message can still be produced. With more than three known
    points every triple is checked: one bad triple among four points weakens the
    solution even though the whole set determines it.
    """
    if approximate is None or len(known) < 3:
        return []

    import itertools

    findings: list[Finding] = []
    for triple in itertools.combinations(sorted(known), 3):
        circle = _circumcircle([(known[p][0].value, known[p][1].value) for p in triple])
        if circle is None:
            findings.append(
                Finding(
                    code="collinear_known_points",
                    severity=Severity.BLOCKING,
                    message=(
                        f"known points {', '.join(triple)} are collinear, so they define no "
                        "circle and cannot fix a resection between them"
                    ),
                    stations=triple,
                )
            )
            continue
        (centre_x, centre_y), radius = circle
        distance = math.hypot(approximate[0] - centre_x, approximate[1] - centre_y)
        departure = abs(distance - radius) / radius
        if departure < DANGER_CIRCLE_TOLERANCE:
            findings.append(
                Finding(
                    code="danger_circle",
                    severity=Severity.BLOCKING,
                    message=(
                        f"the occupied station lies on the danger circle through "
                        f"{', '.join(triple)}: every point on that circle sees the three in "
                        "the same directions, so they do not determine a position. Add a "
                        "fourth point off the circle, or a distance"
                    ),
                    stations=triple,
                    value=departure,
                    threshold=DANGER_CIRCLE_TOLERANCE,
                )
            )
    return findings


def _circumcircle(
    points: list[tuple[float, float]],
) -> tuple[tuple[float, float], float] | None:
    """Centre and radius of the circle through three points, or ``None``.

    ``None`` when they are collinear, which is a real configuration and not an
    error to raise on: three points in a line define no circle, and a resection
    between them is impossible for a different reason worth its own message.
    """
    (x1, y1), (x2, y2), (x3, y3) = points
    determinant = 2.0 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    scale = max(abs(x1), abs(x2), abs(x3), abs(y1), abs(y2), abs(y3), 1.0)
    if abs(determinant) < 1e-12 * scale**2:
        return None

    squared = (x1**2 + y1**2, x2**2 + y2**2, x3**2 + y3**2)
    centre_x = (
        squared[0] * (y2 - y3) + squared[1] * (y3 - y1) + squared[2] * (y1 - y2)
    ) / determinant
    centre_y = (
        squared[0] * (x3 - x2) + squared[1] * (x1 - x3) + squared[2] * (x2 - x1)
    ) / determinant
    return (centre_x, centre_y), math.hypot(x1 - centre_x, y1 - centre_y)


def _resection_start(
    known: dict[str, tuple[Quantity, Quantity]], directions: dict[str, Quantity]
) -> tuple[float, float]:
    """A starting point for the iteration: the centroid of the known points.

    Crude, and sufficient -- the resection equations converge from anywhere
    inside the figure. Deliberately not the circumcentre, which would start the
    iteration at the worst possible place.
    """
    eastings = [known[p][0].value for p in directions]
    northings = [known[p][1].value for p in directions]
    return sum(eastings) / len(eastings), sum(northings) / len(northings)


def _is_invertible(matrix: np.ndarray, tolerance: float = 1e10) -> bool:
    """Whether a small normal matrix can be inverted meaningfully."""
    if matrix.size == 0:
        return False
    try:
        condition = float(np.linalg.cond(matrix))
    except np.linalg.LinAlgError:  # pragma: no cover - defensive
        return False
    return math.isfinite(condition) and condition < tolerance


# -- forward intersection ------------------------------------------------


def forward_intersection(
    target: str,
    sightings: dict[str, tuple[tuple[Quantity, Quantity], Quantity]],
    *,
    approximate: tuple[float, float] | None = None,
    max_iterations: int = 20,
    convergence: float = 1e-6,
) -> IntersectionResult:
    """Coordinates of a sighted point from two or more known stations (FR-408).

    Args:
        sightings: Station id to (its known position, the **azimuth** to the
            target). Azimuths rather than directions: an intersection is
            computed from oriented stations, and where the orientation is
            unknown it is a resection first.

    Weak geometry -- near-parallel rays -- is reported *through the error
    ellipse's shape* rather than left for the user to discover, which
    ``specs/09`` section 4.3 asks for explicitly. A finding is added when the
    ellipse is more than ten times longer than it is wide.
    """
    if len(sightings) < 2:
        raise ValidationError(
            "intersection_needs_two_stations",
            received=len(sightings),
            expected="at least two stations sighting the target",
        )

    x, y = approximate if approximate is not None else _intersection_start(sightings)

    for _iteration in range(max_iterations):
        design_rows: list[list[float]] = []
        misclosures: list[float] = []
        weights: list[float] = []

        for station, (position, azimuth) in sorted(sightings.items()):
            east, north = position[0].value, position[1].value
            d_east, d_north = x - east, y - north
            squared = d_east**2 + d_north**2
            if squared <= 0.0:
                raise ComputationError(
                    "intersection_on_a_station",
                    station=station,
                    expected="a target distinct from every station sighting it",
                )
            bearing = math.atan2(d_east, d_north)
            design_rows.append([d_north / squared, -d_east / squared])
            misclosures.append(wrap_to_pi(azimuth.value - bearing))
            weights.append(1.0 / max(azimuth.variance, 1e-30))

        design = np.array(design_rows)
        weight = np.diag(weights)
        normal = design.T @ weight @ design
        if not _is_invertible(normal):
            raise ComputationError(
                "intersection_indeterminate",
                expected=(
                    "rays that actually cross. Near-parallel sightings do not determine a "
                    "point, however many of them there are"
                ),
            )
        correction = np.linalg.solve(normal, design.T @ weight @ np.array(misclosures))
        x += correction[0]
        y += correction[1]
        if max(abs(correction[0]), abs(correction[1])) < convergence:
            break
    else:
        raise ComputationError(
            "intersection_did_not_converge",
            iterations=max_iterations,
            expected="a converged solution; check the azimuths for a blunder",
        )

    cofactor = np.linalg.inv(normal)
    covariance = Covariance(
        matrix=cofactor,
        labels=("easting", "northing"),
        units=(Unit.METRE, Unit.METRE),
        mode=UncertaintyMode.RIGOROUS,
    )

    findings: list[Finding] = []
    eigenvalues = np.linalg.eigvalsh(cofactor)
    if eigenvalues[0] > 0.0:
        elongation = math.sqrt(eigenvalues[-1] / eigenvalues[0])
        if elongation > 10.0:
            findings.append(
                Finding(
                    code="weak_intersection_geometry",
                    severity=Severity.WARNING,
                    message=(
                        f"the rays to {target} are close to parallel: the error ellipse is "
                        f"{elongation:.0f} times longer than it is wide, so the point is "
                        "poorly determined along one direction however precise the "
                        "individual sightings are"
                    ),
                    stations=tuple(sorted(sightings)),
                    value=elongation,
                    threshold=10.0,
                )
            )

    return IntersectionResult(
        position=(covariance.quantity("easting", x), covariance.quantity("northing", y)),
        covariance=covariance,
        residuals={
            station: float(value)
            for station, value in zip(sorted(sightings), misclosures, strict=True)
        },
        findings=tuple(findings),
    )


def _intersection_start(
    sightings: dict[str, tuple[tuple[Quantity, Quantity], Quantity]],
) -> tuple[float, float]:
    """Close the first two rays analytically to start the iteration."""
    (first, second) = sorted(sightings)[:2]
    (p1, a1), (p2, a2) = sightings[first], sightings[second]
    x1, y1 = p1[0].value, p1[1].value
    x2, y2 = p2[0].value, p2[1].value

    s1, c1 = math.sin(a1.value), math.cos(a1.value)
    s2, c2 = math.sin(a2.value), math.cos(a2.value)
    determinant = s1 * c2 - s2 * c1
    if abs(determinant) < 1e-12:
        # Parallel rays. Return the midpoint and let the iteration's own
        # singularity check produce the diagnosis, which says more than a
        # duplicate one here would.
        return (x1 + x2) / 2.0, (y1 + y2) / 2.0

    t = ((x2 - x1) * c2 - (y2 - y1) * s2) / determinant
    return x1 + t * s1, y1 + t * c1


# -- 3D radiation --------------------------------------------------------


def radiate(
    target: str,
    station: tuple[Quantity, Quantity, Quantity],
    orientation: Quantity,
    horizontal: Quantity,
    zenith: Quantity,
    distance: Quantity,
    instrument_height: Quantity,
    target_height: Quantity,
    *,
    correlation: float | None = None,
) -> RadiationResult:
    """Fix a point in three dimensions from one setup (FR-411).

        E = E0 + d sin(z) sin(alpha + theta)
        N = N0 + d sin(z) cos(alpha + theta)
        U = U0 + d cos(z) + hi - hs

    with *alpha* the setup's orientation and *theta* the reduced circle reading.

    The three coordinates come from one pointing, so they are strongly
    correlated; the full 3x3 covariance is the result. ``specs/09`` section 4.6
    is explicit that treating them as independent is wrong, and this is the
    routine production case -- a detail survey radiates hundreds of points from
    one setup.
    """
    azimuth = orientation.value + horizontal.value
    sin_a, cos_a = math.sin(azimuth), math.cos(azimuth)
    sin_z, cos_z = math.sin(zenith.value), math.cos(zenith.value)
    d = distance.value
    horizontal_distance = d * sin_z

    inputs = {
        "orientation": orientation,
        "horizontal": horizontal,
        "zenith": zenith,
        "distance": distance,
        "instrument_height": instrument_height,
        "target_height": target_height,
        "station_easting": station[0],
        "station_northing": station[1],
        "station_up": station[2],
    }
    correlations = None
    strategies: set[Strategy] = set()
    if correlation is None:
        strategies.add(Strategy.INDEPENDENCE_ASSUMED)
    elif correlation:
        correlations = {("distance", "zenith"): correlation}

    covariance_in = Covariance.from_quantities(
        {name: quantity.detached() for name, quantity in inputs.items()},
        correlations=correlations,
    )

    order = list(inputs)
    jacobian = np.zeros((3, len(order)))

    def column(name: str) -> int:
        return order.index(name)

    # Easting.
    jacobian[0, column("orientation")] = horizontal_distance * cos_a
    jacobian[0, column("horizontal")] = horizontal_distance * cos_a
    jacobian[0, column("zenith")] = d * cos_z * sin_a
    jacobian[0, column("distance")] = sin_z * sin_a
    jacobian[0, column("station_easting")] = 1.0
    # Northing.
    jacobian[1, column("orientation")] = -horizontal_distance * sin_a
    jacobian[1, column("horizontal")] = -horizontal_distance * sin_a
    jacobian[1, column("zenith")] = d * cos_z * cos_a
    jacobian[1, column("distance")] = sin_z * cos_a
    jacobian[1, column("station_northing")] = 1.0
    # Up.
    jacobian[2, column("zenith")] = -d * sin_z
    jacobian[2, column("distance")] = cos_z
    jacobian[2, column("instrument_height")] = 1.0
    jacobian[2, column("target_height")] = -1.0
    jacobian[2, column("station_up")] = 1.0

    covariance = covariance_in.transform(
        jacobian,
        ["easting", "northing", "up"],
        [Unit.METRE, Unit.METRE, Unit.METRE],
        strategies=strategies,
    )

    values = (
        station[0].value + horizontal_distance * sin_a,
        station[1].value + horizontal_distance * cos_a,
        station[2].value + d * cos_z + instrument_height.value - target_height.value,
    )
    return RadiationResult(
        target=target,
        position=(
            covariance.quantity("easting", values[0]),
            covariance.quantity("northing", values[1]),
            covariance.quantity("up", values[2]),
        ),
        covariance=covariance,
    )
