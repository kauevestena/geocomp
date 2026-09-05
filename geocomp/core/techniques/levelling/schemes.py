# SPDX-License-Identifier: GPL-2.0-or-later
"""The three sight schemes (FR-500, FR-501, FR-502).

``specs/10-module-levelling.md`` section 2.

The proposal names three, and the distinction is not cosmetic: each has a
different geometry and therefore a different error model, and which systematic
errors cancel changes with it.

* **Equal sights.** Backsight and foresight distances equal. The preferred
  method, because equal sight lengths cancel the collimation error and the
  effects of curvature and refraction to first order. What GeoComp adds is the
  *accumulated* imbalance, which is the number that actually drives the residual
  error over a line -- per-setup imbalances of alternating sign cost nothing.
* **Equidistant sights.** Reciprocal observation from both banks of an obstacle,
  where an equal-sight setup is impossible. What does not cancel geometrically
  cancels by symmetry instead, and what is left is modelled **conservatively**,
  with the reason stated in the output.
* **Extreme sights.** Several foresights from one setup. They all subtract the
  same backsight reading, so they are **correlated**, and the correlation is not
  a nuisance: it is what makes the height difference between two of the
  foresighted points *better* determined than treating them independently would
  suggest.

That last point is worth stating plainly, because it runs against the usual
intuition that ignoring a correlation is conservative. Here it is not. Two
foresights from one setup differ by ``f_i - f_j``: the backsight cancels
exactly. Treating them as independent adds ``2 * sigma_b^2`` that is not there,
and the reported uncertainty of every derived difference between foresighted
points is too *large*. ``specs/10`` section 7 makes an executable test of it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from geocomp.core.errors import ValidationError
from geocomp.core.findings import Finding, Severity
from geocomp.core.instruments.level import LevelProfile
from geocomp.core.techniques.levelling.readings import LevelSetup, StaffReading
from geocomp.core.uncertainty import Covariance, Quantity, Strategy
from geocomp.core.units import Unit

__all__ = [
    "ReciprocalPair",
    "ReciprocalReduction",
    "SetupReduction",
    "reduce_reciprocal",
    "reduce_setup",
]


@dataclass(frozen=True)
class SetupReduction:
    """The height differences one instrument setup determined.

    Attributes:
        from_station: The backsighted station. Every difference runs from it.
        to_stations: The foresighted stations, in the setup's order.
        height_differences: One per foresight, in the same order.
        covariance: The **full** matrix over those differences, labelled by
            foresighted station. Diagonal only when there is a single foresight;
            otherwise the shared backsight puts ``sigma_b^2`` in every
            off-diagonal cell, which is the correlation FR-104 exists for.
        imbalances: Backsight minus foresight distance per foresight, metres, or
            an empty tuple when the distances were not recorded.
        collimation: The correction applied per foresight, for the report. Zero
            where the sights were balanced or the instrument applies its own.
    """

    setup_id: str
    from_station: str
    to_stations: tuple[str, ...]
    height_differences: tuple[Quantity, ...]
    covariance: Covariance
    imbalances: tuple[float, ...] = ()
    collimation: tuple[Quantity, ...] = ()
    findings: tuple[Finding, ...] = ()

    @property
    def is_clustered(self) -> bool:
        """Whether these differences must travel together (FR-104)."""
        return len(self.height_differences) > 1

    def height_difference(self, station: str) -> Quantity:
        """The difference from the backsighted station to *station*."""
        try:
            index = self.to_stations.index(station)
        except ValueError:
            raise ValidationError(
                "station_not_foresighted",
                setup=self.setup_id,
                station=station,
                expected=list(self.to_stations),
            ) from None
        return self.height_differences[index]

    def between_foresights(self, first: str, second: str) -> Quantity:
        """The height difference from one foresighted station to another.

        Computed **through the covariance**, so the shared backsight cancels as
        it does in reality. This is the quantity ``specs/10`` section 7 item 3
        is about: taking it from two independently-treated differences would
        report an uncertainty inflated by twice the backsight variance.
        """
        i, j = self.covariance.index(first), self.covariance.index(second)
        matrix = self.covariance.matrix
        variance = matrix[i, i] + matrix[j, j] - 2.0 * matrix[i, j]
        value = self.height_differences[j].value - self.height_differences[i].value
        return Quantity(
            value=value,
            variance=max(variance, 0.0),
            unit=Unit.METRE,
            mode=self.covariance.mode,
            strategies=self.covariance.strategies,
        )


def reduce_setup(
    setup: LevelSetup,
    level: LevelProfile | None = None,
    *,
    max_sight_length: float = 0.0,
    max_sight_imbalance: float = 0.0,
) -> SetupReduction:
    """Reduce one setup to height differences with their full covariance.

    Handles both the equal-sights case (FR-500) and the extreme-sights case
    (FR-502): they are the same arithmetic, and the only difference is how many
    foresights there are, which is a property of the data rather than a mode.

        dh_i = b - f_i - c * (d_b - d_fi)

    Args:
        setup: One instrument position.
        level: The instrument, for its collimation. ``None`` skips the
            collimation term entirely rather than assuming it is zero -- which
            is the same statement for a balanced setup and a different one for
            an imbalanced setup, so the findings say which was the case.
        max_sight_length: Longest permitted sight, metres. Zero disables.
        max_sight_imbalance: Largest permitted per-setup imbalance, metres. Zero
            disables.
    """
    backsight = setup.backsight
    foresights = list(setup.foresights)
    findings: list[Finding] = []

    inputs: dict[str, Quantity] = {"b": backsight.reading.detached()}
    for index, sight in enumerate(foresights):
        inputs[f"f{index}"] = sight.reading.detached()

    imbalances: list[float] = []
    if setup.has_distances:
        imbalances = [
            backsight.distance_value - sight.distance_value for sight in foresights
        ]

    # The collimation enters every foresight of this setup through one shared
    # column, exactly as the refraction coefficient does in leap-frog
    # trigonometric levelling: one instrument, one calibration, one error.
    collimation = _collimation(level)
    apply_collimation = collimation is not None and bool(imbalances)
    if apply_collimation:
        inputs["c"] = collimation.detached()  # type: ignore[union-attr]

    order = list(inputs)
    jacobian = np.zeros((len(foresights), len(order)))
    values: list[float] = []
    corrections: list[Quantity] = []

    for index, sight in enumerate(foresights):
        jacobian[index, order.index("b")] = 1.0
        jacobian[index, order.index(f"f{index}")] = -1.0
        value = backsight.reading.value - sight.reading.value

        if apply_collimation:
            imbalance = imbalances[index]
            jacobian[index, order.index("c")] = -imbalance
            correction = level.collimation_correction(imbalance)  # type: ignore[union-attr]
            value += correction.value
            corrections.append(correction)
        else:
            corrections.append(Quantity.exact(0.0, Unit.METRE))
        values.append(value)

    covariance = Covariance.from_quantities(inputs).transform(
        jacobian, [sight.station for sight in foresights], [Unit.METRE] * len(foresights)
    )
    differences = tuple(
        covariance.quantity(sight.station, values[index])
        for index, sight in enumerate(foresights)
    )

    findings.extend(
        _geometry_findings(
            setup,
            imbalances,
            max_sight_length=max_sight_length,
            max_sight_imbalance=max_sight_imbalance,
            collimation_applied=apply_collimation,
            level=level,
        )
    )

    return SetupReduction(
        setup_id=setup.id,
        from_station=backsight.station,
        to_stations=tuple(sight.station for sight in foresights),
        height_differences=differences,
        covariance=covariance,
        imbalances=tuple(imbalances),
        collimation=tuple(corrections),
        findings=tuple(findings),
    )


def _collimation(level: LevelProfile | None) -> Quantity | None:
    """The collimation to propagate, or ``None`` when there is nothing to apply."""
    if level is None or level.applies_collimation:
        return None
    if level.collimation.value == 0.0 and level.collimation.is_exact:
        # A profile that states an exact zero has been calibrated and found
        # true; carrying a column of zeros through the Jacobian would say the
        # same thing more slowly.
        return None
    return level.collimation


def _geometry_findings(
    setup: LevelSetup,
    imbalances: list[float],
    *,
    max_sight_length: float,
    max_sight_imbalance: float,
    collimation_applied: bool,
    level: LevelProfile | None,
) -> list[Finding]:
    findings: list[Finding] = []

    if not setup.has_distances:
        findings.append(
            Finding(
                code="level_setup_without_distances",
                severity=Severity.WARNING,
                message=(
                    f"setup {setup.id} recorded no sight distances, so its balance "
                    "cannot be checked and no collimation correction can be applied. "
                    "Record the distances, or read three wires and let them be derived"
                ),
                stations=(setup.backsight.station,),
            )
        )
        return findings

    if max_sight_length > 0.0:
        for sight in (setup.backsight, *setup.foresights):
            if sight.distance_value > max_sight_length:
                findings.append(
                    Finding(
                        code="level_sight_too_long",
                        severity=Severity.WARNING,
                        message=(
                            f"the sight to {sight.station} from setup {setup.id} is "
                            f"{sight.distance_value:.1f} m, beyond the "
                            f"{max_sight_length:.1f} m this class permits. Long sights "
                            "magnify both refraction and the residual collimation error"
                        ),
                        stations=(sight.station,),
                        value=sight.distance_value,
                        threshold=max_sight_length,
                    )
                )

    if max_sight_imbalance > 0.0:
        for index, imbalance in enumerate(imbalances):
            if abs(imbalance) > max_sight_imbalance:
                findings.append(
                    Finding(
                        code="level_setup_imbalanced",
                        severity=Severity.WARNING,
                        message=(
                            f"setup {setup.id} is out of balance by {imbalance:+.2f} m "
                            f"on the sight to {setup.foresights[index].station}, beyond "
                            f"the {max_sight_imbalance:.2f} m this class permits"
                        ),
                        stations=(setup.foresights[index].station,),
                        value=abs(imbalance),
                        threshold=max_sight_imbalance,
                    )
                )

    if not collimation_applied and any(abs(value) > 0.0 for value in imbalances):
        worst = max(imbalances, key=abs)
        if level is None:
            findings.append(
                Finding(
                    code="level_imbalance_without_instrument",
                    severity=Severity.INFO,
                    message=(
                        f"setup {setup.id} is out of balance by {worst:+.2f} m and no "
                        "level profile was supplied, so no collimation correction was "
                        "applied. Supply the two-peg test result to correct it, or "
                        "balance the sights so it does not matter"
                    ),
                    stations=(setup.backsight.station,),
                    value=abs(worst),
                )
            )

    return findings


@dataclass(frozen=True)
class ReciprocalPair:
    """One bank's half of an equidistant-sights crossing (FR-501).

    Attributes:
        near: The reading onto the staff on the instrument's own bank -- the
            short sight, over which refraction is negligible.
        far: The reading onto the staff across the obstacle -- the long sight,
            which carries essentially all of the error the method exists to
            remove.
    """

    setup_id: str
    near: StaffReading
    far: StaffReading

    def __post_init__(self) -> None:
        if self.near.station == self.far.station:
            raise ValidationError(
                "reciprocal_pair_same_station",
                setup=self.setup_id,
                station=self.near.station,
                expected="two distinct stations, one on each bank",
            )


@dataclass(frozen=True)
class ReciprocalReduction:
    """A height difference across an obstacle, from both banks (FR-501).

    Attributes:
        height_difference: From ``from_station`` to ``to_station``, the mean of
            the two determinations.
        discrepancy: The two determinations' difference, metres. Expected zero;
            a large one says the refraction changed between the two
            observations, which is precisely the failure the method assumes did
            not happen, so it is reported rather than averaged away.
        inflation: The factor the variance was multiplied by, and the reason.
    """

    from_station: str
    to_station: str
    height_difference: Quantity
    forward: Quantity
    reverse: Quantity
    discrepancy: float
    inflation: float
    findings: tuple[Finding, ...] = ()
    meta: dict[str, Any] = field(default_factory=dict)


def reduce_reciprocal(
    first: ReciprocalPair,
    second: ReciprocalPair,
    *,
    variance_inflation: float = 2.0,
    discrepancy_tolerance: float = 0.0,
) -> ReciprocalReduction:
    """Combine two reciprocal observations across an obstacle (FR-501).

    Each bank determines the same height difference::

        dh(1) = near_1 - far_1        (instrument on bank A: near = A, far = B)
        dh(2) = far_2  - near_2       (instrument on bank B: near = B, far = A)

    Both run from *A* to *B*. The systematic part of the long sight -- curvature
    and, far more importantly, refraction over water -- enters the two with
    opposite sign, so it cancels in the mean. That cancellation is the method,
    and it is why the scheme is used where an equal-sight setup is impossible.

    **The uncertainty is deliberately conservative, and says so.** Refraction
    across water varies rapidly and asymmetrically; the symmetry the method
    relies on holds only to the extent that the two observations saw the same
    air, and they cannot have, because they were not simultaneous. So the
    propagated variance is multiplied by ``variance_inflation`` and the result
    is tagged :attr:`~geocomp.core.uncertainty.Strategy.EMPIRICAL_SCALING`,
    which carries into every report: a number that looks like a rigorous
    propagation but is not would misrepresent the crossing (FR-203).

    Args:
        first: The pair observed from the bank the difference runs *from*.
        second: The pair observed from the other bank.
        variance_inflation: Multiplies the propagated variance. One means no
            inflation, which the findings then say plainly rather than leaving
            the reader to notice.
        discrepancy_tolerance: Above which the two determinations' disagreement
            is reported. Zero disables the check.
    """
    if variance_inflation < 1.0:
        raise ValidationError(
            "variance_inflation_below_one",
            received=variance_inflation,
            expected=(
                "a factor of at least one; deflating the variance of a reciprocal "
                "crossing would claim the method is better than its inputs"
            ),
        )

    from_station, to_station = first.near.station, first.far.station
    if {second.near.station, second.far.station} != {from_station, to_station}:
        raise ValidationError(
            "reciprocal_pairs_disagree",
            received=[second.near.station, second.far.station],
            expected=[from_station, to_station],
        )
    if second.near.station != to_station:
        raise ValidationError(
            "reciprocal_second_pair_reversed",
            received=second.near.station,
            expected=(
                f"{to_station}; the second pair is observed from the far bank, so its "
                "near reading is onto the station the difference runs to"
            ),
        )

    inputs = {
        "near1": first.near.reading.detached(),
        "far1": first.far.reading.detached(),
        "near2": second.near.reading.detached(),
        "far2": second.far.reading.detached(),
    }
    order = list(inputs)
    # dh = ((near1 - far1) + (far2 - near2)) / 2
    jacobian = np.zeros((1, 4))
    jacobian[0, order.index("near1")] = 0.5
    jacobian[0, order.index("far1")] = -0.5
    jacobian[0, order.index("far2")] = 0.5
    jacobian[0, order.index("near2")] = -0.5

    forward_value = first.near.reading.value - first.far.reading.value
    reverse_value = second.far.reading.value - second.near.reading.value
    propagated = Covariance.from_quantities(inputs).transform(
        jacobian, ["height_difference"], [Unit.METRE]
    )

    variance = float(propagated.matrix[0, 0]) * variance_inflation
    height_difference = Quantity.approximate(
        (forward_value + reverse_value) / 2.0,
        variance**0.5,
        Unit.METRE,
        Strategy.EMPIRICAL_SCALING,
        *propagated.strategies,
    )

    discrepancy = forward_value - reverse_value
    findings: list[Finding] = [
        Finding(
            code="reciprocal_variance_inflated",
            severity=Severity.INFO,
            message=(
                f"the variance of this crossing was multiplied by {variance_inflation:g}. "
                "Refraction over water varies rapidly and asymmetrically, and the two "
                "reciprocal observations were not simultaneous, so the symmetry the "
                "method relies on holds only approximately"
            ),
            stations=(from_station, to_station),
            value=variance_inflation,
        )
        if variance_inflation > 1.0
        else Finding(
            code="reciprocal_variance_not_inflated",
            severity=Severity.WARNING,
            message=(
                "this crossing was reduced with no variance inflation, so its "
                "uncertainty assumes the two reciprocal observations saw identical "
                "refraction. They were not simultaneous, so they did not"
            ),
            stations=(from_station, to_station),
            value=1.0,
        )
    ]

    if discrepancy_tolerance > 0.0 and abs(discrepancy) > discrepancy_tolerance:
        findings.append(
            Finding(
                code="reciprocal_determinations_disagree",
                severity=Severity.WARNING,
                message=(
                    f"the two banks give height differences differing by "
                    f"{discrepancy:+.4f} m. The method assumes the refraction was the "
                    "same for both, and a discrepancy this size says it was not"
                ),
                stations=(from_station, to_station),
                value=abs(discrepancy),
                threshold=discrepancy_tolerance,
            )
        )

    return ReciprocalReduction(
        from_station=from_station,
        to_station=to_station,
        height_difference=height_difference,
        forward=Quantity.from_std_dev(
            forward_value,
            (first.near.reading.variance + first.far.reading.variance) ** 0.5,
            Unit.METRE,
        ),
        reverse=Quantity.from_std_dev(
            reverse_value,
            (second.near.reading.variance + second.far.reading.variance) ** 0.5,
            Unit.METRE,
        ),
        discrepancy=discrepancy,
        inflation=variance_inflation,
        findings=tuple(findings),
    )
