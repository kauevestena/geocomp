# SPDX-License-Identifier: GPL-2.0-or-later
"""Weighting a difference observation by how much observing went into it.

``specs/10-module-levelling.md`` section 4 (FR-504) and
``specs/12-module-gravimetry.md``.

**This module is deliberately not in the levelling package**, and the reason is
recorded in ADR-0002, Amendment 1: a gravity difference and a height difference
are the same observation equation, so a drift-corrected gravimetric network is a
level network wearing different units. Everything here would otherwise be
written twice, in two packages, with two chances of being wrong differently.

The model is one line::

    sigma = coefficient * sqrt(extent)

and everything interesting is in what *extent* means:

* **Length.** A levelling line's error accumulates with distance, so
  ``sigma = k * sqrt(L)`` with *L* in kilometres. Suits long lines with
  consistent sight lengths.
* **Count.** It accumulates per setup instead, so ``sigma = k * sqrt(n)``. Suits
  short, irregular lines where the per-setup reading error dominates and sight
  lengths vary too much for length to stand in for effort.
* **Duration.** It accumulates with elapsed time -- a gravimeter's drift does,
  which is why this member exists here in phase P4 rather than being added in
  P8. An abstraction that has been used once is an assertion; used twice, it is
  a design.
* **None.** Every observation weighted alike. A real choice, not a fallback:
  GNSS-derived height differences over one baseline length are not better for
  being shorter.

The two are **not convertible**, which is exactly why FR-504 offers both rather
than picking one. Converting between them would need the sight lengths of every
setup, and if those were known the choice would not arise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import Unit

__all__ = ["DifferenceWeighting", "ExtentKind"]


class ExtentKind(Enum):
    """What accumulates along a difference observation.

    Recorded on the result rather than inferred, because a network weighted by
    length and one weighted by setup count are different objects and the
    statistics do not distinguish them -- the same reason
    :class:`~geocomp.core.instruments.stochastic.SigmaSource` exists.
    """

    #: Route length. Levelling in kilometres.
    LENGTH = "length"
    #: Instrument stations: levelling setups, gravimetric ties.
    COUNT = "count"
    #: Elapsed time. A gravimeter's drift accumulates in it (FR-702).
    DURATION = "duration"
    #: Every observation weighted alike.
    NONE = "none"

    @property
    def accumulates(self) -> bool:
        return self is not ExtentKind.NONE


@dataclass(frozen=True)
class DifferenceWeighting:
    """The stochastic model of a 1D difference observation (FR-504, FR-064).

    Attributes:
        kind: What the extent measures.
        coefficient: The constant of proportionality, in the observation's unit
            per square root of one unit of extent. For levelling with
            ``ExtentKind.LENGTH`` this is the manufacturer's metres-per-root-
            kilometre figure.
        unit: The unit of the observation being weighted -- metres for a height
            difference, ``ACCELERATION`` for a gravity difference. Carried so a
            weighting cannot be silently applied to the wrong quantity.
        extent_label: What one unit of extent is called, for the report:
            ``"km"``, ``"setups"``, ``"hours"``. Presentational only, and empty
            is allowed.
        strategy: How the coefficient was arrived at. A manufacturer's figure is
            :attr:`~geocomp.core.uncertainty.Strategy.NOMINAL_PRECISION`; one
            derived from the residuals of a previous adjustment is
            ``EMPIRICAL_SCALING``, and the difference matters to anyone reading
            the variance factor afterwards.
    """

    kind: ExtentKind
    coefficient: float
    unit: Unit = Unit.METRE
    extent_label: str = ""
    strategy: Strategy = Strategy.NOMINAL_PRECISION

    def __post_init__(self) -> None:
        if self.coefficient <= 0.0:
            raise ValidationError(
                "weighting_coefficient_not_positive",
                received=self.coefficient,
                expected=(
                    "a positive constant of proportionality; a zero coefficient claims "
                    "every difference is exact and gives an infinite weight"
                ),
            )
        if self.unit not in (Unit.METRE, Unit.ACCELERATION):
            raise ValidationError(
                "weighting_unsupported_unit",
                received=self.unit.name,
                expected=(
                    "METRE for a height difference or ACCELERATION for a gravity "
                    "difference; a 1D difference network holds one or the other"
                ),
            )

    def sigma(self, extent: float = 1.0) -> float:
        """The standard deviation for an observation of the given extent."""
        if not self.kind.accumulates:
            return self.coefficient
        if extent < 0.0:
            raise ValidationError(
                "negative_extent",
                kind=self.kind.value,
                received=extent,
                expected=f"a non-negative extent in {self.extent_label or 'the extent unit'}",
            )
        return self.coefficient * math.sqrt(extent)

    def apply(self, value: float, extent: float = 1.0) -> Quantity:
        """A difference with this model's uncertainty attached.

        Replaces whatever uncertainty the value arrived with. That is the point
        and it is not free: the propagated uncertainty of a levelled difference
        comes from the staff readings alone and is routinely optimistic, because
        it knows nothing of refraction, staff calibration or a tripod settling.
        The ``k * sqrt(L)`` model is fitted to lines that suffered all three. So
        the choice between them is a real one, the strategy is recorded, and
        nothing here decides it silently.
        """
        sigma = self.sigma(extent)
        if sigma <= 0.0:
            raise ValidationError(
                "weighting_gave_zero_sigma",
                kind=self.kind.value,
                extent=extent,
                expected=(
                    "a positive extent; an observation of zero extent gets zero "
                    "uncertainty and therefore infinite weight, which would dominate "
                    "the whole network"
                ),
            )
        return Quantity.approximate(value, sigma, self.unit, self.strategy)

    def reweight(self, quantity: Quantity, extent: float = 1.0) -> Quantity:
        """Re-attach this model's uncertainty to an existing quantity."""
        if quantity.unit is not self.unit:
            raise ValidationError(
                "weighting_unit_mismatch",
                received=quantity.unit.name,
                expected=self.unit.name,
            )
        return self.apply(quantity.value, extent)

    @property
    def describe(self) -> str:
        """A one-line statement of the model, for a provenance record."""
        if not self.kind.accumulates:
            return f"sigma = {self.coefficient:g} {self.unit.value}, uniform"
        label = self.extent_label or self.kind.value
        return f"sigma = {self.coefficient:g} {self.unit.value} * sqrt({label})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.name,
            "coefficient": self.coefficient,
            "unit": self.unit.name,
            "extent_label": self.extent_label,
            "strategy": self.strategy.name,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DifferenceWeighting:
        return cls(
            kind=ExtentKind[payload["kind"]],
            coefficient=float(payload["coefficient"]),
            unit=Unit[payload.get("unit", Unit.METRE.name)],
            extent_label=payload.get("extent_label", ""),
            strategy=Strategy[payload.get("strategy", Strategy.NOMINAL_PRECISION.name)],
        )
