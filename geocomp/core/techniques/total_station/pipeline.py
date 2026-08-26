# SPDX-License-Identifier: GPL-2.0-or-later
"""The generalised pre-processing pipeline, end to end (FR-400 to FR-405).

``specs/09-module-total-station.md`` section 2:

    raw readings -> face reduction -> instrument corrections -> atmospheric
      correction -> EDM corrections -> geometric reductions -> observations

Each stage is separately callable, which is the teaching requirement (``specs/01``
section 3, profile P1) and also what makes each one a Processing algorithm with
an inspectable output. This module is the composition of them, for the routine
case where a user wants the whole chain.

**Findings accumulate; they do not stop the run** (FR-166). A setup with a bad
face pair still produces the other pointings, and the report says what was
wrong with which. The one thing that *is* refused is producing an observation
from a pair carrying a blocking finding: a mean of two distances a metre apart
is not a measurement of anything, and passing it to an adjustment would let a
known-bad number acquire a residual and a standard deviation as though it were
real.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from geocomp.core.findings import Finding, Severity, worst_severity
from geocomp.core.instruments.profiles import InstrumentProfile, ProfileLibrary
from geocomp.core.models import (
    Cluster,
    ClusterKind,
    Observation,
    ObservationType,
)
from geocomp.core.techniques.total_station.atmosphere import (
    Atmosphere,
    apply_atmospheric_correction,
)
from geocomp.core.techniques.total_station.corrections import (
    apply_edm_corrections,
    apply_instrument_corrections,
)
from geocomp.core.techniques.total_station.face import (
    DEFAULT_COLLIMATION_TOLERANCE,
    FaceReduction,
    SetupDiagnostics,
    reduce_face_pair,
    reduce_single_face,
    setup_diagnostics,
)
from geocomp.core.techniques.total_station.readings import Setup
from geocomp.core.techniques.total_station.reductions import (
    BasicReduction,
    reduce_basic,
)
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

__all__ = [
    "PreprocessingOptions",
    "ProcessedPointing",
    "SetupResult",
    "preprocess_setup",
    "to_observations",
]


@dataclass(frozen=True)
class PreprocessingOptions:
    """How the chain is run.

    Attributes:
        collimation_tolerance: Radians, for the face-pair and drift diagnostics.
        distance_tolerance: Metres. ``None`` derives it from the instrument's
            EDM specification, which is the right threshold.
        distance_zenith_correlation: The correlation between a slope distance
            and its zenith angle, which share a pointing. ``None`` means unknown
            and is recorded as ``INDEPENDENCE_ASSUMED`` rather than silently
            treated as zero (``specs/05`` section 4.1).
        apply_atmospheric: Whether to run the first-velocity correction at all.
            Turning it off is a legitimate choice on short sights; doing so
            silently would not be, so it is a parameter.
    """

    collimation_tolerance: float = DEFAULT_COLLIMATION_TOLERANCE
    distance_tolerance: float | None = None
    distance_zenith_correlation: float | None = None
    apply_atmospheric: bool = True


@dataclass(frozen=True)
class ProcessedPointing:
    """One target, taken all the way through the chain.

    Attributes:
        reduction: The face reduction, with its diagnostics.
        basic: The reduced horizontal distance and height difference, with
            their joint covariance. ``None`` for an angles-only pointing.
        atmospheric_ppm: What the first-velocity correction applied, or ``None``
            when it was not run.
    """

    station: str
    target: str
    reduction: FaceReduction
    basic: BasicReduction | None = None
    atmospheric_ppm: Quantity | None = None
    findings: tuple[Finding, ...] = ()

    @property
    def is_usable(self) -> bool:
        """Whether this pointing may become an observation.

        False when anything blocking was found. The pointing is still returned
        and still reported -- a rejected measurement that vanishes from the
        output cannot be reconsidered (``specs/19`` section 2).
        """
        return not any(f.severity is Severity.BLOCKING for f in self.findings)


@dataclass(frozen=True)
class SetupResult:
    """Everything one instrument station produced."""

    station: str
    pointings: tuple[ProcessedPointing, ...]
    diagnostics: SetupDiagnostics
    findings: tuple[Finding, ...] = field(default_factory=tuple)

    @property
    def usable(self) -> tuple[ProcessedPointing, ...]:
        return tuple(p for p in self.pointings if p.is_usable)

    @property
    def all_findings(self) -> tuple[Finding, ...]:
        collected = list(self.findings) + list(self.diagnostics.findings)
        for pointing in self.pointings:
            collected.extend(pointing.findings)
        return tuple(collected)

    @property
    def severity(self) -> Severity | None:
        return worst_severity(self.all_findings)


def preprocess_setup(
    setup: Setup,
    library: ProfileLibrary,
    *,
    atmosphere: Atmosphere | None = None,
    options: PreprocessingOptions | None = None,
) -> SetupResult:
    """Run the whole chain over one instrument station.

    Args:
        atmosphere: Conditions at the setup. When ``None``, the setup's own
            recorded conditions are used; when it has none either, the
            atmospheric correction is skipped and the omission is reported --
            not silently defaulted, because a 10-degree error over a kilometre
            is 10 mm and the user should know it was assumed rather than
            measured.
    """
    options = options or PreprocessingOptions()
    instrument = library.instrument(setup.instrument_id)
    reflector = library.reflector(setup.reflector_id)

    conditions = atmosphere or _setup_atmosphere(setup)
    findings: list[Finding] = []
    if options.apply_atmospheric and conditions is None:
        findings.append(
            Finding(
                code="no_atmospheric_data",
                severity=Severity.INFO,
                message=(
                    f"station {setup.station} records no temperature or pressure, so the "
                    "first-velocity correction was not applied. On short sights this is "
                    "immaterial; over a kilometre a 10 degree error is 10 mm"
                ),
                stations=(setup.station,),
            )
        )

    reductions: list[FaceReduction] = []
    pointings: list[ProcessedPointing] = []

    for pair in setup.pairs:
        reduction = reduce_face_pair(
            pair,
            collimation_tolerance=options.collimation_tolerance,
            distance_tolerance=options.distance_tolerance,
            instrument=instrument,
        )
        reductions.append(reduction)
        pointings.append(
            _finish_pointing(
                setup, reduction, instrument, reflector, conditions, options, pair.direct.target_height
            )
        )

    for single in setup.singles:
        reduction = reduce_single_face(single, instrument)
        reductions.append(reduction)
        pointings.append(
            _finish_pointing(
                setup, reduction, instrument, reflector, conditions, options, single.target_height
            )
        )

    return SetupResult(
        station=setup.station,
        pointings=tuple(pointings),
        diagnostics=setup_diagnostics(
            setup, reductions, collimation_drift_tolerance=options.collimation_tolerance
        ),
        findings=tuple(findings),
    )


def _finish_pointing(
    setup: Setup,
    reduction: FaceReduction,
    instrument: InstrumentProfile,
    reflector,
    atmosphere: Atmosphere | None,
    options: PreprocessingOptions,
    target_height: Quantity | None,
) -> ProcessedPointing:
    """Instrument corrections, then EDM, then atmosphere, then basic reduction."""
    corrected = apply_instrument_corrections(reduction, instrument)
    findings = list(corrected.findings)

    distance = corrected.distance
    ppm: Quantity | None = None

    if distance is not None:
        edm = apply_edm_corrections(distance, instrument, reflector)
        findings.extend(edm.findings)
        distance = edm.distance

        if options.apply_atmospheric and atmosphere is not None:
            correction = apply_atmospheric_correction(distance, atmosphere, instrument)
            distance = correction.distance
            ppm = correction.ppm

    basic = None
    if distance is not None:
        basic = reduce_basic(
            distance,
            corrected.zenith,
            setup.instrument_height,
            target_height or Quantity.exact(0.0, Unit.METRE),
            correlation=options.distance_zenith_correlation,
        )

    return ProcessedPointing(
        station=setup.station,
        target=corrected.target,
        reduction=FaceReduction(
            target=corrected.target,
            horizontal=corrected.horizontal,
            zenith=corrected.zenith,
            distance=distance,
            collimation=corrected.collimation,
            vertical_index=corrected.vertical_index,
            distance_difference=corrected.distance_difference,
            set_number=corrected.set_number,
            findings=corrected.findings,
            single_face=corrected.single_face,
        ),
        basic=basic,
        atmospheric_ppm=ppm,
        findings=tuple(findings),
    )


def to_observations(
    result: SetupResult, *, prefix: str = ""
) -> tuple[list[Observation], list[Cluster]]:
    """Turn a processed setup into observations an adjustment can take.

    Directions from one setup become a ``DIRECTION_SET`` cluster (FR-104): they
    share the setup's unknown orientation, and splitting them into independent
    scalars would discard that and falsify every statistic downstream.

    Distances and zenith angles are emitted as individual observations. They are
    correlated with each other through the pointing, and that correlation is
    carried in :attr:`ProcessedPointing.basic`'s covariance -- wiring it into a
    cluster as well is phase P9's business, where combined adjustment needs it.

    Only usable pointings are converted. A pair with a blocking finding is left
    out, so a known-bad number cannot acquire a residual and a standard
    deviation as though it were real.
    """
    tag = prefix or result.station
    observations: list[Observation] = []
    clusters: list[Cluster] = []

    usable = [p for p in result.usable if p.basic is not None or p.reduction.distance is None]
    direction_ids: list[str] = []
    direction_quantities: list[Quantity] = []
    # Every direction belongs to the setup's cluster, including a lone one: the
    # orientation unknown exists whether or not a second target was sighted, and
    # the domain model refuses a DIRECTION without a cluster for exactly that
    # reason (FR-104).
    cluster_id = f"{tag}-directions"

    for pointing in usable:
        target = pointing.target
        direction_id = f"{tag}-dir-{target}"
        observations.append(
            Observation(
                id=direction_id,
                type=ObservationType.DIRECTION,
                stations=(result.station, target),
                values=(pointing.reduction.horizontal,),
                cluster_id=cluster_id,
            )
        )
        direction_ids.append(direction_id)
        direction_quantities.append(pointing.reduction.horizontal)

        observations.append(
            Observation(
                id=f"{tag}-zen-{target}",
                type=ObservationType.ZENITH_ANGLE,
                stations=(result.station, target),
                values=(pointing.reduction.zenith,),
            )
        )

        if pointing.reduction.distance is not None:
            observations.append(
                Observation(
                    id=f"{tag}-sd-{target}",
                    type=ObservationType.SLOPE_DISTANCE,
                    stations=(result.station, target),
                    values=(pointing.reduction.distance,),
                )
            )
        if pointing.basic is not None:
            observations.append(
                Observation(
                    id=f"{tag}-hd-{target}",
                    type=ObservationType.HORIZONTAL_DISTANCE,
                    stations=(result.station, target),
                    values=(pointing.basic.horizontal_distance.detached(),),
                )
            )

    if direction_ids:
        clusters.append(
            Cluster(
                id=cluster_id,
                kind=ClusterKind.DIRECTION_SET,
                observation_ids=tuple(direction_ids),
                covariance=Covariance(
                    matrix=np.diag([q.variance for q in direction_quantities]),
                    labels=tuple(direction_ids),
                    units=tuple(Unit.RADIAN for _ in direction_ids),
                    mode=direction_quantities[0].mode,
                    strategies=frozenset().union(
                        *(q.strategies for q in direction_quantities)
                    ),
                ),
            )
        )

    return observations, clusters


def _setup_atmosphere(setup: Setup) -> Atmosphere | None:
    """The setup's own recorded conditions, if it has a complete set."""
    if setup.temperature is None or setup.pressure is None:
        return None
    return Atmosphere(
        temperature=setup.temperature,
        pressure=setup.pressure,
        humidity=setup.humidity or Quantity.exact(0.0, Unit.DIMENSIONLESS),
    )
