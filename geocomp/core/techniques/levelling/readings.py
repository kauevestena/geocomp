# SPDX-License-Identifier: GPL-2.0-or-later
"""Staff readings, three-wire sets and instrument setups (FR-500, FR-160).

``specs/10-module-levelling.md`` sections 2 and 6.

A levelling field book is a list of readings, and everything downstream --
the scheme, the closure, the network -- is a way of combining them. So the
reading is the primitive, and it carries two things a bare number does not:

* **its sight distance**, because the balance check in ``specs/10`` section 2.1
  is arithmetic on distances and is simply unavailable without them; and
* **its three-wire set**, where one was read, because the spread of the three
  wires is an *empirical* precision estimate for that reading -- the only one in
  the whole module that comes from the observations themselves rather than from
  a manufacturer's brochure.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.findings import Finding, Severity
from geocomp.core.uncertainty import Quantity, Strategy, UncertaintyMode, combine_modes
from geocomp.core.units import Unit

__all__ = [
    "LevelSetup",
    "StaffReading",
    "ThreeWireReading",
    "empirical_reading_sigma",
]


@dataclass(frozen=True)
class ThreeWireReading:
    """Upper, middle and lower stadia wires read on one staff (FR-160).

    Three wires buy two things at once, and both are why the layout survives on
    precise work despite taking three times as long:

    * The **sight distance** comes free, by stadia: ``factor * (upper - lower)``.
      Which means the balance check of ``specs/10`` section 2.1 costs nothing.
    * The **half-sum check** ``(upper + lower) / 2 - middle`` has an expected
      value of exactly zero. A non-zero one is a misread wire, caught in the
      field on the spot rather than in the office a week later.
    """

    upper: Quantity
    middle: Quantity
    lower: Quantity

    def __post_init__(self) -> None:
        for name, quantity in (
            ("upper", self.upper),
            ("middle", self.middle),
            ("lower", self.lower),
        ):
            if not isinstance(quantity, Quantity):
                raise ValidationError(
                    "three_wire_reading_not_a_quantity",
                    component=name,
                    expected="a Quantity; every reading carries its uncertainty (FR-200)",
                )
            if quantity.unit is not Unit.METRE:
                raise ValidationError(
                    "three_wire_wrong_unit",
                    component=name,
                    received=quantity.unit.name,
                    expected=Unit.METRE.name,
                )
        if not self.lower.value < self.middle.value < self.upper.value:
            raise ValidationError(
                "three_wire_out_of_order",
                received=[self.lower.value, self.middle.value, self.upper.value],
                expected=(
                    "lower < middle < upper; a staff is read upwards, so any other "
                    "order means the three values were entered in the wrong columns"
                ),
            )

    @property
    def interval(self) -> Quantity:
        """``upper - lower``, from which the sight distance follows."""
        return self.upper - self.lower

    @property
    def half_sum_residual(self) -> float:
        """``(upper + lower) / 2 - middle``. Expected zero; a check, not a value."""
        return (self.upper.value + self.lower.value) / 2.0 - self.middle.value

    def mean(self) -> Quantity:
        """The mean of the three wires, with its uncertainty propagated.

        Rigorous propagation of three readings, **not** their sample spread. The
        three wires read three deliberately *different* heights on the staff, so
        their variance is the stadia interval and has nothing to do with reading
        error -- treating it as a precision estimate would report a sigma of
        centimetres for a reading good to half a millimetre.

        The empirical evidence in a three-wire set is the half-sum residual, and
        one set carries a single degree of freedom, which is nearly worthless on
        its own. :func:`empirical_reading_sigma` pools it across a line, where it
        becomes a real check on the nominal precision.
        """
        mean = (self.lower.value + self.middle.value + self.upper.value) / 3.0
        # Three readings of the reticle against the staff, taken as independent
        # -- the same assumption every scalar operation in
        # :mod:`geocomp.core.uncertainty` makes, so it is not tagged here as a
        # strategy that other arithmetic would not tag.
        variance = (self.upper.variance + self.middle.variance + self.lower.variance) / 9.0
        mode, strategies = combine_modes(self.upper, self.middle, self.lower)
        return Quantity(
            value=mean, variance=variance, unit=Unit.METRE, mode=mode, strategies=strategies
        )

    def stadia_distance(self, factor: float, sigma_reading: float | None = None) -> Quantity:
        """Sight distance by stadia: ``factor * (upper - lower)``.

        Args:
            factor: The instrument's stadia multiplication constant.
            sigma_reading: Standard deviation of one outer-wire reading. When
                given it is propagated through the interval; when not, the
                interval's own propagated uncertainty is used.
        """
        if factor <= 0.0:
            raise ValidationError(
                "stadia_factor_not_positive",
                received=factor,
                expected="a positive stadia multiplication constant, usually 100",
            )
        if sigma_reading is None:
            return self.interval * factor
        return Quantity.approximate(
            (self.upper.value - self.lower.value) * factor,
            factor * sigma_reading * (2.0**0.5),
            Unit.METRE,
            Strategy.NOMINAL_PRECISION,
        )

    def check(self, tolerance: float, *, label: str = "") -> Finding | None:
        """The half-sum check, as a finding or ``None`` when it passes."""
        residual = self.half_sum_residual
        if abs(residual) <= tolerance:
            return None
        return Finding(
            code="three_wire_half_sum",
            severity=Severity.WARNING,
            message=(
                f"the three wires of {label or 'a reading'} give "
                f"(upper + lower) / 2 - middle = {residual:+.4f} m, which should be "
                "zero. One of the three was misread, or they were entered in the "
                "wrong columns"
            ),
            value=abs(residual),
            threshold=tolerance,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "upper": self.upper.to_dict(),
            "middle": self.middle.to_dict(),
            "lower": self.lower.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ThreeWireReading:
        return cls(
            upper=Quantity.from_dict(payload["upper"]),
            middle=Quantity.from_dict(payload["middle"]),
            lower=Quantity.from_dict(payload["lower"]),
        )


@dataclass(frozen=True)
class StaffReading:
    """One reading of a staff standing on a station.

    Attributes:
        station: The point the staff stood on. A turning point gets an id like
            any other station -- it is a station, briefly.
        reading: The staff reading, metres, with its uncertainty.
        distance: The sight distance, metres, or ``None`` where it was not
            recorded. ``None`` is not zero: it disables the balance check for
            this setup and says so, rather than reporting a perfectly balanced
            setup that nobody measured.
        three_wire: The wires this reading was formed from, where three were
            read.
    """

    station: str
    reading: Quantity
    distance: Quantity | None = None
    three_wire: ThreeWireReading | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.station or not self.station.strip():
            raise ValidationError(
                "staff_reading_without_station",
                expected="the id of the point the staff stood on",
            )
        if not isinstance(self.reading, Quantity):
            raise ValidationError(
                "staff_reading_not_a_quantity",
                station=self.station,
                expected="a Quantity; every reading carries its uncertainty (FR-200)",
            )
        for name, quantity in (("reading", self.reading), ("distance", self.distance)):
            if quantity is not None and quantity.unit is not Unit.METRE:
                raise ValidationError(
                    "staff_reading_wrong_unit",
                    station=self.station,
                    parameter=name,
                    received=quantity.unit.name,
                    expected=Unit.METRE.name,
                )
        if self.distance is not None and self.distance.value < 0.0:
            raise ValidationError(
                "negative_sight_distance",
                station=self.station,
                received=self.distance.value,
                expected="a non-negative sight distance",
            )

    @property
    def has_distance(self) -> bool:
        return self.distance is not None

    @property
    def distance_value(self) -> float:
        """The sight distance, or zero when none was recorded.

        Only for arithmetic that has already established the distance exists --
        :attr:`has_distance` is the question to ask first.
        """
        return self.distance.value if self.distance is not None else 0.0

    @classmethod
    def from_three_wire(
        cls,
        station: str,
        three_wire: ThreeWireReading,
        *,
        stadia_factor: float = 100.0,
        sigma_reading: float | None = None,
        meta: dict[str, Any] | None = None,
    ) -> StaffReading:
        """Build a reading from a three-wire set, deriving the sight distance."""
        return cls(
            station=station,
            reading=three_wire.mean(),
            distance=three_wire.stadia_distance(stadia_factor, sigma_reading),
            three_wire=three_wire,
            meta=dict(meta or {}),
        )


@dataclass(frozen=True)
class LevelSetup:
    """One instrument position: one backsight and one or more foresights.

    The number of foresights is what distinguishes the schemes, and it is a
    property of the data rather than a mode the user selects:

    * **one** foresight is the ordinary equal-sights setup (FR-500);
    * **several** are extreme sights (FR-502), and they are correlated, because
      they all subtract the same backsight reading.

    Attributes:
        backsight: The reading back along the line, onto the known point.
        foresights: The readings forward. Ordered, and the order is preserved
            into the cluster covariance -- for the same reason
            :class:`~geocomp.core.models.observation.Cluster` stores its member
            order explicitly.
    """

    id: str
    backsight: StaffReading
    foresights: tuple[StaffReading, ...]
    level_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError(
                "level_setup_without_id",
                expected="an id; observations and findings reference a setup by it",
            )
        if not self.foresights:
            raise ValidationError(
                "level_setup_without_foresight",
                setup=self.id,
                expected=(
                    "at least one foresight; a backsight alone determines no height "
                    "difference"
                ),
            )
        stations = [self.backsight.station, *(sight.station for sight in self.foresights)]
        if len(set(stations)) != len(stations):
            raise ValidationError(
                "level_setup_repeats_a_station",
                setup=self.id,
                received=stations,
                expected=(
                    "distinct stations; a sight onto the same point twice from one setup "
                    "gives a height difference of zero by construction and adds nothing"
                ),
            )

    @property
    def is_extreme_sights(self) -> bool:
        """Whether this setup carries several foresights (FR-502)."""
        return len(self.foresights) > 1

    @property
    def has_distances(self) -> bool:
        """Whether every sight of this setup recorded its distance."""
        return self.backsight.has_distance and all(
            sight.has_distance for sight in self.foresights
        )

    def imbalance(self, foresight_index: int = 0) -> float | None:
        """Backsight minus foresight distance, metres, or ``None`` if unrecorded."""
        foresight = self.foresights[foresight_index]
        if not (self.backsight.has_distance and foresight.has_distance):
            return None
        return self.backsight.distance_value - foresight.distance_value

    @property
    def sight_length(self) -> float:
        """The total sighted distance through this setup, metres.

        Backsight plus the *longest* foresight, not the sum of all of them: the
        line advances by one backsight and one foresight however many extra
        points were levelled from the same position, and using the sum would
        inflate the line length that the weighting depends on.
        """
        if not self.has_distances:
            return 0.0
        return self.backsight.distance_value + max(
            sight.distance_value for sight in self.foresights
        )

    @property
    def mode(self) -> UncertaintyMode:
        modes = [self.backsight.reading.mode, *(s.reading.mode for s in self.foresights)]
        return (
            UncertaintyMode.APPROXIMATE
            if UncertaintyMode.APPROXIMATE in modes
            else UncertaintyMode.RIGOROUS
        )


def empirical_reading_sigma(
    readings: Sequence[ThreeWireReading],
) -> tuple[float | None, int]:
    """An empirical staff-reading sigma pooled from half-sum residuals (FR-160).

    The half-sum residual of one set is::

        e = (u + l) / 2 - m = (eps_u + eps_l) / 2 - eps_m

    so with three independent readings of equal precision ``var(e) = 1.5 sigma^2``
    and each set contributes **one** degree of freedom. Pooled over *n* sets::

        sigma_hat = sqrt( sum(e_i^2) / (1.5 n) )

    This is the only precision figure in the whole levelling module that comes
    from the observations rather than from a manufacturer's specification, which
    is what makes it worth computing: it is the one number that can contradict
    the instrument profile.

    Returns:
        The pooled estimate and the number of degrees of freedom behind it.
        ``(None, 0)`` for an empty input. **The count is returned rather than
        buried** because one or two sets give an estimate too unstable to act
        on, and a caller that cannot see the count cannot know that.
    """
    residuals = [reading.half_sum_residual for reading in readings]
    if not residuals:
        return None, 0
    total = sum(residual**2 for residual in residuals)
    return math.sqrt(total / (1.5 * len(residuals))), len(residuals)
