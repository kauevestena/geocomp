# SPDX-License-Identifier: GPL-2.0-or-later
"""Two epochs brought face to face (``specs/14`` sections 2 to 4, FR-830 to FR-833).

Deformation analysis starts here: two solutions of the same network, checked
for everything that would make their difference something other than motion,
brought into one frame, and laid side by side component by component with the
covariance of their difference.

**What is refused, and what is only reported.** A solution without an epoch is
refused (FR-105): the difference of two unknown instants is not a displacement.
So are two solutions whose heights are of different types or were related to
the ellipsoid by different geoid models, whose datum definitions differ in a way
no transformation bridges, or whose frames cannot be reconciled -- each would
put a systematic difference into every displacement and call it motion. What
does not change the numbers -- a different engine, a station only one epoch
has -- is reported as a finding, because a monitoring series whose epochs were
processed differently is still worth knowing about.

**Datum definitions.** A free solution (inner or minimum constraint) differs
from another free one only by an S-transformation, which the analysis applies
over the reference block (``congruency.py``); two free solutions therefore
compare. So do two solutions held the same way. A free solution against a held
one does not: the held one has the constraint in its coordinates and no
transformation takes it out.

**Frames.** Geocentric solutions in different frames are transformed -- the
second into the first's frame, at the second's own epoch, never along a
velocity: moving a position between epochs is exactly the motion this module
exists to measure. The transformation's stated accuracy enters the second
epoch's covariance as a common translation of every station (FR-207): it moves
all of them together, so it disappears from anything measured relative to a
reference block and stays in an absolute displacement, which is where it is
true. Projected or local solutions must be in one coordinate reference system.

**Cross-covariance** (section 4). Two epochs that share reference stations, a
datum or GNSS products are correlated, and ignoring it overstates the
uncertainty of the difference -- which makes real motion look insignificant.
When it is not supplied the epochs are taken as independent, the result is
``APPROXIMATE`` with ``INDEPENDENCE_ASSUMED``, and :attr:`Comparison.bias` says
which way that errs.

**Cofactors and one variance factor.** Each solution carries ``sigma_0^2 Q``
with its own a-posteriori variance factor. The tests downstream are the
classical ones (Pelzer, Niemeier, Caspary): they use the cofactors of both
epochs with the **pooled** variance factor over their joint degrees of freedom,
so that the statistic is F-distributed under the null hypothesis that nothing
moved. The displacement covariance reported is that pooled factor times the
cofactor of the difference.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from geocomp.core.adjustment.geocentric import ELLIPSOID
from geocomp.core.errors import ValidationError
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic, enu_rotation
from geocomp.core.geodesy.frames import TransformationRecord, canonical_frame, transform_point
from geocomp.core.models import CoordinateSystem, DatumDefinition, Solution
from geocomp.core.uncertainty import Strategy, UncertaintyMode

__all__ = ["Comparison", "Finding", "compare"]

#: Where each component a solution estimates sits in its position triple.
_INDEX = {"e": 0, "n": 1, "u": 2, "h": 2, "x": 0, "y": 1, "z": 2}
#: The component sets a solution can have, smallest first, each in layout order.
_SETS = (("h",), ("e", "n"), ("e", "n", "u"), ("x", "y", "z"))
#: Free datum definitions: they differ from one another by an S-transformation.
_FREE = frozenset({DatumDefinition.INNER_CONSTRAINT, DatumDefinition.MINIMUM_CONSTRAINT})
#: What an input with no planimetry calls its CRS (``techniques/levelling/network.py``).
_NO_CRS = frozenset({"", "LOCAL"})

#: Which way independence errs, said in the result rather than left to the reader.
INDEPENDENCE_BIAS = (
    "the two epochs were taken as independent; if they share reference stations, a "
    "datum definition or GNSS products they are positively correlated, the true "
    "uncertainty of each displacement is smaller than the one stated, and the "
    "significance of real motion is understated"
)


@dataclass(frozen=True)
class Finding:
    """Something that differs between two epochs without refusing them.

    A code and its values rather than a sentence: the core does not phrase
    (``specs/18`` section 2), and the monitoring report says the same finding
    in three languages. ``str()`` gives the English, for logs and tests.

    Codes: ``engines_differ`` (``first``, ``second``: engine and version),
    ``datums_both_free`` (``first``, ``second``: datum definitions),
    ``stations_in_one_epoch`` (``stations``).
    """

    code: str
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        c = self.context
        if self.code == "engines_differ":
            return f"processed by different engines or versions: {c['first']} and {c['second']}"
        if self.code == "datums_both_free":
            return (
                f"datum definitions {c['first']} and {c['second']}: both free, related by the "
                "S-transformation onto the reference block"
            )
        if self.code == "stations_in_one_epoch":
            return f"stations in one epoch only, not compared: {', '.join(c['stations'])}"
        return self.code

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "context": dict(self.context)}


@dataclass(frozen=True)
class Comparison:
    """Two epochs of one network, aligned for deformation analysis.

    Attributes:
        stations: The stations both epochs estimate, in the first's order.
        components: What each station contributes, in order: ``("e", "n",
            "u")``, ``("e", "n")``, ``("h",)``, or for a geocentric solution
            ``("e", "n", "u")`` after turning into each station's horizon.
        first, second: The positions, stacked station by station.
        difference: ``second - first``.
        cofactor: The cofactor matrix of the difference, in units of
            :attr:`variance_factor`.
        first_covariance, second_covariance: Each epoch's own covariance over
            the compared components, turned as :attr:`difference` is -- what a
            time series plots.
        variance_factor: The pooled a-posteriori variance factor.
        degrees_of_freedom: The two epochs' together; zero means the variance
            factor is the a-priori one and the tests use chi-square.
        coordinates: Each station's first-epoch horizontal coordinates, in the
            frame the S-transformation's rotation needs (metres, local).
        transformations: What was applied to bring the second epoch across.
        findings: What differs between the epochs without refusing them.
        bias: The direction of any approximation's error, or empty.
    """

    first_solution: str
    second_solution: str
    first_epoch: float
    second_epoch: float
    stations: tuple[str, ...]
    components: tuple[str, ...]
    first: np.ndarray
    second: np.ndarray
    difference: np.ndarray
    cofactor: np.ndarray
    variance_factor: float
    degrees_of_freedom: int
    coordinates: np.ndarray
    frame: str
    first_covariance: np.ndarray
    second_covariance: np.ndarray
    geocentric: bool = False
    mode: UncertaintyMode = UncertaintyMode.RIGOROUS
    strategies: frozenset[Strategy] = frozenset()
    transformations: tuple[TransformationRecord, ...] = ()
    findings: tuple[Finding, ...] = ()
    bias: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def dimension(self) -> int:
        return len(self.components)

    @property
    def covariance(self) -> np.ndarray:
        """The covariance of the difference: pooled variance factor times cofactor."""
        return self.variance_factor * self.cofactor

    def indices(self, stations: Sequence[str]) -> list[int]:
        """The rows of *stations*' components, in the order given."""
        k = self.dimension
        position = {s: i for i, s in enumerate(self.stations)}
        missing = [s for s in stations if s not in position]
        if missing:
            raise ValidationError(
                "monitoring_station_not_compared",
                stations=missing,
                expected=list(self.stations),
            )
        return [position[s] * k + c for s in stations for c in range(k)]


def compare(
    first: Solution,
    second: Solution,
    *,
    stations: Sequence[str] | None = None,
    cross_covariance: np.ndarray | None = None,
) -> Comparison:
    """Align *second* with *first* for deformation analysis.

    Args:
        stations: Restrict to these; by default every station both estimate.
        cross_covariance: ``Sigma_{x1 x2}`` over the compared components, in the
            order of the result (station by station, component by component,
            in the solutions' own coordinates -- X, Y, Z for a geocentric one).
            ``None`` takes the epochs as independent and says so.

    Raises:
        ValidationError: ``monitoring_solution_without_epoch`` and
            ``monitoring_solution_epoch_assumed`` (FR-105);
            ``monitoring_height_types_differ``, ``monitoring_geoid_models_differ``,
            ``monitoring_datum_incompatible``, ``monitoring_coordinate_systems_differ``,
            ``monitoring_frames_differ``, ``monitoring_frame_needs_velocity``,
            ``monitoring_no_common_stations``.
    """
    for solution in (first, second):
        if getattr(solution, "epoch", None) is None:
            raise ValidationError(
                "monitoring_solution_without_epoch",
                solution=solution.id,
                expected=(
                    "a reference epoch on every solution compared (FR-105): the "
                    "difference of two unknown instants is not a displacement"
                ),
            )
        if getattr(solution, "epoch_assumed", False):
            raise ValidationError(
                "monitoring_solution_epoch_assumed",
                solution=solution.id,
                received=solution.epoch.decimal_year,
                expected=(
                    "an epoch someone stated (FR-105): this one is an adjustment's "
                    "default, chosen because neither the run nor its network gave one"
                ),
            )
    findings = _check(first, second)
    system = _system(first)
    components = _components(first)
    if _components(second) != components:
        raise ValidationError(
            "monitoring_components_differ",
            received=[list(components), list(_components(second))],
            expected="both epochs adjusted in the same dimension",
        )

    common = [s.station_id for s in first.adjusted_stations if _has(second, s.station_id)]
    if stations is not None:
        unknown = [s for s in stations if s not in common]
        if unknown:
            raise ValidationError(
                "monitoring_station_not_in_both",
                stations=unknown,
                expected=common,
            )
        common = [s for s in common if s in set(stations)]
    only = sorted(
        {s.station_id for s in first.adjusted_stations} ^ {s.station_id for s in second.adjusted_stations}
    )
    if only:
        findings.append(Finding("stations_in_one_epoch", {"stations": only}))
    if not common:
        raise ValidationError(
            "monitoring_no_common_stations",
            first=first.id,
            second=second.id,
            expected="at least one station both epochs estimate",
        )

    x1, s1 = _vector(first, common, components)
    x2, s2 = _vector(second, common, components)
    transformations: tuple[TransformationRecord, ...] = ()
    frame = (first.crs or "").strip()
    if system is CoordinateSystem.CARTESIAN:
        frame, x2, s2, transformations = _reconcile(first, second, x2, s2, len(common))
    else:
        _same_system(first, second)

    f1 = int(first.statistics.degrees_of_freedom or 0)
    f2 = int(second.statistics.degrees_of_freedom or 0)
    v1 = _variance_factor(first)
    v2 = _variance_factor(second)
    degrees = f1 + f2
    pooled = (f1 * v1 + f2 * v2) / degrees if degrees > 0 else 1.0
    q = s1 / v1 + s2 / v2
    mode, strategies, bias = UncertaintyMode.RIGOROUS, frozenset(), ""
    if cross_covariance is None:
        mode, strategies, bias = (
            UncertaintyMode.APPROXIMATE,
            frozenset({Strategy.INDEPENDENCE_ASSUMED}),
            INDEPENDENCE_BIAS,
        )
    else:
        cross = np.asarray(cross_covariance, dtype=float)
        if cross.shape != q.shape:
            raise ValidationError(
                "monitoring_cross_covariance_shape",
                received=list(cross.shape),
                expected=list(q.shape),
            )
        q = q - (cross + cross.T) / pooled

    difference = x2 - x1
    coordinates = _horizontal(first, common)
    geocentric = system is CoordinateSystem.CARTESIAN
    if geocentric:
        # Into each station's horizon: the tests' quadratic forms are unchanged
        # by an orthogonal turn, and east, north and up are what a component
        # test and a reader need.
        rotation = _rotation(x1, len(common))
        difference = rotation @ difference
        q = rotation @ q @ rotation.T
        s1, s2 = rotation @ s1 @ rotation.T, rotation @ s2 @ rotation.T
        x1, x2 = rotation @ x1, rotation @ x2
        components = ("e", "n", "u")

    return Comparison(
        first_solution=first.id,
        second_solution=second.id,
        first_epoch=first.epoch.decimal_year,
        second_epoch=second.epoch.decimal_year,
        stations=tuple(common),
        components=components,
        first=x1,
        second=x2,
        difference=difference,
        cofactor=(q + q.T) / 2.0,
        variance_factor=float(pooled),
        degrees_of_freedom=degrees,
        coordinates=coordinates,
        frame=frame,
        first_covariance=s1,
        second_covariance=s2,
        geocentric=geocentric,
        mode=mode,
        strategies=strategies,
        transformations=transformations,
        findings=tuple(findings),
        bias=bias,
    )


# -- checks ------------------------------------------------------------------


def _check(first: Solution, second: Solution) -> list[Finding]:
    """Refuse what would put a systematic difference into every displacement;
    return what differs without doing so."""
    heights = _height_types(first), _height_types(second)
    if heights[0] != heights[1]:
        raise ValidationError(
            "monitoring_height_types_differ",
            received=[sorted(heights[0]), sorted(heights[1])],
            solutions=[first.id, second.id],
            expected="heights of one type in both epochs",
        )
    geoids = _geoid_models(first), _geoid_models(second)
    if geoids[0] != geoids[1]:
        raise ValidationError(
            "monitoring_geoid_models_differ",
            received=[sorted(geoids[0]), sorted(geoids[1])],
            solutions=[first.id, second.id],
            expected=(
                "one geoid model in both epochs: heights computed with two models "
                "differ by the difference of the models, which is not motion"
            ),
        )
    d1, d2 = first.datum_definition, second.datum_definition
    if d1 != d2 and not ({d1, d2} <= _FREE):
        raise ValidationError(
            "monitoring_datum_incompatible",
            received=[d1.value, d2.value],
            solutions=[first.id, second.id],
            expected=(
                "the same datum definition in both epochs, or both free (inner or "
                "minimum constraint); a held solution carries its constraint in its "
                "coordinates, and no transformation takes it out"
            ),
        )
    findings: list[Finding] = []
    p1, p2 = first.provenance, second.provenance
    if p1 is not None and p2 is not None:
        e1 = " ".join(filter(None, (p1.engine or "in_house", p1.engine_version or "")))
        e2 = " ".join(filter(None, (p2.engine or "in_house", p2.engine_version or "")))
        if e1 != e2:
            findings.append(Finding("engines_differ", {"first": e1, "second": e2}))
    if d1 != d2:
        findings.append(Finding("datums_both_free", {"first": d1.value, "second": d2.value}))
    return findings


def _height_types(solution: Solution) -> set[str]:
    return {s.position.height_type.name for s in solution.adjusted_stations}


def _geoid_models(solution: Solution) -> set[str]:
    return {s.position.geoid_model for s in solution.adjusted_stations if s.position.geoid_model}


def _system(solution: Solution) -> CoordinateSystem:
    systems = {s.position.system for s in solution.adjusted_stations}
    if len(systems) != 1:
        raise ValidationError(
            "monitoring_mixed_coordinate_systems",
            solution=solution.id,
            received=sorted(s.value for s in systems),
        )
    return systems.pop()


def _same_system(first: Solution, second: Solution) -> None:
    if _system(second) is not _system(first):
        raise ValidationError(
            "monitoring_coordinate_systems_differ",
            received=[_system(first).value, _system(second).value],
            expected="both epochs in one coordinate system",
        )
    a, b = (first.crs or "").strip().upper(), (second.crs or "").strip().upper()
    if a != b and not (a in _NO_CRS and b in _NO_CRS):
        raise ValidationError(
            "monitoring_frames_differ",
            received=[first.crs, second.crs],
            solutions=[first.id, second.id],
            expected=(
                "one coordinate reference system for both epochs of a projected or "
                "local network; only geocentric solutions are transformed between frames"
            ),
        )


def _reconcile(first: Solution, second: Solution, x2, s2, count):
    """The second epoch's positions in the first's frame, at the second's epoch."""
    if _system(second) is not CoordinateSystem.CARTESIAN:
        raise ValidationError(
            "monitoring_coordinate_systems_differ",
            received=[CoordinateSystem.CARTESIAN.value, _system(second).value],
            expected="both epochs geocentric",
        )
    try:
        source, target = canonical_frame(second.crs), canonical_frame(first.crs)
    except ValidationError as error:
        raise ValidationError(
            "monitoring_frames_differ",
            received=[first.crs, second.crs],
            expected=error.context.get("expected"),
        ) from error
    if source == target:
        return target, x2, s2, ()
    epoch = second.epoch.decimal_year
    moved = np.empty_like(x2)
    linear = np.zeros((len(x2), len(x2)))
    record = None
    for i in range(count):
        block = slice(3 * i, 3 * i + 3)
        try:
            result = transform_point(x2[block], source=source, target=target, epoch=epoch, target_epoch=epoch)
        except ValidationError as error:
            raise ValidationError(
                "monitoring_frame_needs_velocity",
                received=[second.crs, first.crs],
                epoch=epoch,
                expected=(
                    "frames related at the second epoch itself: this pair is related only "
                    "at another epoch, and moving a position between epochs is the motion "
                    "being measured"
                ),
            ) from error
        moved[block] = result.xyz
        linear[block, block] = _step_matrix(x2[block], source, target, epoch)
        record = result.record
    covariance = linear @ s2 @ linear.T
    accuracy = record.accuracy if record is not None else 0.0
    if accuracy:
        # A common translation of every station, fully correlated (FR-207).
        common = np.kron(np.ones((count, count)), np.eye(3))
        covariance = covariance + accuracy**2 * common
    return target, moved, covariance, (record,) if record is not None else ()


def _step_matrix(xyz, source, target, epoch) -> np.ndarray:
    """The 3x3 derivative of the transformation at *xyz*. Helmert steps are
    linear, so differences over a metre are exact to rounding."""
    base = transform_point(xyz, source=source, target=target, epoch=epoch, target_epoch=epoch).xyz
    matrix = np.empty((3, 3))
    for k in range(3):
        nudged = np.array(xyz, dtype=float)
        nudged[k] += 1.0
        matrix[:, k] = (
            transform_point(nudged, source=source, target=target, epoch=epoch, target_epoch=epoch).xyz - base
        )
    return matrix


# -- vectors -----------------------------------------------------------------


def _components(solution: Solution) -> tuple[str, ...]:
    names: set[str] = set()
    labels = (
        solution.parameter_covariance.labels
        if solution.parameter_covariance is not None
        else tuple(label for s in solution.adjusted_stations if s.covariance for label in s.covariance.labels)
    )
    stations = {s.station_id for s in solution.adjusted_stations}
    for label in labels:
        station, _, component = label.rpartition(".")
        if station in stations and component in _INDEX:
            names.add(component)
    for candidate in _SETS:
        if names and names <= set(candidate):
            return candidate
    raise ValidationError(
        "monitoring_no_position_components",
        solution=solution.id,
        received=sorted(names),
        expected="a solution of positions: X, Y, Z; east, north, up; or heights",
    )


def _has(solution: Solution, station_id: str) -> bool:
    return any(s.station_id == station_id for s in solution.adjusted_stations)


def _vector(solution: Solution, stations: list[str], components: tuple[str, ...]):
    """Positions and their covariance over *stations*' *components*; a
    component the solution holds contributes its value and no variance."""
    k = len(components)
    values = np.empty(len(stations) * k)
    labels = [f"{s}.{c}" for s in stations for c in components]
    for i, station_id in enumerate(stations):
        position = solution.station(station_id).position
        for j, component in enumerate(components):
            values[i * k + j] = position.values[_INDEX[component]].value
    covariance = np.zeros((len(labels), len(labels)))
    source = solution.parameter_covariance
    if source is not None:
        where = {label: n for n, label in enumerate(source.labels)}
        present = [(n, where[label]) for n, label in enumerate(labels) if label in where]
        rows = [a for a, _ in present]
        columns = [b for _, b in present]
        covariance[np.ix_(rows, rows)] = np.asarray(source.matrix)[np.ix_(columns, columns)]
    else:
        for i, station_id in enumerate(stations):
            block = solution.station(station_id).covariance
            if block is None:
                continue
            where = {label: n for n, label in enumerate(block.labels)}
            present = [
                (i * k + j, where[f"{station_id}.{c}"])
                for j, c in enumerate(components)
                if f"{station_id}.{c}" in where
            ]
            rows = [a for a, _ in present]
            columns = [b for _, b in present]
            covariance[np.ix_(rows, rows)] = np.asarray(block.matrix)[np.ix_(columns, columns)]
    return values, covariance


def _variance_factor(solution: Solution) -> float:
    value = solution.statistics.variance_factor_aposteriori
    return float(value) if value and value > 0.0 else 1.0


def _rotation(xyz: np.ndarray, count: int) -> np.ndarray:
    blocks = []
    for i in range(count):
        latitude, longitude, _ = cartesian_to_geodetic(*xyz[3 * i : 3 * i + 3], ELLIPSOID)
        blocks.append(enu_rotation(latitude, longitude))
    out = np.zeros((3 * count, 3 * count))
    for i, block in enumerate(blocks):
        out[3 * i : 3 * i + 3, 3 * i : 3 * i + 3] = block
    return out


def _horizontal(solution: Solution, stations: list[str]) -> np.ndarray:
    """Each station's horizontal position in metres, in a plane: easting and
    northing as they are, or a geocentric one in the network's mean horizon."""
    positions = np.array([[q.value for q in solution.station(s).position.values] for s in stations])
    if _system(solution) is not CoordinateSystem.CARTESIAN:
        return positions[:, :2]
    centre = positions.mean(axis=0)
    latitude, longitude, _ = cartesian_to_geodetic(*centre, ELLIPSOID)
    rotation = enu_rotation(latitude, longitude)
    return ((positions - centre) @ rotation.T)[:, :2]
