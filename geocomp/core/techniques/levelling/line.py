# SPDX-License-Identifier: GPL-2.0-or-later
"""Levelling lines: a run of setups reduced as one thing (FR-500, FR-503).

``specs/10-module-levelling.md`` sections 2.1 and 3.

A line is reduced **as a whole**, not as a sum of independently reduced setups,
and the reason is the collimation.

One instrument levels the whole line, so there is one collimation error *c*, not
one per setup. Its contribution to the line's height difference is::

    -c * sum_i (d_bi - d_fi) = -c * (accumulated imbalance)

Carry *c* through a single shared column and two things follow that a per-setup
treatment gets wrong. The **value** is corrected by the accumulated imbalance,
so per-setup imbalances of opposite sign cancel each other as they physically
do. And the **uncertainty** contribution is
``(accumulated imbalance)^2 * var(c)``, which goes to *zero* for a balanced line
-- whatever *c* is, and whatever its uncertainty. That is the mathematical
statement of why equal sights is the preferred method: on a balanced line the
collimation need not even be known.

Summing independently reduced setups would instead give
``sum_i (imbalance_i)^2 * var(c)``, which is never zero unless every single
setup was perfectly balanced. It is the same mistake, in the same shape, as
treating the two sights of a leap-frog pair as having independent refraction
coefficients (:mod:`geocomp.core.techniques.total_station.levelling`); there it
inflates the uncertainty, here it does too.

**Which foresight continues the line.** A setup may carry several foresights
(extreme sights, FR-502). The **first** continues the line; the rest are side
shots, levelled from the same position and returned separately with their
correlation intact. The convention is enforced rather than assumed: the next
setup's backsight must stand on the previous setup's first foresight, and a
field book entered out of order is refused by name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from geocomp.core.errors import ValidationError
from geocomp.core.findings import Finding, Severity
from geocomp.core.instruments.level import LevelProfile
from geocomp.core.techniques.levelling.readings import LevelSetup
from geocomp.core.techniques.levelling.schemes import SetupReduction, reduce_setup
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

__all__ = [
    "LevellingLine",
    "LineReduction",
    "SideShot",
    "reduce_line",
    "reverse_height_difference",
]


@dataclass(frozen=True)
class LevellingLine:
    """An ordered run of setups from one station to another.

    Attributes:
        setups: In observation order. Each setup's backsight stands on the
            previous setup's first foresight.
        level_id: The instrument that ran the line. One line, one instrument --
            which is exactly the assumption that lets the collimation be a
            single shared unknown. Changing instruments mid-line makes two
            lines, and GeoComp will not pretend otherwise.
        levelling_class_id: The specification the line is judged against
            (FR-503), or ``None`` when none was stated.
    """

    id: str
    setups: tuple[LevelSetup, ...]
    level_id: str | None = None
    levelling_class_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError(
                "levelling_line_without_id",
                expected="an id; closures and findings reference a line by it",
            )
        if not self.setups:
            raise ValidationError(
                "levelling_line_without_setups",
                line=self.id,
                expected="at least one setup",
            )
        for previous, following in zip(self.setups, self.setups[1:], strict=False):
            expected = previous.foresights[0].station
            if following.backsight.station != expected:
                raise ValidationError(
                    "levelling_line_discontinuous",
                    line=self.id,
                    setup=following.id,
                    received=following.backsight.station,
                    expected=(
                        f"{expected}, the first foresight of setup {previous.id}; the "
                        "line advances through the first foresight and the rest are "
                        "side shots"
                    ),
                )

    @property
    def from_station(self) -> str:
        return self.setups[0].backsight.station

    @property
    def to_station(self) -> str:
        return self.setups[-1].foresights[0].station

    @property
    def setup_count(self) -> int:
        return len(self.setups)

    @property
    def has_distances(self) -> bool:
        return all(setup.has_distances for setup in self.setups)

    @property
    def length_km(self) -> float | None:
        """The levelled distance in kilometres, or ``None`` when unmeasured.

        ``None`` rather than zero, and it propagates: length weighting and the
        ``k * sqrt(L)`` tolerance both refuse rather than treat an unmeasured
        line as one of zero length, which would make every tolerance zero and
        every weight infinite.
        """
        if not self.has_distances:
            return None
        return sum(setup.sight_length for setup in self.setups) / 1000.0

    @property
    def stations(self) -> tuple[str, ...]:
        """Every station the line touches, side shots included, in order."""
        seen: list[str] = [self.from_station]
        for setup in self.setups:
            for sight in setup.foresights:
                if sight.station not in seen:
                    seen.append(sight.station)
        return tuple(seen)


@dataclass(frozen=True)
class SideShot:
    """A point levelled from a line's setup without the line passing through it.

    Carries the setup it came from, because its height difference is correlated
    with the line's step at that setup -- they share the backsight -- and a
    later network assembly needs that to build the cluster (FR-104).
    """

    setup_id: str
    from_station: str
    to_station: str
    height_difference: Quantity
    reduction: SetupReduction


@dataclass(frozen=True)
class LineReduction:
    """One levelling line reduced to a single height difference.

    Attributes:
        height_difference: From ``from_station`` to ``to_station``, with the
            collimation carried once over the whole line.
        accumulated_imbalance: Sum of the per-setup backsight-minus-foresight
            distances, metres, or ``None`` when the distances were not
            recorded. **The number the balance check is about**: it, not the
            per-setup imbalance, is what multiplies the collimation.
        collimation: The total correction applied, for the report.
        raw_height_difference: Before the collimation correction, so a report
            can show what the correction changed.
    """

    line_id: str
    from_station: str
    to_station: str
    height_difference: Quantity
    raw_height_difference: Quantity
    setups: tuple[SetupReduction, ...]
    side_shots: tuple[SideShot, ...] = ()
    length_km: float | None = None
    setup_count: int = 0
    accumulated_imbalance: float | None = None
    collimation: Quantity | None = None
    findings: tuple[Finding, ...] = ()

    @property
    def is_balanced(self) -> bool:
        """Whether the accumulated imbalance is exactly zero.

        The condition under which the collimation contributes neither a
        correction nor an uncertainty, which is worth being able to assert.
        """
        return self.accumulated_imbalance == 0.0


def reduce_line(
    line: LevellingLine,
    level: LevelProfile | None = None,
    *,
    max_sight_length: float = 0.0,
    max_sight_imbalance: float = 0.0,
    max_accumulated_imbalance: float = 0.0,
) -> LineReduction:
    """Reduce a whole line to one height difference (FR-500, FR-502).

    Args:
        line: The setups, in observation order.
        level: The instrument, for its collimation. ``None`` skips the term.
        max_sight_length: Per-sight limit, metres. Zero disables.
        max_sight_imbalance: Per-setup limit, metres. Zero disables.
        max_accumulated_imbalance: Per-line limit, metres. Zero disables. This
            is the limit that matters; see the module docstring.
    """
    reductions = tuple(
        reduce_setup(
            setup,
            level,
            max_sight_length=max_sight_length,
            max_sight_imbalance=max_sight_imbalance,
        )
        for setup in line.setups
    )
    findings: list[Finding] = [
        finding for reduction in reductions for finding in reduction.findings
    ]

    # One shared column for the collimation, and one per staff reading. The
    # readings of different setups are independent; the collimation is not.
    inputs: dict[str, Quantity] = {}
    for index, setup in enumerate(line.setups):
        inputs[f"b{index}"] = setup.backsight.reading.detached()
        inputs[f"f{index}"] = setup.foresights[0].reading.detached()

    imbalances: list[float] | None = None
    if line.has_distances:
        imbalances = [setup.imbalance(0) or 0.0 for setup in line.setups]
    accumulated = sum(imbalances) if imbalances is not None else None

    collimation = None
    if level is not None and not level.applies_collimation and accumulated is not None:
        if not (level.collimation.value == 0.0 and level.collimation.is_exact):
            collimation = level.collimation
            inputs["c"] = collimation.detached()

    order = list(inputs)
    jacobian = np.zeros((1, len(order)))
    raw = 0.0
    for index, setup in enumerate(line.setups):
        jacobian[0, order.index(f"b{index}")] = 1.0
        jacobian[0, order.index(f"f{index}")] = -1.0
        raw += setup.backsight.reading.value - setup.foresights[0].reading.value

    correction = Quantity.exact(0.0, Unit.METRE)
    if collimation is not None:
        jacobian[0, order.index("c")] = -float(accumulated)
        correction = level.collimation_correction(float(accumulated))  # type: ignore[union-attr]

    propagated = Covariance.from_quantities(inputs).transform(
        jacobian, ["height_difference"], [Unit.METRE]
    )
    height_difference = propagated.quantity("height_difference", raw + correction.value)
    raw_difference = Quantity(
        value=raw,
        variance=sum(
            setup.backsight.reading.variance + setup.foresights[0].reading.variance
            for setup in line.setups
        ),
        unit=Unit.METRE,
        mode=height_difference.mode,
        strategies=height_difference.strategies,
    )

    side_shots = tuple(
        SideShot(
            setup_id=setup.id,
            from_station=setup.backsight.station,
            to_station=sight.station,
            height_difference=reductions[index].height_difference(sight.station),
            reduction=reductions[index],
        )
        for index, setup in enumerate(line.setups)
        for sight in setup.foresights[1:]
    )

    if accumulated is None:
        findings.append(
            Finding(
                code="levelling_line_length_unknown",
                severity=Severity.WARNING,
                message=(
                    f"line {line.id} recorded no sight distances, so its length is "
                    "unknown. Length weighting and the k*sqrt(L) tolerance both need "
                    "it and will refuse rather than assume a length of zero"
                ),
                stations=(line.from_station, line.to_station),
            )
        )
    elif max_accumulated_imbalance > 0.0 and abs(accumulated) > max_accumulated_imbalance:
        findings.append(
            Finding(
                code="levelling_line_accumulated_imbalance",
                severity=Severity.WARNING,
                message=(
                    f"line {line.id} accumulated {accumulated:+.2f} m of sight imbalance, "
                    f"beyond the {max_accumulated_imbalance:.2f} m this class permits. "
                    "It is the accumulated figure, not the per-setup one, that "
                    "multiplies the collimation error over a line"
                ),
                stations=(line.from_station, line.to_station),
                value=abs(accumulated),
                threshold=max_accumulated_imbalance,
            )
        )
    elif accumulated == 0.0 and collimation is not None:
        findings.append(
            Finding(
                code="levelling_line_balanced",
                severity=Severity.INFO,
                message=(
                    f"line {line.id} is exactly balanced, so the collimation error "
                    "contributes neither a correction nor an uncertainty, whatever its "
                    "value. This is what makes equal sights the preferred method"
                ),
                stations=(line.from_station, line.to_station),
                value=0.0,
            )
        )

    return LineReduction(
        line_id=line.id,
        from_station=line.from_station,
        to_station=line.to_station,
        height_difference=height_difference,
        raw_height_difference=raw_difference,
        setups=reductions,
        side_shots=side_shots,
        length_km=line.length_km,
        setup_count=line.setup_count,
        accumulated_imbalance=accumulated,
        collimation=correction if collimation is not None else None,
        findings=tuple(findings),
    )


def reverse_height_difference(reduction: LineReduction) -> Quantity:
    """The line's height difference read the other way.

    A levelling line run forward and back gives two determinations of one
    difference, and the second is the negative of the first. Provided rather
    than left to the caller because negating a Quantity by hand is exactly where
    a sign error hides.
    """
    return -reduction.height_difference
