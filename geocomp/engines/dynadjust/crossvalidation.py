# SPDX-License-Identifier: GPL-2.0-or-later
"""Comparing an in-house solution with DynAdjust's (specs/07 section 6).

This is what phase P6 exists to make possible. Both engines fill the same
:class:`~geocomp.core.models.solution.Solution`, so the comparison is between
two answers to one question rather than between two file formats -- and a
disagreement is a real finding about one of the two implementations.

**What is compared, and what is not.** Degrees of freedom, observation and
parameter counts, the variance factor and the residuals are properties of the
observations, the weights and the model. They are the same numbers whatever
frame the coordinates are held in, so they are compared directly and a
difference in any of them means the two engines solved different problems.

Coordinates are only comparable when both solutions are in the same frame, and
that is **checked, not assumed**: comparing a geocentric X against a projected
easting produces a number, and the number is meaningless. When the frames differ
the coordinate comparison is reported as not attempted, with the two frames
named, rather than silently skipped or silently wrong.

**Tolerances are arguments, not constants.** How closely two least-squares
implementations should agree depends on the network -- an ill-conditioned one
amplifies the difference between two orderings of the same arithmetic -- so the
caller says what it expects and the report says what it found.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from geocomp.core.models.position import CoordinateSystem
from geocomp.core.models.solution import Solution

__all__ = ["Agreement", "Comparison", "compare"]

#: Default agreement expected of two independent implementations, in metres.
#: A tenth of a millimetre: far below any observation's precision, far above
#: the last-digit differences two orderings of the same arithmetic produce.
COORDINATE_TOLERANCE = 1e-4

#: Default relative agreement expected of the variance factor. DynAdjust prints
#: sigma-zero to three decimals, so two runs that agree exactly still differ by
#: up to half a unit in the third place; 1e-2 relative accommodates that without
#: accommodating a genuinely different weight matrix.
VARIANCE_TOLERANCE = 1e-2


@dataclass(frozen=True)
class Agreement:
    """One quantity, as each engine reported it."""

    quantity: str
    reference: float | int | None
    other: float | int | None
    tolerance: float | None = None
    agrees: bool = True
    #: Set when the comparison was not attempted, saying why.
    not_compared: str = ""

    @property
    def difference(self) -> float | None:
        if self.reference is None or self.other is None:
            return None
        return float(self.other) - float(self.reference)


@dataclass(frozen=True)
class Comparison:
    """The whole comparison of two solutions."""

    reference_id: str
    other_id: str
    agreements: tuple[Agreement, ...] = ()
    #: Station id -> the largest absolute component difference, in metres.
    coordinate_differences: dict[str, float] = field(default_factory=dict)
    #: Observation id -> the largest absolute residual difference.
    residual_differences: dict[str, float] = field(default_factory=dict)

    @property
    def agrees(self) -> bool:
        """Did every quantity that *was* compared agree?

        A quantity that could not be compared does not make this ``False``: it
        is not evidence of disagreement, and treating absence of evidence as
        evidence would make an unconvertible frame look like a defect in an
        engine.
        """
        return all(item.agrees for item in self.agreements if not item.not_compared)

    @property
    def disagreements(self) -> tuple[Agreement, ...]:
        return tuple(item for item in self.agreements if not item.agrees)

    @property
    def largest_coordinate_difference(self) -> float | None:
        return max(self.coordinate_differences.values(), default=None)

    def summary(self) -> str:
        """A line per quantity, for a report or a log."""
        lines = [f"{self.reference_id} vs {self.other_id}"]
        for item in self.agreements:
            if item.not_compared:
                lines.append(f"  -- {item.quantity}: not compared ({item.not_compared})")
                continue
            mark = "ok" if item.agrees else "**"
            lines.append(
                f"  {mark} {item.quantity}: {item.reference} vs {item.other}"
                + (f" (difference {item.difference:+.3e})" if item.difference is not None else "")
            )
        return "\n".join(lines)


def _exact(quantity: str, reference: int, other: int) -> Agreement:
    return Agreement(quantity, reference, other, agrees=reference == other)


def _within(
    quantity: str,
    reference: float | None,
    other: float | None,
    *,
    tolerance: float,
    relative: bool = False,
) -> Agreement:
    if reference is None or other is None:
        return Agreement(
            quantity,
            reference,
            other,
            not_compared="one of the two solutions does not report it",
        )
    difference = abs(other - reference)
    scale = max(abs(reference), abs(other)) if relative else 1.0
    return Agreement(
        quantity,
        reference,
        other,
        tolerance=tolerance,
        agrees=difference <= tolerance * (scale or 1.0),
    )


def compare(
    reference: Solution,
    other: Solution,
    *,
    coordinate_tolerance: float = COORDINATE_TOLERANCE,
    variance_tolerance: float = VARIANCE_TOLERANCE,
    residual_tolerance: float = COORDINATE_TOLERANCE,
) -> Comparison:
    """Compare two solutions of the same network.

    *reference* is conventionally the in-house one and *other* DynAdjust's, but
    nothing depends on which is which -- the comparison is symmetric, and the
    names only decide which column of the summary is which.
    """
    agreements: list[Agreement] = [
        _exact(
            "degrees of freedom",
            reference.statistics.degrees_of_freedom,
            other.statistics.degrees_of_freedom,
        ),
        _exact(
            "observations", reference.statistics.n_observations, other.statistics.n_observations
        ),
        _exact("parameters", reference.statistics.n_parameters, other.statistics.n_parameters),
        _within(
            "variance factor",
            reference.statistics.variance_factor_aposteriori,
            other.statistics.variance_factor_aposteriori,
            tolerance=variance_tolerance,
            relative=True,
        ),
    ]

    coordinates, coordinate_agreement = _compare_coordinates(
        reference, other, tolerance=coordinate_tolerance
    )
    agreements.append(coordinate_agreement)

    residuals, residual_agreement = _compare_residuals(
        reference, other, tolerance=residual_tolerance
    )
    agreements.append(residual_agreement)

    return Comparison(
        reference_id=reference.id,
        other_id=other.id,
        agreements=tuple(agreements),
        coordinate_differences=coordinates,
        residual_differences=residuals,
    )


def _frames(solution: Solution) -> set[CoordinateSystem]:
    return {station.position.system for station in solution.adjusted_stations}


def _compare_coordinates(
    reference: Solution, other: Solution, *, tolerance: float
) -> tuple[dict[str, float], Agreement]:
    """Largest component difference per station, when the frames allow it."""
    left, right = _frames(reference), _frames(other)
    if left != right:
        return {}, Agreement(
            "coordinates",
            None,
            None,
            not_compared=(
                f"the frames differ ({sorted(f.value for f in left)} vs "
                f"{sorted(f.value for f in right)}); a component of one is not a "
                "component of the other, and differencing them would produce a "
                "number that means nothing"
            ),
        )

    by_id = {station.station_id: station for station in other.adjusted_stations}
    differences: dict[str, float] = {}
    missing: list[str] = []
    for station in reference.adjusted_stations:
        match = by_id.get(station.station_id)
        if match is None:
            missing.append(station.station_id)
            continue
        differences[station.station_id] = max(
            abs(one.value - two.value)
            for one, two in zip(station.position.values, match.position.values, strict=True)
        )
    if missing:
        return differences, Agreement(
            "coordinates",
            None,
            None,
            not_compared=f"stations present in one solution only: {sorted(missing)[:10]}",
        )
    worst = max(differences.values(), default=0.0)
    return differences, Agreement(
        "coordinates (largest component difference, m)",
        0.0,
        worst,
        tolerance=tolerance,
        agrees=worst <= tolerance,
    )


def _compare_residuals(
    reference: Solution, other: Solution, *, tolerance: float
) -> tuple[dict[str, float], Agreement]:
    """Largest residual difference per observation.

    Both engines report one result per *row* of the design matrix, so a GNSS
    baseline has three. They are compared row by row in the order each solution
    lists them, which is the order both derive from the network; a differing
    count is reported rather than reconciled, because pairing rows by guesswork
    is how a comparison comes out clean while comparing the wrong things.
    """
    left: dict[str, list[float]] = {}
    for result in reference.observation_results:
        left.setdefault(result.observation_id, []).append(result.residual)
    right: dict[str, list[float]] = {}
    for result in other.observation_results:
        right.setdefault(result.observation_id, []).append(result.residual)

    if not left or not right:
        return {}, Agreement(
            "residuals",
            len(left) or None,
            len(right) or None,
            not_compared="one of the two solutions reports no observation results",
        )
    if set(left) != set(right):
        return {}, Agreement(
            "residuals",
            len(left),
            len(right),
            not_compared=(
                "the two solutions name different observations: "
                f"{sorted(set(left) ^ set(right))[:10]}"
            ),
        )

    differences: dict[str, float] = {}
    mismatched: list[str] = []
    for identifier, values in left.items():
        others = right[identifier]
        if len(values) != len(others):
            mismatched.append(identifier)
            continue
        differences[identifier] = max(
            abs(one - two) for one, two in zip(values, others, strict=True)
        )
    if mismatched:
        return differences, Agreement(
            "residuals",
            None,
            None,
            not_compared=f"different component counts for {sorted(mismatched)[:10]}",
        )
    worst = max(differences.values(), default=0.0)
    return differences, Agreement(
        "residuals (largest difference)",
        0.0,
        worst,
        tolerance=tolerance,
        agrees=worst <= tolerance,
    )
