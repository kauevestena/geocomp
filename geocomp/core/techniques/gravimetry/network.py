# SPDX-License-Identifier: GPL-2.0-or-later
"""Gravimetric networks: from reduced readings to adjusted station gravity (FR-700 to FR-703).

``specs/12-module-gravimetry.md`` sections 4.3 and 5.

**The pipeline.** Reduced readings (:mod:`.readings`) are grouped into
*occupations* -- a CG-5 records a reading a minute for as long as it stands on
a mark, and those are one visit, not sixty -- and the occupations of each
session become observations of gravity differences: successive differences
with the drift left in and estimated jointly, or differences from a base
station with a fitted drift already removed (:mod:`.drift`). Absolute values
enter as weighted ``GRAVITY`` observations. The adjustment is the in-house core,
unchanged: a gravity difference is a height difference in another unit
(ADR-0002, Amendment 1).

**The covariance is exact, not assembled from diagonals.** Every observation of
one instrument is a linear function of its occupations, ``z = A y``, so::

    C_z = A Sigma_y A^T  +  sigma_k^2 (A g)(A g)^T

The first term is why successive differences are correlated -- each occupation
but the first and last appears in two of them, with opposite signs -- and why
differences from a base share the base's fitted value. The second is the
calibration factor's uncertainty (FR-204): it multiplies every reading of the
instrument, so it is perfectly correlated across all of them, and ``A g`` is
what survives of it in each observation -- the difference itself, so the term
grows with ``|dg|`` exactly as ``specs/12`` section 4.1 requires. Both go into
one correlated cluster per instrument (FR-104).

Carrying the correlation is the default. ``DriftOptions(correlated=False)``
drops it, the way MCGravi and pyGrav do, and records that it did; it exists so
their published solutions can be reproduced (RD-07), not because it is better.

**What the result states.** The datum defect and how it was removed; which
drift treatment each session got and why; each session's drift with its
uncertainty; every uncheckable observation by name; and an
``uncertainty_mode`` on the solution that is approximate whenever anything that
went into it was (FR-703).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np

from geocomp.core.adjustment.datum import detect_defect
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    AdjustmentRun,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.adjustment.parameters import Frame, drift_component
from geocomp.core.errors import ValidationError
from geocomp.core.instruments.profiles import ProfileLibrary
from geocomp.core.models import (
    GRAVITY_COMPONENT,
    Cluster,
    ClusterKind,
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    DatumDefinition,
    Epoch,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Provenance,
    Solution,
    Station,
)
from geocomp.core.statistics.distributions import chi2_quantile
from geocomp.core.statistics.reliability import DEFAULT_ALPHA, DEFAULT_BETA, reliability
from geocomp.core.statistics.tests import data_snooping, global_test
from geocomp.core.techniques.gravimetry.drift import (
    DriftEstimate,
    DriftMode,
    DriftOptions,
    DriftTreatment,
    drift_is_estimable,
)
from geocomp.core.techniques.gravimetry.readings import ReducedReading
from geocomp.core.techniques.gravimetry.tides import TIDE_SYSTEM
from geocomp.core.uncertainty import (
    Covariance,
    Quantity,
    Strategy,
    UncertaintyMode,
    combine_modes,
)
from geocomp.core.units import Unit

__all__ = [
    "AbsoluteGravity",
    "DatumReport",
    "DriftPreview",
    "GravityNetwork",
    "GravityNetworkResult",
    "Occupation",
    "SessionReport",
    "TreatmentComparison",
    "adjust_gravity_network",
    "build_gravity_network",
    "compare_treatments",
    "drift_previews",
    "group_occupations",
]


@dataclass(frozen=True)
class Occupation:
    """One visit of one instrument to one mark: its readings, averaged.

    Attributes:
        id: ``<session>#<n>``, in time order within the session.
        instant: The readings' weighted mean time -- what the drift and the
            differences are evaluated at.
        gravity: The readings' weighted mean, m/s^2, with variance
            ``1 / sum(w)``. That treats the readings of one visit as
            independent, which a minute-by-minute series from a standing
            instrument is not quite; the strategy says so whenever more than
            one reading was averaged.
        instrument_gravity: The same mean of the readings before the
            calibration factor -- what the factor multiplies.
        readings: The ids averaged.
    """

    id: str
    station: str
    session: str
    instrument: str
    instant: datetime
    gravity: Quantity
    instrument_gravity: float
    readings: tuple[str, ...]


def group_occupations(reduced: list[ReducedReading]) -> list[Occupation]:
    """Group consecutive readings at one station, within a session, into visits."""
    by_session: dict[str, list[ReducedReading]] = {}
    for item in reduced:
        by_session.setdefault(item.reading.session, []).append(item)

    occupations: list[Occupation] = []
    for session in sorted(by_session):
        items = sorted(by_session[session], key=lambda r: r.reading.instant)
        instruments = {item.reading.instrument for item in items}
        if len(instruments) > 1:
            raise ValidationError(
                "gravity_session_mixes_instruments",
                session=session,
                received=sorted(instruments),
                expected="one instrument per session; drift belongs to an instrument",
            )
        runs: list[list[ReducedReading]] = []
        for item in items:
            if runs and runs[-1][-1].reading.station == item.reading.station:
                runs[-1].append(item)
            else:
                runs.append([item])
        for index, run in enumerate(runs):
            occupations.append(_occupation(f"{session}#{index + 1}", run))
    return occupations


def _occupation(occupation_id: str, run: list[ReducedReading]) -> Occupation:
    weights = [1.0 / item.gravity.variance for item in run]
    total = sum(weights)
    first = run[0].reading.instant
    offset = sum(
        w * (item.reading.instant - first).total_seconds() for w, item in zip(weights, run, strict=True)
    )
    mode, strategies = combine_modes(*(item.gravity for item in run))
    if len(run) > 1:
        mode, strategies = UncertaintyMode.APPROXIMATE, strategies | {Strategy.INDEPENDENCE_ASSUMED}
    gravity = Quantity(
        value=sum(w * item.gravity.value for w, item in zip(weights, run, strict=True)) / total,
        variance=1.0 / total,
        unit=Unit.ACCELERATION,
        mode=mode,
        strategies=frozenset(strategies),
    )
    return Occupation(
        id=occupation_id,
        station=run[0].reading.station,
        session=run[0].reading.session,
        instrument=run[0].reading.instrument,
        instant=first + timedelta(seconds=offset / total),
        gravity=gravity,
        instrument_gravity=sum(
            w * item.instrument_gravity for w, item in zip(weights, run, strict=True)
        )
        / total,
        readings=tuple(item.reading.id for item in run),
    )


@dataclass(frozen=True)
class AbsoluteGravity:
    """An absolute determination at a station, entering the adjustment weighted.

    Attributes:
        value: At the mark, m/s^2, with its published uncertainty. Weighted,
            never fixed: an absolute value has an uncertainty and should be
            used (``specs/12`` section 5).
        tide_system: The permanent-tide convention the value is published in.
            GeoComp's relative values are tide-free; a zero-tide absolute value
            differs by a latitude-dependent few microgal, and the result
            records the mismatch rather than converting silently.
    """

    id: str
    station: str
    value: Quantity
    tide_system: str = TIDE_SYSTEM
    source: str = ""

    def __post_init__(self) -> None:
        if self.value.unit is not Unit.ACCELERATION or not self.value.variance > 0.0:
            raise ValidationError(
                "absolute_gravity_invalid",
                observation=self.id,
                expected=(
                    "a gravity value in m/s^2 with its uncertainty; an absolute value "
                    "without one would be a fixed constraint under another name"
                ),
            )


@dataclass(frozen=True)
class SessionReport:
    """What one session contributed and how its drift was treated."""

    session: str
    instrument: str
    treatment: DriftTreatment
    occupations: int
    reference: datetime
    base_station: str | None = None
    precorrection: DriftEstimate | None = None


@dataclass
class GravityNetwork:
    """A gravity network ready to adjust, and how it was built."""

    network: Network
    drift_unknowns: dict[str, tuple[str, ...]]
    sessions: dict[str, SessionReport]
    occupations: tuple[Occupation, ...]
    options: DriftOptions
    notes: list[str] = field(default_factory=list)


def build_gravity_network(
    reduced: list[ReducedReading],
    profiles: ProfileLibrary,
    *,
    absolutes: tuple[AbsoluteGravity, ...] | list[AbsoluteGravity] = (),
    held: dict[str, Quantity] | None = None,
    drift: DriftOptions | None = None,
    stations: dict[str, Station] | None = None,
    network_id: str = "gravity",
    crs: str = "EPSG:4326",
    confidence: float = 0.95,
) -> GravityNetwork:
    """Turn reduced readings into an adjustable network.

    Args:
        reduced: From :func:`~geocomp.core.techniques.gravimetry.readings.reduce_readings`.
        profiles: For each instrument's calibration factor.
        absolutes: Absolute determinations, entering weighted.
        held: Stations whose gravity is held exactly, m/s^2 -- a datum
            chosen, not measured, so the result's uncertainties are relative
            to it. The station keeps the location its readings give it.
        drift: See :class:`~geocomp.core.techniques.gravimetry.drift.DriftOptions`.
        stations: Stations to use, with their locations and any gravity
            constraints. Stations not given are created at the location their
            readings were taken at, when the readings carry one.
        confidence: For the test of a pre-correction's base residuals.

    Raises:
        ValidationError: a session whose drift can be neither estimated nor
            pre-corrected, naming it and saying which occupations are missing.
    """
    options = drift or DriftOptions()
    occupations = group_occupations(reduced)
    if not occupations:
        raise ValidationError("gravity_network_without_readings", expected="at least one reading")

    sessions: dict[str, list[Occupation]] = {}
    for occupation in occupations:
        sessions.setdefault(occupation.session, []).append(occupation)

    network = Network(id=network_id, crs=crs)
    for station in _stations(reduced, occupations, absolutes, stations, crs, held or {}):
        network.add_station(station)

    reports: dict[str, SessionReport] = {}
    drift_unknowns: dict[str, tuple[str, ...]] = {}
    by_instrument: dict[str, list[_Row]] = {}
    for session, visits in sessions.items():
        report, rows = _session(session, visits, options, confidence)
        reports[session] = report
        by_instrument.setdefault(report.instrument, []).extend(rows)
        if report.treatment is DriftTreatment.JOINT:
            drift_unknowns[session] = tuple(drift_component(k) for k in range(1, options.degree + 1))

    for instrument, rows in by_instrument.items():
        factor = profiles.gravimeter(instrument).calibration_factor
        _add_instrument(network, instrument, rows, occupations, factor, options.correlated)

    for absolute in absolutes:
        network.add_observation(
            Observation(
                id=f"absolute:{absolute.id}",
                type=ObservationType.GRAVITY,
                stations=(absolute.station,),
                values=(absolute.value,),
                meta={"tide_system": absolute.tide_system, "source": absolute.source},
            )
        )

    network.require_valid()
    notes = _notes(absolutes, reduced)
    return GravityNetwork(
        network=network,
        drift_unknowns=drift_unknowns,
        sessions=reports,
        occupations=tuple(occupations),
        options=options,
        notes=notes,
    )


@dataclass(frozen=True)
class _Row:
    """One observation as a linear function of occupations: ``sum w_i y_i``."""

    id: str
    origin: str
    target: str
    weights: dict[str, float]
    meta: dict
    strategies: frozenset[Strategy] = frozenset()


def _session(
    session: str, visits: list[Occupation], options: DriftOptions, confidence: float
) -> tuple[SessionReport, list[_Row]]:
    reference = visits[0].instant
    elapsed = [(v.instant - reference).total_seconds() for v in visits]
    stations = [v.station for v in visits]
    estimable = drift_is_estimable(stations, elapsed, options.degree, options.time_scale)
    base = _base_station(session, stations, options)
    base_count = stations.count(base)
    can_precorrect = base_count >= options.degree + 1

    if options.mode is DriftMode.JOINT:
        if not estimable:
            raise ValidationError(
                "gravity_drift_not_estimable",
                session=session,
                degree=options.degree,
                expected=(
                    f"re-occupations enough to determine a degree-{options.degree} drift: "
                    "at least one station visited more than once, at enough different "
                    "times. A session that visits each station once cannot separate "
                    "drift from gravity"
                ),
            )
        rows = [
            _Row(
                id=f"{a.id}>{b.id}",
                origin=a.station,
                target=b.station,
                weights={a.id: -1.0, b.id: 1.0},
                meta={
                    "drift_owner": session,
                    "drift_elapsed_s": (ta, tb),
                    "drift_scale_s": options.time_scale,
                    "occupations": (a.id, b.id),
                },
            )
            for (a, ta), (b, tb) in zip(
                zip(visits, elapsed, strict=True), zip(visits[1:], elapsed[1:], strict=True), strict=False
            )
        ]
        report = SessionReport(session, visits[0].instrument, DriftTreatment.JOINT, len(visits), reference)
        return report, rows

    if not can_precorrect:
        raise ValidationError(
            "gravity_drift_base_insufficient",
            session=session,
            base_station=base,
            base_occupations=base_count,
            degree=options.degree,
            expected=(
                f"at least {options.degree + 1} readings of the base station, at different "
                f"times, to fit a degree-{options.degree} drift to"
            ),
        )
    return _precorrected(session, visits, elapsed, base, options, confidence)


def _base_station(session: str, stations: list[str], options: DriftOptions) -> str:
    wanted = (options.base_stations or {}).get(session)
    if wanted is not None:
        if wanted not in stations:
            raise ValidationError(
                "gravity_base_station_not_in_session",
                session=session,
                received=wanted,
                expected=sorted(set(stations)),
            )
        return wanted
    counts = {station: stations.count(station) for station in stations}
    most = max(counts.values())
    return next(station for station in stations if counts[station] == most)


def _precorrected(
    session: str,
    visits: list[Occupation],
    elapsed: list[float],
    base: str,
    options: DriftOptions,
    confidence: float,
) -> tuple[SessionReport, list[_Row]]:
    """Fit ``base + drift(tau)`` to the base visits and difference the rest against it."""
    degree = options.degree
    base_visits = [(v, t) for v, t in zip(visits, elapsed, strict=True) if v.station == base]
    design = np.array([[(t / options.time_scale) ** k for k in range(degree + 1)] for _, t in base_visits])
    weight = np.diag([1.0 / v.gravity.variance for v, _ in base_visits])
    normal = design.T @ weight @ design
    mapping = np.linalg.solve(normal, design.T @ weight)  # (degree+1) x m, over base visits
    ids = [v.id for v, _ in base_visits]
    values = np.array([v.gravity.value for v, _ in base_visits])

    redundancy = len(base_visits) - (degree + 1)
    verified: bool | None = None
    if redundancy > 0:
        residuals = design @ (mapping @ values) - values
        statistic = float(residuals @ weight @ residuals)
        verified = statistic <= chi2_quantile(confidence, redundancy)

    strategies = frozenset() if verified else frozenset({Strategy.MODEL_ASSUMED})
    rows: list[_Row] = []
    for visit, seconds in zip(visits, elapsed, strict=True):
        if visit.station == base:
            continue
        powers = np.array([(seconds / options.time_scale) ** k for k in range(degree + 1)])
        # y_j - (beta_0 + sum c_k tau_j^k): the visit minus the base's fitted
        # value at the same instant.
        weights = {visit.id: 1.0}
        for index, coefficient in zip(ids, powers @ mapping, strict=True):
            weights[index] = weights.get(index, 0.0) - float(coefficient)
        rows.append(
            _Row(
                id=f"{session}:{base}>{visit.id}",
                origin=base,
                target=visit.station,
                weights=weights,
                meta={
                    "drift_treatment": DriftTreatment.PRE_CORRECTED.value,
                    "session": session,
                    "occupations": (visit.id,),
                },
                strategies=strategies,
            )
        )

    covariance = mapping @ np.diag([v.gravity.variance for v, _ in base_visits]) @ mapping.T
    mode, inherited = combine_modes(*(v.gravity for v, _ in base_visits))
    if strategies:
        mode = UncertaintyMode.APPROXIMATE
    coefficients = tuple(
        Quantity(
            value=float(mapping[k] @ values),
            variance=float(covariance[k, k]),
            unit=Unit.ACCELERATION,
            mode=mode,
            strategies=inherited | strategies,
        )
        for k in range(1, degree + 1)
    )
    estimate = DriftEstimate(
        session=session,
        treatment=DriftTreatment.PRE_CORRECTED,
        coefficients=coefficients,
        covariance=Covariance(
            matrix=covariance[1:, 1:],
            labels=tuple(f"{session}.{drift_component(k)}" for k in range(1, degree + 1)),
            units=tuple(Unit.ACCELERATION for _ in range(degree)),
        ),
        time_scale=options.time_scale,
        reference=visits[0].instant,
        base_station=base,
        verified=verified,
    )
    report = SessionReport(
        session,
        visits[0].instrument,
        DriftTreatment.PRE_CORRECTED,
        len(visits),
        visits[0].instant,
        base_station=base,
        precorrection=estimate,
    )
    return report, rows


def _add_instrument(
    network: Network,
    instrument: str,
    rows: list[_Row],
    occupations: list[Occupation],
    factor: Quantity,
    correlated: bool,
) -> None:
    """Add one instrument's observations with the covariance ``A S A^T + s_k^2 (A g)(A g)^T``."""
    if not rows:
        return
    visits = {o.id: o for o in occupations if o.instrument == instrument}
    order = sorted({key for row in rows for key in row.weights})
    column = {key: index for index, key in enumerate(order)}
    design = np.zeros((len(rows), len(order)))
    for index, row in enumerate(rows):
        for key, weight in row.weights.items():
            design[index, column[key]] = weight

    y = np.array([visits[key].gravity.value for key in order])
    sigma = np.diag([visits[key].gravity.variance for key in order])
    unscaled = design @ np.array([visits[key].instrument_gravity for key in order])
    covariance = design @ sigma @ design.T + factor.variance * np.outer(unscaled, unscaled)
    values = design @ y

    independent = not correlated
    for index, row in enumerate(rows):
        members = [visits[key] for key in row.weights]
        mode, strategies = combine_modes(*(m.gravity for m in members), factor)
        strategies = strategies | row.strategies
        if row.strategies or independent:
            mode = UncertaintyMode.APPROXIMATE
        if independent:
            strategies = strategies | {Strategy.INDEPENDENCE_ASSUMED}
        network.add_observation(
            Observation(
                id=row.id,
                type=ObservationType.GRAVITY_DIFFERENCE,
                stations=(row.origin, row.target),
                values=(
                    Quantity(
                        value=float(values[index]),
                        variance=float(covariance[index, index]),
                        unit=Unit.ACCELERATION,
                        mode=mode,
                        strategies=frozenset(strategies),
                    ),
                ),
                instrument_id=instrument,
                cluster_id=None if independent or len(rows) == 1 else f"gravimeter:{instrument}",
                meta=dict(row.meta),
            )
        )
    if independent or len(rows) == 1:
        return
    ids = tuple(row.id for row in rows)
    network.add_cluster(
        Cluster(
            id=f"gravimeter:{instrument}",
            kind=ClusterKind.GENERIC,
            observation_ids=ids,
            covariance=Covariance(
                matrix=covariance,
                labels=ids,
                units=tuple(Unit.ACCELERATION for _ in ids),
            ),
        )
    )


def _stations(
    reduced: list[ReducedReading],
    occupations: list[Occupation],
    absolutes,
    given: dict[str, Station] | None,
    crs: str,
    held: dict[str, Quantity],
) -> list[Station]:
    names = {o.station for o in occupations} | {a.station for a in absolutes}
    given = given or {}
    unknown = sorted((set(given) | set(held)) - names)
    if unknown:
        raise ValidationError(
            "gravity_station_not_observed",
            received=unknown,
            expected="stations that at least one reading or absolute value refers to",
        )
    both = sorted(set(given) & set(held))
    if both:
        raise ValidationError(
            "gravity_station_held_twice",
            received=both,
            expected="each station either given with its own constraint or held here, not both",
        )
    located: dict[str, Position] = {}
    for item in reduced:
        reading = item.reading
        if reading.station in located or reading.latitude is None or reading.longitude is None:
            continue
        located[reading.station] = Position(
            values=(
                Quantity.exact(reading.latitude, Unit.RADIAN),
                Quantity.exact(reading.longitude, Unit.RADIAN),
                Quantity.exact(reading.height or 0.0, Unit.METRE),
            ),
            system=CoordinateSystem.GEODETIC,
            crs=crs,
            height_type=HeightType.ELLIPSOIDAL,
        )
    built = []
    for name in sorted(names):
        if name in given:
            built.append(given[name])
            continue
        constraint = (
            ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({GRAVITY_COMPONENT}),
                gravity=held[name],
            )
            if name in held
            else ConstraintSpec()
        )
        built.append(Station(id=name, approx_position=located.get(name), constraint=constraint))
    return built


def _notes(absolutes, reduced: list[ReducedReading]) -> list[str]:
    notes: list[str] = []
    systems = {a.tide_system for a in absolutes}
    if systems - {TIDE_SYSTEM}:
        notes.append(
            "absolute values given in the "
            + ", ".join(sorted(systems - {TIDE_SYSTEM}))
            + f" system are combined with {TIDE_SYSTEM} relative values without conversion; "
            "the difference is a latitude-dependent few microgal"
        )
    unreduced = sorted({r.reading.station for r in reduced if r.to_mark is None})
    if unreduced:
        notes.append(
            "readings at " + ", ".join(unreduced) + " carry no sensor height and were taken "
            "to refer to the mark"
        )
    return notes


@dataclass(frozen=True)
class DriftPreview:
    """What one session can say about its drift before any adjustment.

    Attributes:
        estimable: Whether the session's occupations determine its drift
            jointly -- something re-occupied at enough distinct times.
        base_station: The station a pre-correction would fit to: the most
            occupied, the earliest breaking a tie, unless one was named.
        base_occupations: How often that station was read.
        estimate: The drift fitted to the base's readings, when there are
            enough of them; ``None`` otherwise. A preview, not the answer: the
            joint estimate uses every re-occupation, not only the base's.
    """

    session: str
    instrument: str
    occupations: int
    estimable: bool
    base_station: str
    base_occupations: int
    estimate: DriftEstimate | None


def drift_previews(
    reduced: list[ReducedReading], options: DriftOptions | None = None, *, confidence: float = 0.95
) -> tuple[DriftPreview, ...]:
    """Each session's drift as its base readings show it (``specs/12`` section 4.3).

    What *Pre-processing* reports under "drift": whether each session can be
    estimated jointly, and the drift a base-station fit gives it. The network
    adjustment then treats the drift as the options say; nothing here is
    applied to the readings.
    """
    options = options or DriftOptions()
    sessions: dict[str, list[Occupation]] = {}
    for occupation in group_occupations(reduced):
        sessions.setdefault(occupation.session, []).append(occupation)
    previews = []
    for session in sorted(sessions):
        visits = sessions[session]
        reference = visits[0].instant
        elapsed = [(v.instant - reference).total_seconds() for v in visits]
        stations = [v.station for v in visits]
        base = _base_station(session, stations, options)
        count = stations.count(base)
        estimate = None
        if count >= options.degree + 1:
            report, _ = _precorrected(session, visits, elapsed, base, options, confidence)
            estimate = report.precorrection
        previews.append(
            DriftPreview(
                session=session,
                instrument=visits[0].instrument,
                occupations=len(visits),
                estimable=drift_is_estimable(stations, elapsed, options.degree, options.time_scale),
                base_station=base,
                base_occupations=count,
                estimate=estimate,
            )
        )
    return tuple(previews)


@dataclass(frozen=True)
class DatumReport:
    """What the relative observations left undetermined, and what determined it.

    Attributes:
        defect: Of the differences alone -- 1, the level of the whole network,
            for any connected network of differences (``specs/12`` section 5).
            Absolute values then remove it, which :attr:`removed_by` says.
        components: Which components, by name.
        removed_by: In words: a fixed station, weighted absolute values, or an
            inner constraint that leaves every value relative to their mean.
    """

    defect: int
    components: tuple[str, ...]
    removed_by: str


@dataclass(frozen=True)
class GravityNetworkResult:
    """An adjusted gravity network and everything the adjustment concluded.

    Attributes:
        solution: Adjusted gravity per station, at its location, with the
            observation results and statistics. Its ``uncertainty_mode`` is
            approximate whenever any input was (FR-703).
        run: The raw adjustment, for anything a Solution does not carry.
        datum: The detected defect and how it was removed.
        sessions: How each session's drift was treated.
        drift: Every session's drift, joint or pre-corrected.
        uncheckable: Observations whose redundancy number is near zero -- a
            blunder in one of these cannot be detected, and in a small, weakly
            redundant gravity network that is common (``specs/12`` section 5).
        notes: Assumptions the result depends on, in words.
    """

    solution: Solution
    run: AdjustmentRun
    datum: DatumReport
    sessions: dict[str, SessionReport]
    drift: dict[str, DriftEstimate]
    uncheckable: tuple[str, ...]
    tide_system: str
    notes: tuple[str, ...]

    def gravity(self, station: str) -> Quantity:
        for adjusted in self.solution.adjusted_stations:
            if adjusted.station_id == station:
                assert adjusted.gravity is not None
                return adjusted.gravity
        raise ValidationError(
            "gravity_station_not_in_solution",
            station=station,
            expected="a station of the adjusted network; a held station has no column",
        )


def adjust_gravity_network(
    built: GravityNetwork,
    *,
    confidence: float = 0.95,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    variance_factor_apriori: float = 1.0,
    solution_id: str = "gravity-adjustment",
    provenance: Provenance | None = None,
) -> GravityNetworkResult:
    """Adjust, test and report a gravity network (FR-700, FR-702, FR-250..FR-253)."""
    network = built.network
    datum, removed_by = _datum(network)
    options = AdjustmentOptions(
        frame=Frame.GRAVITY_1D,
        datum=datum,
        confidence=confidence,
        variance_factor_apriori=variance_factor_apriori,
        auxiliary=dict(built.drift_unknowns),
    )
    run = adjust(network, options)
    # Criterion 4 of specs/12 section 8 is about the *relative* observations:
    # differences alone leave the level of the whole network free, and that
    # defect is reported even when absolute values go on to remove it.
    relative = [o for o in network.active_observations if o.type is ObservationType.GRAVITY_DIFFERENCE]
    defect = detect_defect(relative, Frame.GRAVITY_1D)

    test = global_test(
        run.variance_factor_aposteriori,
        run.degrees_of_freedom,
        variance_factor_apriori=variance_factor_apriori,
        confidence=confidence,
    )
    snooping = data_snooping(
        run.residuals,
        run.cofactor_residuals,
        run.system.weight,
        run.system.row_labels,
        variance_factor=run.variance_factor_aposteriori,
        degrees_of_freedom=run.degrees_of_freedom,
        confidence=confidence,
    )
    reliability_report = reliability(
        run.cofactor_residuals,
        run.system.weight,
        run.system.design,
        run.cofactor_parameters,
        run.system.row_labels,
        alpha=alpha,
        beta=beta,
    )
    results = to_observation_results(run, snooping=snooping, reliability=reliability_report)
    instants = [o.instant for o in built.occupations]
    middle = instants[0] + (max(instants) - instants[0]) / 2
    solution = to_solution(
        run,
        network,
        solution_id=solution_id,
        crs=network.crs,
        epoch=Epoch.from_datetime(middle),
        datum=datum,
        observation_results=results,
        global_test=test,
        confidence=confidence,
        provenance=provenance,
    )

    drift = {
        session: report.precorrection
        for session, report in built.sessions.items()
        if report.precorrection is not None
    }
    for session, names in built.drift_unknowns.items():
        drift[session] = _joint_drift(run, built.sessions[session], names, built.options.time_scale)

    return GravityNetworkResult(
        solution=solution,
        run=run,
        datum=DatumReport(
            defect=defect.size,
            components=tuple(c.value for c in defect.components),
            removed_by=removed_by,
        ),
        sessions=dict(built.sessions),
        drift=drift,
        uncheckable=tuple(r.observation_id for r in results if r.is_uncheckable),
        tide_system=TIDE_SYSTEM,
        notes=tuple(built.notes),
    )


def _datum(network: Network) -> tuple[DatumDefinition, str]:
    fixed = sorted(
        s.id
        for s in network.stations.values()
        if s.constraint.mode is ConstraintMode.FIXED and GRAVITY_COMPONENT in s.constraint.components
    )
    weighted = sorted(
        s.id
        for s in network.stations.values()
        if s.constraint.mode is ConstraintMode.WEIGHTED and GRAVITY_COMPONENT in s.constraint.components
    )
    absolute = sorted(
        o.stations[0] for o in network.active_observations if o.type is ObservationType.GRAVITY
    )
    if fixed:
        return DatumDefinition.FIXED, "gravity held fixed at " + ", ".join(fixed)
    if absolute or weighted:
        return DatumDefinition.CONSTRAINED, "weighted absolute gravity at " + ", ".join(
            sorted(set(absolute) | set(weighted))
        )
    return (
        DatumDefinition.INNER_CONSTRAINT,
        "an inner constraint: the mean of the station values is held, so every value "
        "is relative to that mean and none is an absolute gravity",
    )


def _joint_drift(
    run: AdjustmentRun, report: SessionReport, names: tuple[str, ...], time_scale: float
) -> DriftEstimate:
    columns = [run.layout.column(report.session, name) for name in names]
    covariance = run.parameter_covariance[np.ix_(columns, columns)]
    # A jointly estimated drift is as approximate as the observations it came
    # from -- a modelled tide in every reading makes it so.
    mode, strategies = combine_modes(*(v for o in run.observations for v in o.values))
    return DriftEstimate(
        session=report.session,
        treatment=DriftTreatment.JOINT,
        coefficients=tuple(
            Quantity(
                value=float(run.parameters[c]),
                variance=float(run.parameter_covariance[c, c]),
                unit=Unit.ACCELERATION,
                mode=mode,
                strategies=strategies,
            )
            for c in columns
        ),
        covariance=Covariance(
            matrix=covariance,
            labels=tuple(f"{report.session}.{name}" for name in names),
            units=tuple(Unit.ACCELERATION for _ in names),
            mode=mode,
            strategies=strategies,
        ),
        time_scale=time_scale,
        reference=report.reference,
    )


@dataclass(frozen=True)
class TreatmentComparison:
    """Two adjustments of one network, station by station (``specs/12`` section 8, criterion 3).

    Attributes:
        differences: ``first - second`` per common station. The variance is the
            sum of the two **a priori** variances -- what the stated precision
            of the data allows each to be off by -- not the a posteriori ones:
            when a drift model is wrong the variance factor explodes and scales
            every a posteriori sigma with it, which would make any disagreement
            look insignificant exactly when it matters. The sum is also an upper
            bound, since both come from the same readings; the strategy says so.
        largest: The station whose difference is largest in magnitude.
        significant: Stations whose difference exceeds three of those standard
            deviations. By the conservative bound, so a station listed here
            really does differ by more than the data can explain.
    """

    differences: dict[str, Quantity]
    largest: str | None
    significant: tuple[str, ...]


def compare_treatments(first: GravityNetworkResult, second: GravityNetworkResult) -> TreatmentComparison:
    """Compare two adjustments of the same stations -- joint against pre-corrected, typically."""
    a, b = _apriori(first), _apriori(second)
    differences = {
        station: Quantity(
            value=a[station].value - b[station].value,
            variance=a[station].variance + b[station].variance,
            unit=Unit.ACCELERATION,
            mode=UncertaintyMode.APPROXIMATE,
            strategies=frozenset({Strategy.INDEPENDENCE_ASSUMED}),
        )
        for station in sorted(set(a) & set(b))
    }
    largest = max(differences, key=lambda s: abs(differences[s].value), default=None)
    significant = tuple(
        s for s, d in differences.items() if d.variance > 0 and abs(d.value) > 3.0 * math.sqrt(d.variance)
    )
    return TreatmentComparison(differences=differences, largest=largest, significant=significant)


def _apriori(result: GravityNetworkResult) -> dict[str, Quantity]:
    """Each station's adjusted gravity with its a priori variance."""
    run = result.run
    found: dict[str, Quantity] = {}
    for station in run.layout.station_ids():
        column = run.layout.column(station, "g")
        if column is None:
            continue
        found[station] = Quantity(
            value=float(run.parameters[column]),
            variance=float(run.variance_factor_apriori * run.cofactor_parameters[column, column]),
            unit=Unit.ACCELERATION,
        )
    return found
