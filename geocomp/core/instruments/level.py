# SPDX-License-Identifier: GPL-2.0-or-later
"""Levels and levelling accuracy classes (FR-061, FR-503, FR-504).

``specs/10-module-levelling.md`` sections 2, 3 and 4.

Two records, and they answer different questions.

A :class:`LevelProfile` answers *how good is this instrument*: the two precision
figures the two weighting models need, and the collimation from a two-peg test.
Those belong to a piece of equipment and travel with it between jobs.

A :class:`LevellingClass` answers *how good does this job have to be*: the
permissible misclosure and the sight-geometry limits a line is judged against.
Those belong to the specification the work is done under, not to the level.

**GeoComp ships no table of national tolerance values, deliberately.** The
permissible misclosure is ``k * sqrt(L)`` everywhere, but *k* differs by country,
by class within a country, and by edition of the standard. A transcribed value
that is wrong does not fail loudly: it silently accepts a line that should have
been re-run, or rejects one that was fine, and the surveyor has no way to see
which. So a class is a record the user fills in from the specification in front
of them, and :attr:`LevellingClass.source` records which document that was --
which is what makes a closure report defensible rather than merely printed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import Unit

__all__ = ["LevelProfile", "LevellingClass"]


@dataclass(frozen=True)
class LevellingClass:
    """The specification a levelling line is judged against (FR-503).

    Attributes:
        tolerance_coefficient: *k* in the permissible misclosure
            ``k * sqrt(L)``, in **metres per square root of a kilometre**. Zero
            means no tolerance has been configured, and a closure check then
            reports the misclosure with no verdict rather than inventing one.
        max_sight_length: Longest permitted sight, metres. Zero is unconstrained.
        max_sight_imbalance: Largest permitted backsight-minus-foresight
            distance **per setup**, metres. Zero is unconstrained.
        max_accumulated_imbalance: Largest permitted imbalance **accumulated
            over a line**, metres. This is the one that matters: per-setup
            imbalances of alternating sign cost nothing, and it is their sum
            that drives the residual collimation error (``specs/10`` section
            2.1). Zero is unconstrained.
        source: The document these numbers came from. Empty means the user
            entered them without citing one, which a report says plainly.
    """

    id: str
    name: str = ""
    tolerance_coefficient: float = 0.0
    max_sight_length: float = 0.0
    max_sight_imbalance: float = 0.0
    max_accumulated_imbalance: float = 0.0
    source: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError(
                "levelling_class_without_id",
                expected="a non-empty id; lines and reports reference a class by it",
            )
        for name, value in (
            ("tolerance_coefficient", self.tolerance_coefficient),
            ("max_sight_length", self.max_sight_length),
            ("max_sight_imbalance", self.max_sight_imbalance),
            ("max_accumulated_imbalance", self.max_accumulated_imbalance),
        ):
            if value < 0.0:
                raise ValidationError(
                    "levelling_class_negative_limit",
                    levelling_class=self.id,
                    parameter=name,
                    received=value,
                    expected="a non-negative limit; zero means unconstrained",
                )

    @property
    def label(self) -> str:
        return self.name or self.id

    @property
    def has_tolerance(self) -> bool:
        """Whether a permissible misclosure can be computed at all."""
        return self.tolerance_coefficient > 0.0

    def permissible_misclosure(self, length_km: float) -> float | None:
        """``k * sqrt(L)`` in metres, or ``None`` when no *k* is configured.

        ``None`` rather than a large number: "we do not know the tolerance" and
        "the tolerance is generous" are different statements, and only one of
        them should let a line pass.
        """
        if not self.has_tolerance:
            return None
        if length_km < 0.0:
            raise ValidationError(
                "negative_line_length",
                levelling_class=self.id,
                received=length_km,
                expected="a non-negative line length in kilometres",
            )
        return self.tolerance_coefficient * math.sqrt(length_km)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "tolerance_coefficient": self.tolerance_coefficient,
            "max_sight_length": self.max_sight_length,
            "max_sight_imbalance": self.max_sight_imbalance,
            "max_accumulated_imbalance": self.max_accumulated_imbalance,
        }
        for key, value in (("name", self.name), ("source", self.source)):
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LevellingClass:
        return cls(
            id=payload["id"],
            name=payload.get("name", ""),
            tolerance_coefficient=float(payload.get("tolerance_coefficient", 0.0)),
            max_sight_length=float(payload.get("max_sight_length", 0.0)),
            max_sight_imbalance=float(payload.get("max_sight_imbalance", 0.0)),
            max_accumulated_imbalance=float(payload.get("max_accumulated_imbalance", 0.0)),
            source=payload.get("source", ""),
        )


@dataclass(frozen=True)
class LevelProfile:
    """One level, with its calibration and its two precision figures (FR-061).

    **Two sigmas, because there are two weighting models.** FR-504 lets a height
    difference be weighted by line length or by number of setups, and the two
    are not convertible without knowing the sight lengths -- which is the whole
    point of offering both. So the profile carries the constant of
    proportionality for each, and refuses to derive one from the other.

    Attributes:
        collimation: The line-of-sight tilt *c*, radians, from a two-peg test.
            Positive when the line of sight rises. It cancels in an equal-sight
            setup and does not cancel in an imbalanced one, which is what
            ``specs/10`` section 2.1's balance check is about.
        applies_collimation: Whether the instrument already removes it -- a
            digital level with a stored calibration does. The applied-once rule:
            correcting a second time doubles the error.
        sigma_per_km: Standard deviation of a height difference, in metres per
            square root of a kilometre. The figure manufacturers publish, and
            the constant for length weighting.
        sigma_per_setup: Standard deviation contributed by one setup, in metres.
            The constant for setup weighting.
        sigma_reading: Standard deviation of one staff reading, metres. Used for
            the three-wire mean's expected dispersion, which is what makes an
            imported three-wire set checkable rather than merely averaged.
        stadia_factor: Sight distance is ``factor * (upper - lower)``. A hundred
            on essentially every instrument, but it is an instrument constant
            and GeoComp does not assume constants (``specs/10`` section 6).
        sigma_stadia_reading: Standard deviation of an outer-wire reading,
            metres. Zero falls back to ``sigma_reading``: the outer wires are
            read less carefully than the middle one in practice, but claiming a
            specific degradation nobody measured would be inventing a number.
    """

    id: str
    name: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    calibration_date: str = ""
    calibration_reference: str = ""

    collimation: Quantity = field(default_factory=lambda: Quantity.exact(0.0, Unit.RADIAN))
    applies_collimation: bool = False

    sigma_per_km: float = 0.0
    sigma_per_setup: float = 0.0
    sigma_reading: float = 0.0

    stadia_factor: float = 100.0
    sigma_stadia_reading: float = 0.0

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError(
                "level_profile_without_id",
                expected="a non-empty id; observations reference profiles by it",
            )
        if self.collimation.unit is not Unit.RADIAN:
            raise ValidationError(
                "profile_wrong_unit",
                parameter="level.collimation",
                received=self.collimation.unit.name,
                expected=Unit.RADIAN.name,
            )
        for name, value in (
            ("sigma_per_km", self.sigma_per_km),
            ("sigma_per_setup", self.sigma_per_setup),
            ("sigma_reading", self.sigma_reading),
            ("sigma_stadia_reading", self.sigma_stadia_reading),
        ):
            if value < 0.0:
                raise ValidationError(
                    "level_sigma_negative",
                    level=self.id,
                    parameter=name,
                    received=value,
                    expected="a non-negative standard deviation",
                )
        if self.stadia_factor <= 0.0:
            raise ValidationError(
                "level_stadia_factor_not_positive",
                level=self.id,
                received=self.stadia_factor,
                expected="a positive stadia multiplication constant, usually 100",
            )

    @property
    def label(self) -> str:
        return self.name or self.id

    # -- stochastic model -------------------------------------------------

    def sigma_for_length(self, length_km: float) -> float | None:
        """``sigma_per_km * sqrt(L)``, or ``None`` when the profile has no figure.

        ``None`` rather than zero, for the same reason as everywhere else in
        GeoComp: a profile that says nothing about precision has not claimed the
        instrument is perfect.
        """
        if self.sigma_per_km <= 0.0:
            return None
        if length_km < 0.0:
            raise ValidationError(
                "negative_line_length",
                level=self.id,
                received=length_km,
                expected="a non-negative line length in kilometres",
            )
        return self.sigma_per_km * math.sqrt(length_km)

    def sigma_for_setups(self, setups: int) -> float | None:
        """``sigma_per_setup * sqrt(n)``, or ``None`` when unconfigured."""
        if self.sigma_per_setup <= 0.0:
            return None
        if setups < 0:
            raise ValidationError(
                "negative_setup_count",
                level=self.id,
                received=setups,
                expected="a non-negative number of setups",
            )
        return self.sigma_per_setup * math.sqrt(setups)

    @property
    def reading_sigma(self) -> float | None:
        return self.sigma_reading if self.sigma_reading > 0.0 else None

    @property
    def stadia_sigma(self) -> float | None:
        """The outer-wire reading sigma, falling back to the middle-wire one."""
        if self.sigma_stadia_reading > 0.0:
            return self.sigma_stadia_reading
        return self.reading_sigma

    def reading_quantity(self, value: float) -> Quantity:
        """One staff reading with the profile's nominal precision attached."""
        sigma = self.reading_sigma
        if sigma is None:
            raise ValidationError(
                "level_without_reading_sigma",
                level=self.id,
                expected=(
                    "a sigma_reading on the level profile; GeoComp does not invent one, "
                    "because a fabricated weight corrupts every statistic computed from it"
                ),
            )
        return Quantity.approximate(value, sigma, Unit.METRE, Strategy.NOMINAL_PRECISION)

    def collimation_correction(self, imbalance: float) -> Quantity:
        """The residual collimation correction for a sight imbalance (FR-500).

        A collimation *c* tilts the line of sight, so a staff at distance *d* is
        read too high by ``c * d``::

            r_true = r_obs - c * d

        A height difference is a difference of two such readings, so::

            dh = (b_obs - c * d_b) - (f_obs - c * d_f)
               = (b_obs - f_obs) - c * (d_b - d_f)

        The correction is therefore ``-c * imbalance`` -- **zero when the sights
        are equal**, whatever *c* is, which is the whole reason equal sights are
        the preferred method and why *c* need not even be known for a balanced
        line.

        Args:
            imbalance: Backsight minus foresight distance, metres. Accumulated
                over a line, this is the number the balance check reports,
                because per-setup imbalances of alternating sign cancel and only
                their sum drives the residual error.

        Returns:
            The correction to **add** to the observed height difference, with
            the collimation's own uncertainty propagated. An instrument that
            already applies its calibration returns an exact zero rather than a
            second correction -- the applied-once rule.
        """
        if self.applies_collimation:
            return Quantity.exact(0.0, Unit.METRE)
        return Quantity(
            value=-self.collimation.value * imbalance,
            variance=self.collimation.variance * imbalance**2,
            unit=Unit.METRE,
            mode=self.collimation.mode,
            strategies=self.collimation.strategies,
        )

    # -- serialisation ----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "collimation": self.collimation.to_dict(),
            "applies_collimation": self.applies_collimation,
            "sigma_per_km": self.sigma_per_km,
            "sigma_per_setup": self.sigma_per_setup,
            "sigma_reading": self.sigma_reading,
            "stadia_factor": self.stadia_factor,
            "sigma_stadia_reading": self.sigma_stadia_reading,
        }
        for key, value in (
            ("name", self.name),
            ("manufacturer", self.manufacturer),
            ("model", self.model),
            ("serial_number", self.serial_number),
            ("calibration_date", self.calibration_date),
            ("calibration_reference", self.calibration_reference),
        ):
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LevelProfile:
        return cls(
            id=payload["id"],
            name=payload.get("name", ""),
            manufacturer=payload.get("manufacturer", ""),
            model=payload.get("model", ""),
            serial_number=payload.get("serial_number", ""),
            calibration_date=payload.get("calibration_date", ""),
            calibration_reference=payload.get("calibration_reference", ""),
            collimation=Quantity.from_dict(payload["collimation"]),
            applies_collimation=bool(payload.get("applies_collimation", False)),
            sigma_per_km=float(payload.get("sigma_per_km", 0.0)),
            sigma_per_setup=float(payload.get("sigma_per_setup", 0.0)),
            sigma_reading=float(payload.get("sigma_reading", 0.0)),
            stadia_factor=float(payload.get("stadia_factor", 100.0)),
            sigma_stadia_reading=float(payload.get("sigma_stadia_reading", 0.0)),
        )
