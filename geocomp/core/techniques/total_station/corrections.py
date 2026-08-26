# SPDX-License-Identifier: GPL-2.0-or-later
"""Instrument and EDM corrections (FR-402, FR-403).

``specs/09-module-total-station.md`` sections 2.2 and 2.4.

Each correction parameter has its own uncertainty, and it propagates (FR-204).
A calibrated additive constant known to +/- 0.3 mm and one known to +/- 3 mm
give the same corrected distance and different -- correctly different -- error
ellipses downstream.

**The applied-once rule governs this whole module.** An instrument configured
with its prism constant applies it internally; applying it again here is a
silent error of twice the constant, typically 60 mm, which no statistic
downstream can distinguish from a real displacement. Every correction therefore
checks what the instrument already did, and reports what it decided.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geocomp.core.findings import Finding, Severity
from geocomp.core.instruments.profiles import InstrumentProfile, ReflectorProfile
from geocomp.core.techniques.total_station.face import FaceReduction
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit, wrap_to_2pi

__all__ = [
    "EdmCorrection",
    "apply_edm_corrections",
    "apply_instrument_corrections",
]


@dataclass(frozen=True)
class EdmCorrection:
    """A slope distance with the EDM's own corrections applied.

    Attributes:
        distance: The corrected slope distance.
        additive: The total additive constant applied, instrument plus
            reflector. Zero when the instrument applied it itself.
        scale: The multiplicative scale factor applied.
        cyclic: The cyclic-error correction applied.
        additive_skipped: True when the instrument had already applied the
            additive constant. Recorded rather than inferred, because "the
            correction is zero" and "the correction was already done" are
            different facts and a report must not conflate them.
    """

    distance: Quantity
    additive: Quantity
    scale: Quantity
    cyclic: Quantity
    additive_skipped: bool = False
    findings: tuple[Finding, ...] = ()


def apply_instrument_corrections(
    reduction: FaceReduction, instrument: InstrumentProfile
) -> FaceReduction:
    """Apply the corrections a face pair did not already cancel (FR-402).

    For a pair, that is only the horizontal-axis (trunnion) tilt: collimation
    and vertical index error are cancelled by the pairing itself, and applying
    the stored constants on top would double-count them.

    For a single-face pointing, :func:`~geocomp.core.techniques.total_station.face.reduce_single_face`
    has already applied collimation and index error, so this again adds only the
    trunnion term.

    The trunnion tilt's effect on a horizontal direction depends on the zenith
    angle: it vanishes on a horizontal sight and grows as the line of sight
    steepens, as ``t / tan(z)``.
    """
    tilt = instrument.trunnion_tilt
    if tilt.value == 0.0 and tilt.variance == 0.0:
        return reduction

    zenith = reduction.zenith.value
    findings = list(reduction.findings)

    # cot(z) is unbounded at the zenith and nadir. A sight within a degree of
    # vertical is not a direction measurement at all -- the horizontal circle
    # reading is meaningless there -- so this reports rather than returning a
    # number that grows without bound.
    if abs(math.sin(zenith)) < math.sin(math.radians(1.0)):
        findings.append(
            Finding(
                code="near_vertical_sight",
                severity=Severity.WARNING,
                message=(
                    f"the sight to {reduction.target} is within one degree of vertical, where "
                    "the horizontal circle reading carries almost no directional information "
                    "and the trunnion-tilt correction is unbounded. It was not applied"
                ),
                observations=(reduction.target,),
                value=abs(math.degrees(zenith - math.pi / 2.0)),
            )
        )
        return _replace_findings(reduction, tuple(findings))

    cotangent = math.cos(zenith) / math.sin(zenith)
    correction = tilt * cotangent
    corrected = reduction.horizontal + correction

    return FaceReduction(
        target=reduction.target,
        horizontal=Quantity(
            value=wrap_to_2pi(corrected.value),
            variance=corrected.variance,
            unit=Unit.RADIAN,
            mode=corrected.mode,
            strategies=corrected.strategies,
        ),
        zenith=reduction.zenith,
        distance=reduction.distance,
        collimation=reduction.collimation,
        vertical_index=reduction.vertical_index,
        distance_difference=reduction.distance_difference,
        set_number=reduction.set_number,
        findings=tuple(findings),
        single_face=reduction.single_face,
    )


def apply_edm_corrections(
    distance: Quantity,
    instrument: InstrumentProfile,
    reflector: ReflectorProfile | None = None,
) -> EdmCorrection:
    """Apply the additive constant, scale factor and cyclic error (FR-403).

    The order is the physical one: the additive constant is a fixed offset in
    the instrument's optical path, the scale factor multiplies the measured
    length, and the cyclic error is periodic in the distance itself.

        d = (d_measured + a) * s + c(d_measured)

    Args:
        reflector: ``None`` for a reflectorless measurement, which genuinely has
            no prism constant -- distinct from a prism whose constant is zero.
    """
    findings: list[Finding] = []

    additive, skipped = _additive_constant(instrument, reflector, findings)
    corrected = (distance + additive) * instrument.edm_scale

    cyclic = _cyclic_error(distance, instrument)
    if cyclic.value != 0.0 or cyclic.variance != 0.0:
        corrected = corrected + cyclic

    return EdmCorrection(
        distance=corrected,
        additive=additive,
        scale=instrument.edm_scale,
        cyclic=cyclic,
        additive_skipped=skipped,
        findings=tuple(findings),
    )


def _additive_constant(
    instrument: InstrumentProfile,
    reflector: ReflectorProfile | None,
    findings: list[Finding],
) -> tuple[Quantity, bool]:
    """The total additive constant, honouring the applied-once rule.

    The instrument and the reflector each declare whether their part is applied
    internally, and the two are independent: an instrument can be configured
    with the prism constant while the prism profile records the same value for
    documentation.
    """
    parts: list[Quantity] = []
    skipped = False

    if instrument.applies_edm_constant:
        skipped = True
        findings.append(
            Finding(
                code="edm_constant_applied_by_instrument",
                severity=Severity.INFO,
                message=(
                    f"instrument {instrument.label} applies its additive constant internally, "
                    "so GeoComp did not apply it again"
                ),
            )
        )
    else:
        parts.append(instrument.edm_additive)

    if reflector is not None:
        if reflector.applies_internally:
            skipped = True
            findings.append(
                Finding(
                    code="prism_constant_applied_by_instrument",
                    severity=Severity.INFO,
                    message=(
                        f"the constant of reflector {reflector.label} is applied by the "
                        "instrument, so GeoComp did not apply it again"
                    ),
                )
            )
        else:
            parts.append(reflector.additive_constant)

    if not parts:
        return Quantity.exact(0.0, Unit.METRE), skipped

    total = parts[0]
    for part in parts[1:]:
        total = total + part
    return total, skipped


def _cyclic_error(distance: Quantity, instrument: InstrumentProfile) -> Quantity:
    """The EDM's short-periodic error at this distance.

        c(d) = -A * sin(2 pi d / lambda + phi)

    Negative because the correction removes the error. The amplitude's own
    uncertainty propagates; the distance's does not, because the derivative
    with respect to *d* is ``-2 pi A / lambda * cos(...)``, which for a
    sub-millimetre amplitude and a metre-scale wavelength is a contribution of
    order microns per millimetre of distance error -- far below the amplitude
    term it would be added to.
    """
    amplitude = instrument.cyclic_error_amplitude
    if amplitude.value == 0.0 and amplitude.variance == 0.0:
        return Quantity.exact(0.0, Unit.METRE)

    phase = 2.0 * math.pi * distance.value / instrument.cyclic_error_wavelength
    factor = -math.sin(phase)
    return Quantity(
        value=amplitude.value * factor,
        variance=amplitude.variance * factor**2,
        unit=Unit.METRE,
        mode=amplitude.mode,
        strategies=amplitude.strategies,
    )


def _replace_findings(reduction: FaceReduction, findings: tuple[Finding, ...]) -> FaceReduction:
    return FaceReduction(
        target=reduction.target,
        horizontal=reduction.horizontal,
        zenith=reduction.zenith,
        distance=reduction.distance,
        collimation=reduction.collimation,
        vertical_index=reduction.vertical_index,
        distance_difference=reduction.distance_difference,
        set_number=reduction.set_number,
        findings=findings,
        single_face=reduction.single_face,
    )
