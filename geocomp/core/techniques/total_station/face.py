# SPDX-License-Identifier: GPL-2.0-or-later
"""Face-left / face-right reduction and its diagnostics (FR-400).

``specs/09-module-total-station.md`` section 2.1.

Combining the two faces cancels collimation, horizontal-axis tilt and vertical
index error to first order. Two things about how it is done here are not
incidental:

**The horizontal mean is circular.** The two faces differ nominally by 180
degrees, so the reduction is the mean of the direct reading and the reverse
reading swung by half a turn -- and that mean must be taken on the circle. The
arithmetic mean is wrong whenever the pair straddles the zero of the horizontal
circle. This is not hypothetical: the prototype notebook that seeded RD-01 uses
the arithmetic form with a ``mean > 180`` branch, and it puts one of RD-01's own
six directions exactly 180 degrees away from the truth
(``specs/09`` section 2.1 and ``tests/test_reference_total_station.py``).

**The diagnostics are required output, not an option.** The pair carries
information the mean throws away -- the collimation, the index error, and the
agreement of the two distances -- and RD-01 contains a 1.000 m face-pair
distance discrepancy that averaging silently buries. Reporting it is what turns
a reduction into a check.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from geocomp.core.findings import Finding, Severity
from geocomp.core.instruments.profiles import InstrumentProfile
from geocomp.core.techniques.total_station.readings import Face, FacePair, FaceReading, Setup
from geocomp.core.uncertainty import Quantity, combine_modes
from geocomp.core.units import Unit, wrap_to_2pi, wrap_to_pi

__all__ = [
    "DEFAULT_COLLIMATION_TOLERANCE",
    "DEFAULT_DISTANCE_TOLERANCE",
    "FaceReduction",
    "SetupDiagnostics",
    "reduce_face_pair",
    "reduce_single_face",
    "setup_diagnostics",
]

#: Default tolerances, mirroring ``total_station.collimation_tolerance`` and
#: ``total_station.face_distance_tolerance`` in
#: :mod:`geocomp.core.settings_def`. Duplicated as constants so the core is
#: callable without a settings service, and kept equal by a test.
DEFAULT_COLLIMATION_TOLERANCE = 1.0e-4
DEFAULT_DISTANCE_TOLERANCE = 0.005


@dataclass(frozen=True)
class FaceReduction:
    """One face pair, reduced, with everything the pair revealed.

    Attributes:
        horizontal: The reduced circle reading, radians in ``[0, 2pi)``.
        zenith: The reduced zenith angle, radians.
        distance: The mean slope distance, or ``None`` for an angles-only pair.
        collimation: *c* = (H_direct - H_reverse +/- pi) / 2. Instrumental, and
            it should be stable across a setup.
        vertical_index: *i* = (V_direct + V_reverse - 2pi) / 2. Likewise.
        distance_difference: Direct minus reverse, metres, or ``None``. A plain
            float and not a Quantity because it is a *diagnostic* -- the
            difference of two readings of the same thing, whose expected value
            is zero.
        findings: What the pair says about itself. Empty is the normal case.
    """

    target: str
    horizontal: Quantity
    zenith: Quantity
    distance: Quantity | None
    collimation: Quantity
    vertical_index: Quantity
    distance_difference: float | None = None
    set_number: int = 1
    findings: tuple[Finding, ...] = ()
    #: True when the reduction came from a single face and the instrument's
    #: stored constants were applied instead of being cancelled by the pair.
    single_face: bool = False

    @property
    def blunder_candidates(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is Severity.BLOCKING)

    @property
    def is_clean(self) -> bool:
        return not self.findings


@dataclass(frozen=True)
class SetupDiagnostics:
    """What the instrumental constants did across one whole setup.

    A collimation that is constant across a setup is instrumental and harmless
    -- the face pairs cancel it. One that *drifts* means the instrument moved or
    was disturbed between pointings, and no amount of face pairing fixes that.
    Reporting the spread is the only way to tell the two apart.
    """

    station: str
    collimation_mean: float
    collimation_spread: float
    vertical_index_mean: float
    vertical_index_spread: float
    pair_count: int
    findings: tuple[Finding, ...] = field(default_factory=tuple)


def reduce_face_pair(
    pair: FacePair,
    *,
    collimation_tolerance: float = DEFAULT_COLLIMATION_TOLERANCE,
    distance_tolerance: float | None = None,
    instrument: InstrumentProfile | None = None,
) -> FaceReduction:
    """Reduce a direct/reverse pair to one pointing, with its diagnostics.

    Args:
        pair: The two pointings.
        collimation_tolerance: Radians. A collimation beyond this is reported;
            it is not an error, because a real instrument has one.
        distance_tolerance: Metres. Defaults to the instrument's own EDM
            specification at the measured distance when a profile is given --
            which is the right threshold, because "the two faces should agree
            within the EDM's precision" is exactly what the specification
            states. Falls back to :data:`DEFAULT_DISTANCE_TOLERANCE`.
        instrument: Used only for that default and for the expected constants.

    Returns:
        The reduced pointing. Findings are attached, never raised: a field book
        with several bad pairs must report all of them in one pass (FR-166).
    """
    direct, reverse = pair.direct, pair.reverse

    horizontal = _reduce_horizontal(direct.horizontal, reverse.horizontal)
    collimation = _collimation(direct.horizontal, reverse.horizontal)
    zenith = _reduce_zenith(direct.zenith, reverse.zenith)
    vertical_index = _vertical_index(direct.zenith, reverse.zenith)

    distance, difference = _reduce_distance(direct.distance, reverse.distance)

    findings: list[Finding] = []
    if abs(collimation.value) > collimation_tolerance:
        findings.append(
            Finding(
                code="collimation_beyond_tolerance",
                severity=Severity.WARNING,
                message=(
                    f"the face pair to {pair.target} implies a horizontal collimation of "
                    f"{math.degrees(collimation.value) * 3600:.1f} arcsec, beyond the "
                    f"{math.degrees(collimation_tolerance) * 3600:.1f} arcsec tolerance. The "
                    "pair still cancels it; a value this large means the instrument needs "
                    "adjustment, or the pointings were not to the same target"
                ),
                observations=(pair.target,),
                value=abs(collimation.value),
                threshold=collimation_tolerance,
            )
        )

    if abs(vertical_index.value) > collimation_tolerance:
        findings.append(
            Finding(
                code="vertical_index_beyond_tolerance",
                severity=Severity.WARNING,
                message=(
                    f"the face pair to {pair.target} implies a vertical index error of "
                    f"{math.degrees(vertical_index.value) * 3600:.1f} arcsec, beyond the "
                    f"{math.degrees(collimation_tolerance) * 3600:.1f} arcsec tolerance"
                ),
                observations=(pair.target,),
                value=abs(vertical_index.value),
                threshold=collimation_tolerance,
            )
        )

    if difference is not None:
        threshold = _distance_threshold(distance, distance_tolerance, instrument)
        if abs(difference) > threshold:
            findings.append(
                Finding(
                    # BLOCKING, not a warning. The two faces measure the same
                    # physical distance; a disagreement is not a property of the
                    # instrument, it is an error in one of the two numbers, and
                    # averaging them produces a value that is wrong by half the
                    # discrepancy while looking entirely ordinary.
                    code="face_distance_discrepancy",
                    severity=Severity.BLOCKING,
                    message=(
                        f"the two faces to {pair.target} disagree on the distance by "
                        f"{difference:+.4f} m, against a tolerance of {threshold:.4f} m. "
                        "The mean of the two is not a measurement of anything; check the "
                        "field book before using this pair"
                    ),
                    observations=(pair.target,),
                    value=abs(difference),
                    threshold=threshold,
                )
            )

    return FaceReduction(
        target=pair.target,
        horizontal=horizontal,
        zenith=zenith,
        distance=distance,
        collimation=collimation,
        vertical_index=vertical_index,
        distance_difference=difference,
        set_number=direct.set_number,
        findings=tuple(findings),
    )


def reduce_single_face(
    reading: FaceReading, instrument: InstrumentProfile
) -> FaceReduction:
    """Reduce a pointing that has no opposite face (FR-402).

    A face pair *cancels* the instrumental errors. A single face cannot, so
    they must be applied from the instrument profile instead -- with their own
    uncertainties, which is why the result is measurably worse than a pair's
    and says so through its variance rather than through a note.

    The sign convention is the one :func:`reduce_face_pair` produces: the
    reduced direct reading is ``H_direct - c``, so a single direct pointing has
    the stored *c* subtracted and a single reverse pointing has it added, after
    swinging by half a turn.
    """
    if reading.face is Face.DIRECT:
        horizontal = reading.horizontal - instrument.collimation
        zenith = reading.zenith - instrument.vertical_index
    else:
        horizontal = reading.horizontal + instrument.collimation - math.pi
        # A reverse zenith reads 2pi - z, so the index error enters with the
        # opposite sign and the reading itself must be reflected.
        zenith = 2.0 * math.pi - reading.zenith - instrument.vertical_index

    horizontal = Quantity(
        value=wrap_to_2pi(horizontal.value),
        variance=horizontal.variance,
        unit=Unit.RADIAN,
        mode=horizontal.mode,
        strategies=horizontal.strategies,
    )

    return FaceReduction(
        target=reading.target,
        horizontal=horizontal,
        zenith=zenith,
        distance=reading.distance,
        collimation=instrument.collimation,
        vertical_index=instrument.vertical_index,
        distance_difference=None,
        set_number=reading.set_number,
        single_face=True,
        findings=(
            Finding(
                code="single_face_pointing",
                severity=Severity.INFO,
                message=(
                    f"the pointing to {reading.target} was taken on one face only, so the "
                    "instrumental errors were corrected from the profile rather than "
                    "cancelled. Their uncertainties are included in the result"
                ),
                observations=(reading.target,),
            ),
        ),
    )


def setup_diagnostics(
    setup: Setup,
    reductions: list[FaceReduction],
    *,
    collimation_drift_tolerance: float = DEFAULT_COLLIMATION_TOLERANCE,
) -> SetupDiagnostics:
    """Summarise the instrumental constants across one setup.

    Args:
        collimation_drift_tolerance: Radians. The *spread* is compared against
            this, not the mean: a large but constant collimation is an
            instrument that needs adjusting, and the face pairs handled it. A
            large spread is the instrument or the tripod moving during the
            setup, which they did not.
    """
    pairs = [r for r in reductions if not r.single_face]
    if not pairs:
        return SetupDiagnostics(
            station=setup.station,
            collimation_mean=0.0,
            collimation_spread=0.0,
            vertical_index_mean=0.0,
            vertical_index_spread=0.0,
            pair_count=0,
        )

    collimations = [r.collimation.value for r in pairs]
    indices = [r.vertical_index.value for r in pairs]

    findings: list[Finding] = []
    collimation_spread = _spread(collimations)
    index_spread = _spread(indices)

    if collimation_spread > collimation_drift_tolerance:
        findings.append(
            Finding(
                code="collimation_drift",
                severity=Severity.WARNING,
                message=(
                    f"the collimation implied by the {len(pairs)} face pairs at station "
                    f"{setup.station} varies by {math.degrees(collimation_spread) * 3600:.1f} "
                    "arcsec. A collimation that is constant across a setup is instrumental "
                    "and harmless; one that drifts means the instrument was disturbed, and "
                    "face pairing does not fix that"
                ),
                stations=(setup.station,),
                value=collimation_spread,
                threshold=collimation_drift_tolerance,
            )
        )

    if index_spread > collimation_drift_tolerance:
        findings.append(
            Finding(
                code="vertical_index_drift",
                severity=Severity.WARNING,
                message=(
                    f"the vertical index error at station {setup.station} varies by "
                    f"{math.degrees(index_spread) * 3600:.1f} arcsec across its face pairs"
                ),
                stations=(setup.station,),
                value=index_spread,
                threshold=collimation_drift_tolerance,
            )
        )

    return SetupDiagnostics(
        station=setup.station,
        collimation_mean=sum(collimations) / len(collimations),
        collimation_spread=collimation_spread,
        vertical_index_mean=sum(indices) / len(indices),
        vertical_index_spread=index_spread,
        pair_count=len(pairs),
        findings=tuple(findings),
    )


# -- the arithmetic ------------------------------------------------------


def _reduce_horizontal(direct: Quantity, reverse: Quantity) -> Quantity:
    """Circular mean of the direct reading and the reverse reading less pi.

    Equivalent to ``H_direct - c``, and computed that way: expressing the mean
    as a small correction to one of the readings is numerically better than
    averaging two angles near the wrap, and it makes the wrap behaviour
    obvious rather than emergent.

    The variance is that of the mean of two readings, ``(v_d + v_r) / 4``. The
    circular mean is locally the arithmetic mean, so its Jacobian is
    ``[1/2, 1/2]`` and no approximation is involved.
    """
    correction = wrap_to_pi(direct.value - reverse.value + math.pi) / 2.0
    mode, strategies = combine_modes(direct, reverse)
    return Quantity(
        value=wrap_to_2pi(direct.value - correction),
        variance=(direct.variance + reverse.variance) / 4.0,
        unit=Unit.RADIAN,
        mode=mode,
        strategies=strategies,
    )


def _collimation(direct: Quantity, reverse: Quantity) -> Quantity:
    """c = (H_direct - H_reverse +/- pi) / 2, on the branch nearest zero."""
    mode, strategies = combine_modes(direct, reverse)
    return Quantity(
        value=wrap_to_pi(direct.value - reverse.value + math.pi) / 2.0,
        variance=(direct.variance + reverse.variance) / 4.0,
        unit=Unit.RADIAN,
        mode=mode,
        strategies=strategies,
    )


def _reduce_zenith(direct: Quantity, reverse: Quantity) -> Quantity:
    """V = (V_direct - V_reverse + 2pi) / 2.

    No wrap handling is needed: a zenith angle lives in ``(0, pi)`` on the
    direct face and ``(pi, 2pi)`` on the reverse, so the difference is around
    ``-pi`` and nowhere near a discontinuity. That asymmetry with the horizontal
    case is why only one of the two needs the circular treatment.
    """
    mode, strategies = combine_modes(direct, reverse)
    return Quantity(
        value=(direct.value - reverse.value + 2.0 * math.pi) / 2.0,
        variance=(direct.variance + reverse.variance) / 4.0,
        unit=Unit.RADIAN,
        mode=mode,
        strategies=strategies,
    )


def _vertical_index(direct: Quantity, reverse: Quantity) -> Quantity:
    """i = (V_direct + V_reverse - 2pi) / 2."""
    mode, strategies = combine_modes(direct, reverse)
    return Quantity(
        value=(direct.value + reverse.value - 2.0 * math.pi) / 2.0,
        variance=(direct.variance + reverse.variance) / 4.0,
        unit=Unit.RADIAN,
        mode=mode,
        strategies=strategies,
    )


def _reduce_distance(
    direct: Quantity | None, reverse: Quantity | None
) -> tuple[Quantity | None, float | None]:
    """Mean the two faces' distances, and report how far apart they were.

    One face carrying a distance and the other not is normal -- many operators
    measure the distance on the direct face only -- so that case takes the one
    that exists rather than refusing.
    """
    if direct is None and reverse is None:
        return None, None
    if direct is None:
        return reverse, None
    if reverse is None:
        return direct, None

    difference = direct.value - reverse.value
    mode, strategies = combine_modes(direct, reverse)
    return (
        Quantity(
            value=(direct.value + reverse.value) / 2.0,
            variance=(direct.variance + reverse.variance) / 4.0,
            unit=Unit.METRE,
            mode=mode,
            strategies=strategies,
        ),
        difference,
    )


def _distance_threshold(
    distance: Quantity | None, explicit: float | None, instrument: InstrumentProfile | None
) -> float:
    """How far apart the two faces may be before it is a blunder.

    Three times the EDM's own standard deviation when a profile is available:
    the two faces are independent measurements of one distance, so their
    difference has ``sqrt(2)`` times the single-reading sigma, and three of
    those is the usual blunder threshold. Rounded up to ``sqrt(2) * 3`` rather
    than derived exactly, because the point is to catch a metre, not to be a
    hypothesis test -- data snooping does that properly after the adjustment.
    """
    if explicit is not None:
        return explicit
    if instrument is not None and distance is not None:
        return 3.0 * math.sqrt(2.0) * instrument.distance_sigma(distance.value)
    return DEFAULT_DISTANCE_TOLERANCE


def _spread(values: list[float]) -> float:
    """Peak-to-peak, not a standard deviation.

    With two or three face pairs -- the routine case -- a sample standard
    deviation is a poor statistic and its meaning is not obvious to a reader.
    The largest disagreement is both.
    """
    return max(values) - min(values) if len(values) > 1 else 0.0
