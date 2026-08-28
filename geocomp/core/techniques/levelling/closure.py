# SPDX-License-Identifier: GPL-2.0-or-later
"""Line and loop closures against a tolerance (FR-503).

``specs/10-module-levelling.md`` section 3: *a levelling result without a
closure check is not a result*.

Three things are computed, and the third is where most of the thought went.

1. **The misclosure** -- the observed height difference minus the known one for
   a line, or the sum around a loop, which should be zero.
2. **The comparison** against the permissible misclosure ``k * sqrt(L)``. With
   no *k* configured the misclosure is still reported, with **no verdict**:
   ``specs/10`` section 3 requires the numbers, and inventing a tolerance to
   have something to compare against would be worse than saying nothing.
3. **The distribution across setups**, and an honest statement of what it is.

On that third point. Distributing a misclosure proportionally is the classical
correction, and many specifications still require it, so GeoComp computes it.
But it must be said plainly that **proportional distribution localises nothing**:
every setup receives its share whether or not it is where the error entered, so
a blunder is smeared evenly along the line and made harder to find rather than
easier. What *does* localise an error is the network adjustment with data
snooping, which phase P2 already built.

So the distribution comes with a test that decides which of the two situations
the user is in. The misclosure has a propagated standard deviation, from the
readings themselves; the ratio

    w = misclosure / sigma(misclosure)

is a standardised residual. A line whose |w| is small closed as well as its own
observations say it should, and distributing that misclosure is exactly right. A
line whose |w| is large did **not**: something happened that the reading
precisions do not explain, and spreading it evenly is the one response
guaranteed to hide it. GeoComp says which, by name.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.findings import Finding, Severity
from geocomp.core.instruments.level import LevellingClass
from geocomp.core.techniques.levelling.line import LineReduction
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = [
    "ClosureCheck",
    "SetupShare",
    "line_closure",
    "loop_closure",
]

#: |w| beyond which a misclosure is called inconsistent with the observations'
#: own precision. Two-sided normal, alpha = 0.001 -- the same significance the
#: data-snooping default uses (``stochastic.outlier_alpha``), because it is the
#: same question asked of one aggregate residual instead of many single ones.
BLUNDER_THRESHOLD = 3.29


@dataclass(frozen=True)
class SetupShare:
    """One setup's share of a distributed misclosure.

    Attributes:
        correction: The share, metres, to **add** to that setup's height
            difference. Signed opposite to the misclosure, as a correction is.
        weight: The share of the total this setup carried -- its length or its
            count of one, normalised.
        standardised: ``|correction| / sigma`` of that setup's own height
            difference. Not a localisation, and named so it cannot be mistaken
            for one: it says how large the assigned share is compared with what
            that setup could plausibly have contributed, which is a hint about
            where to look and nothing stronger.
    """

    setup_id: str
    correction: float
    weight: float
    standardised: float | None = None


@dataclass(frozen=True)
class ClosureCheck:
    """A misclosure, its tolerance comparison and its distribution (FR-503).

    Attributes:
        misclosure: Observed minus known, metres. Zero is the expected value.
        permissible: ``k * sqrt(L)``, or ``None`` when no tolerance was
            configured or the length is unknown.
        passed: ``True``, ``False``, or ``None`` for "no tolerance to judge
            against". Three states rather than two, deliberately: a check that
            reports ``True`` when it could not test anything is worse than one
            that admits it.
        standardised: The misclosure over its own propagated sigma, or ``None``
            when the observations carried no uncertainty to propagate.
        distribution: The classical proportional correction, per setup.
    """

    kind: str
    id: str
    misclosure: float
    uncertainty: Quantity | None = None
    permissible: float | None = None
    passed: bool | None = None
    standardised: float | None = None
    length_km: float | None = None
    setup_count: int = 0
    levelling_class: str = ""
    distribution: tuple[SetupShare, ...] = ()
    findings: tuple[Finding, ...] = ()
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def was_judged(self) -> bool:
        """Whether there was a tolerance to compare against at all."""
        return self.passed is not None

    @property
    def looks_like_a_blunder(self) -> bool:
        """Whether the misclosure exceeds what the readings' own precision explains.

        The question that decides whether distributing the misclosure is the
        right response or the worst available one.
        """
        return self.standardised is not None and abs(self.standardised) > BLUNDER_THRESHOLD


def line_closure(
    reduction: LineReduction,
    known_difference: Quantity,
    *,
    levelling_class: LevellingClass | None = None,
    weighting: str = "length",
) -> ClosureCheck:
    """Close a line against a known height difference (FR-503).

    Args:
        reduction: The line as reduced by
            :func:`~geocomp.core.techniques.levelling.line.reduce_line`.
        known_difference: The height difference the line *should* have measured,
            from the two benchmarks' published heights. Carries its own
            uncertainty, which enters the misclosure's -- a line closed against
            two third-order benchmarks has not been tested as sharply as one
            closed against two first-order ones, and pretending otherwise
            overstates the test.
        levelling_class: The specification, or ``None`` for no verdict.
        weighting: ``"length"`` or ``"setups"``; how the misclosure is
            distributed.
    """
    if known_difference.unit is not Unit.METRE:
        raise ValidationError(
            "known_difference_wrong_unit",
            received=known_difference.unit.name,
            expected=Unit.METRE.name,
        )

    misclosure = reduction.height_difference.value - known_difference.value
    sigma = math.sqrt(reduction.height_difference.variance + known_difference.variance)
    uncertainty = Quantity(
        value=misclosure,
        variance=reduction.height_difference.variance + known_difference.variance,
        unit=Unit.METRE,
        mode=reduction.height_difference.mode,
        strategies=reduction.height_difference.strategies | known_difference.strategies,
    )

    return _assemble(
        kind="line",
        identifier=reduction.line_id,
        misclosure=misclosure,
        sigma=sigma,
        uncertainty=uncertainty,
        reductions=[reduction],
        levelling_class=levelling_class,
        weighting=weighting,
    )


def loop_closure(
    reductions: list[LineReduction],
    *,
    loop_id: str = "loop",
    levelling_class: LevellingClass | None = None,
    weighting: str = "length",
) -> ClosureCheck:
    """Close a loop of lines on itself (FR-503).

    The lines must chain end to start and return to where they began. A line
    traversed against its direction contributes its **negated** height
    difference, and GeoComp works out which from the station ids rather than
    asking the user to enter the signs -- entering a sign by hand is where a
    loop closure goes wrong, and it goes wrong by exactly twice the height
    difference, which looks like a blunder somewhere else entirely.
    """
    if not reductions:
        raise ValidationError(
            "loop_without_lines", loop=loop_id, expected="at least one line"
        )

    start = reductions[0].from_station
    at = start
    total = 0.0
    variance = 0.0
    strategies: frozenset = frozenset()
    mode = reductions[0].height_difference.mode

    for reduction in reductions:
        if reduction.from_station == at:
            total += reduction.height_difference.value
            at = reduction.to_station
        elif reduction.to_station == at:
            total -= reduction.height_difference.value
            at = reduction.from_station
        else:
            raise ValidationError(
                "loop_discontinuous",
                loop=loop_id,
                line=reduction.line_id,
                received=[reduction.from_station, reduction.to_station],
                expected=f"a line starting or ending at {at}",
            )
        variance += reduction.height_difference.variance
        strategies |= reduction.height_difference.strategies
        if reduction.height_difference.mode.value == "approximate":
            mode = reduction.height_difference.mode

    if at != start:
        raise ValidationError(
            "loop_does_not_close",
            loop=loop_id,
            received=at,
            expected=f"{start}; a loop must return to the station it began at",
        )

    uncertainty = Quantity(
        value=total, variance=variance, unit=Unit.METRE, mode=mode, strategies=strategies
    )

    return _assemble(
        kind="loop",
        identifier=loop_id,
        misclosure=total,
        sigma=math.sqrt(variance),
        uncertainty=uncertainty,
        reductions=reductions,
        levelling_class=levelling_class,
        weighting=weighting,
    )


def _assemble(
    *,
    kind: str,
    identifier: str,
    misclosure: float,
    sigma: float,
    uncertainty: Quantity,
    reductions: list[LineReduction],
    levelling_class: LevellingClass | None,
    weighting: str,
) -> ClosureCheck:
    lengths = [reduction.length_km for reduction in reductions]
    length_km = None if any(value is None for value in lengths) else math.fsum(
        float(value) for value in lengths
    )
    setup_count = sum(reduction.setup_count for reduction in reductions)

    permissible: float | None = None
    passed: bool | None = None
    if levelling_class is not None and levelling_class.has_tolerance and length_km is not None:
        permissible = levelling_class.permissible_misclosure(length_km)
        passed = abs(misclosure) <= float(permissible)

    standardised = misclosure / sigma if sigma > 0.0 else None
    distribution = _distribute(misclosure, reductions, weighting)
    findings = _closure_findings(
        kind=kind,
        identifier=identifier,
        misclosure=misclosure,
        permissible=permissible,
        passed=passed,
        standardised=standardised,
        length_km=length_km,
        levelling_class=levelling_class,
    )

    return ClosureCheck(
        kind=kind,
        id=identifier,
        misclosure=misclosure,
        uncertainty=uncertainty,
        permissible=permissible,
        passed=passed,
        standardised=standardised,
        length_km=length_km,
        setup_count=setup_count,
        levelling_class=levelling_class.id if levelling_class else "",
        distribution=distribution,
        findings=findings,
    )


def _distribute(
    misclosure: float, reductions: list[LineReduction], weighting: str
) -> tuple[SetupShare, ...]:
    """The classical proportional correction, per setup.

    By sight length where the distances are known and length weighting was
    asked for, otherwise by setup count. Falling back rather than refusing: a
    correction distributed by count is a real answer that many specifications
    accept, whereas refusing to distribute at all because the distances are
    missing helps nobody.
    """
    setups = [
        (setup, reduction)
        for reduction in reductions
        for setup in reduction.setups
    ]
    if not setups:
        return ()

    weights: list[float]
    by_length = weighting == "length" and all(
        reduction.length_km is not None for reduction in reductions
    )
    if by_length:
        weights = [
            _setup_length(setup_reduction, reduction) for setup_reduction, reduction in setups
        ]
        if math.fsum(weights) <= 0.0:
            by_length = False
    if not by_length:
        weights = [1.0] * len(setups)

    total = math.fsum(weights)
    shares: list[SetupShare] = []
    for (setup_reduction, _), weight in zip(setups, weights, strict=True):
        fraction = weight / total
        correction = -misclosure * fraction
        sigma = _setup_sigma(setup_reduction)
        shares.append(
            SetupShare(
                setup_id=setup_reduction.setup_id,
                correction=correction,
                weight=fraction,
                standardised=abs(correction) / sigma if sigma and sigma > 0.0 else None,
            )
        )
    return tuple(shares)


def _setup_length(setup_reduction, reduction: LineReduction) -> float:
    """A setup's share of its line's length, in kilometres.

    Taken from the line rather than the setup, and divided evenly, because a
    :class:`~geocomp.core.techniques.levelling.schemes.SetupReduction` keeps the
    height differences and not the distances they came from. Even division is
    right for a line of consistent sight lengths, which is the case length
    weighting is for in the first place.
    """
    if reduction.length_km is None or not reduction.setups:
        return 0.0
    return float(reduction.length_km) / len(reduction.setups)


def _setup_sigma(setup_reduction) -> float | None:
    """The standard deviation of a setup's first (line-continuing) difference."""
    if not setup_reduction.height_differences:
        return None
    return setup_reduction.height_differences[0].std_dev


def _closure_findings(
    *,
    kind: str,
    identifier: str,
    misclosure: float,
    permissible: float | None,
    passed: bool | None,
    standardised: float | None,
    length_km: float | None,
    levelling_class: LevellingClass | None,
) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    millimetres = misclosure * 1000.0

    if passed is False:
        findings.append(
            Finding(
                code="closure_out_of_tolerance",
                severity=Severity.BLOCKING,
                message=(
                    f"{kind} {identifier} misclosed by {millimetres:+.1f} mm over "
                    f"{length_km:.3f} km, beyond the {float(permissible) * 1000.0:.1f} mm "
                    f"permitted by class {levelling_class.label if levelling_class else ''}. "
                    "GeoComp will not adjust a line that failed its tolerance without an "
                    "explicit acknowledgement"
                ),
                value=abs(misclosure),
                threshold=permissible,
            )
        )
    elif passed is None:
        reason = (
            "no levelling class was given"
            if levelling_class is None
            else (
                "the class states no tolerance coefficient"
                if not levelling_class.has_tolerance
                else "the line recorded no sight distances, so its length is unknown"
            )
        )
        findings.append(
            Finding(
                code="closure_not_judged",
                severity=Severity.WARNING,
                message=(
                    f"{kind} {identifier} misclosed by {millimetres:+.1f} mm, which has "
                    f"not been judged against a tolerance because {reason}. The "
                    "misclosure is reported; whether it is acceptable is not"
                ),
                value=abs(misclosure),
            )
        )

    if standardised is not None and abs(standardised) > BLUNDER_THRESHOLD:
        findings.append(
            Finding(
                code="closure_exceeds_its_own_precision",
                severity=Severity.WARNING,
                message=(
                    f"{kind} {identifier} misclosed by {millimetres:+.1f} mm, which is "
                    f"{abs(standardised):.1f} times its own propagated standard "
                    "deviation. That is not accumulated random error, so distributing "
                    "it proportionally would spread one mistake evenly along the line "
                    "and make it harder to find. Adjust the network and let data "
                    "snooping locate it instead"
                ),
                value=abs(standardised),
                threshold=BLUNDER_THRESHOLD,
            )
        )
    elif standardised is not None:
        findings.append(
            Finding(
                code="closure_consistent_with_its_precision",
                severity=Severity.INFO,
                message=(
                    f"{kind} {identifier} misclosed by {millimetres:+.1f} mm, "
                    f"{abs(standardised):.1f} times its own propagated standard "
                    "deviation. Consistent with accumulated random error, which is the "
                    "case proportional distribution is correct for"
                ),
                value=abs(standardised),
                threshold=BLUNDER_THRESHOLD,
            )
        )

    return tuple(findings)
