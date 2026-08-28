# SPDX-License-Identifier: GPL-2.0-or-later
"""Named instrument and reflector profiles (FR-061, FR-069).

``specs/15-ui-menu-and-settings.md`` section 2.2.

Every constant here carries **its own uncertainty**, because a calibrated
additive constant of -30.0 mm known to +/- 0.3 mm and one known to +/- 3 mm
produce different -- and differently trustworthy -- reduced distances (FR-204).
Storing the constant without its uncertainty makes the second look like the
first.

Two rules in this module are worth stating up front, because both prevent
silent metre- or centimetre-level errors:

* **Applied-once.** ``applies_internally`` records what the instrument already
  did to the reading. A prism constant applied by the instrument *and* by
  GeoComp is a silent error of twice the constant, and nothing downstream can
  detect it.
* **Nominal is not measured.** A precision taken from the manufacturer's
  brochure is flagged :attr:`~geocomp.core.uncertainty.Strategy.NOMINAL_PRECISION`,
  so a report can say where the number came from. Nominal specifications are
  usually optimistic; the residual analysis in phase P2 is what tells the user
  whether the assumption held.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.instruments.level import LevellingClass, LevelProfile
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import Unit

__all__ = [
    "AtmosphericModel",
    "EdmSpecification",
    "InstrumentProfile",
    "ProfileLibrary",
    "ReflectorProfile",
    "angular_specification",
]


class AtmosphericModel(Enum):
    """Which first-velocity formula an instrument's manufacturer specifies.

    The differences between these are at the 0.1 ppm level -- immaterial on a
    20 m sight and worth a millimetre over 10 km. GeoComp offers the choice
    (FR-062) and records which was used rather than picking one silently.
    """

    #: Barrell and Sears via the IUGG 1960 / Ciddor formulation. The general
    #: default, and what most modern instruments assume.
    BARRELL_SEARS = "barrell_sears"
    #: The simplified formula printed in many Leica manuals.
    LEICA = "leica"
    #: The simplified formula printed in many Trimble manuals.
    TRIMBLE = "trimble"


@dataclass(frozen=True)
class EdmSpecification:
    """The distance precision an EDM claims, as ``sigma = a + b * d``.

    The manufacturer's two-part specification: a constant part dominated by the
    instrument's internal timing, and a proportional part in parts per million.

    Attributes:
        constant: *a*, in metres.
        proportional: *b*, dimensionless (so 2 ppm is ``2e-6``).
        scale: A user factor on the whole thing. Nominal specifications are
            usually optimistic, and a surveyor who has run residual analysis on
            their own instrument has a better number than the brochure.
    """

    constant: float
    proportional: float
    scale: float = 1.0

    def __post_init__(self) -> None:
        for name, value in (
            ("constant", self.constant),
            ("proportional", self.proportional),
            ("scale", self.scale),
        ):
            if value < 0.0:
                raise ValidationError(
                    "edm_specification_negative",
                    parameter=name,
                    received=value,
                    expected="a non-negative value; a precision cannot be negative",
                )

    def sigma(self, distance: float) -> float:
        """The standard deviation claimed for a distance of *distance* metres."""
        return self.scale * (self.constant + self.proportional * abs(distance))

    def to_dict(self) -> dict[str, Any]:
        return {"constant": self.constant, "proportional": self.proportional, "scale": self.scale}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> EdmSpecification:
        return cls(
            constant=float(payload["constant"]),
            proportional=float(payload["proportional"]),
            scale=float(payload.get("scale", 1.0)),
        )


def angular_specification(
    sigma: float, *, sets: int = 1, strategies: tuple[Strategy, ...] = ()
) -> Quantity:
    """The angular precision of a mean of *sets* independent sets.

    ``sigma`` is the precision of a single set, and the mean of *n* independent
    sets improves as ``1 / sqrt(n)`` (``specs/09`` section 3). Returned as a
    :class:`Quantity` of value zero so that the caller adds it to a reading:
    it *is* an uncertainty, and the value is a correction of nothing.
    """
    if sets < 1:
        raise ValidationError(
            "non_positive_set_count", received=sets, expected="at least one set"
        )
    if strategies:
        return Quantity.approximate(0.0, sigma / (sets**0.5), Unit.RADIAN, *strategies)
    return Quantity.from_std_dev(0.0, sigma / (sets**0.5), Unit.RADIAN)


@dataclass(frozen=True)
class ReflectorProfile:
    """A prism or reflective target, with its constant (FR-061).

    Attributes:
        additive_constant: The prism constant, in metres. Conventionally
            negative -- the optical centre lies behind the physical mount, so
            the constant shortens the measured distance.
        applies_internally: Whether the instrument is configured to apply this
            constant itself. When true GeoComp does not apply it again.
    """

    id: str
    name: str = ""
    additive_constant: Quantity = field(
        default_factory=lambda: Quantity.exact(0.0, Unit.METRE)
    )
    applies_internally: bool = False
    manufacturer: str = ""
    model: str = ""
    calibration_date: str = ""
    calibration_reference: str = ""

    def __post_init__(self) -> None:
        _require_id(self.id, "reflector")
        _require_unit(self.additive_constant, Unit.METRE, "reflector.additive_constant")

    @property
    def label(self) -> str:
        return self.name or self.id

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "additive_constant": self.additive_constant.to_dict(),
            "applies_internally": self.applies_internally,
        }
        for key, value in (
            ("name", self.name),
            ("manufacturer", self.manufacturer),
            ("model", self.model),
            ("calibration_date", self.calibration_date),
            ("calibration_reference", self.calibration_reference),
        ):
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ReflectorProfile:
        return cls(
            id=payload["id"],
            name=payload.get("name", ""),
            additive_constant=Quantity.from_dict(payload["additive_constant"]),
            applies_internally=bool(payload.get("applies_internally", False)),
            manufacturer=payload.get("manufacturer", ""),
            model=payload.get("model", ""),
            calibration_date=payload.get("calibration_date", ""),
            calibration_reference=payload.get("calibration_reference", ""),
        )


@dataclass(frozen=True)
class InstrumentProfile:
    """One total station, with its calibration constants and precisions.

    Attributes:
        collimation: Horizontal collimation error *c*, in radians. Applied only
            to single-face readings: a face pair cancels it, and applying it
            there as well would double it.
        vertical_index: Vertical index error *i*, in radians. Same rule.
        trunnion_tilt: Horizontal-axis (trunnion) tilt, in radians.
        edm_additive: The instrument half of the additive constant, in metres.
            The reflector carries its own.
        edm_scale: Multiplicative scale error, dimensionless, from calibration
            over a baseline. A value of ``1 + 3e-6`` is a 3 ppm scale error.
        cyclic_error_amplitude: Amplitude of the EDM's cyclic (short-periodic)
            error, in metres, where calibration provides it.
        cyclic_error_wavelength: Its wavelength, in metres.
        applies_edm_constant / applies_atmospheric: What the instrument already
            did. See the module docstring's applied-once rule.
        sigma_direction / sigma_zenith: Single-set angular precisions, radians.
        sigma_zenith_refraction: An extra zenith-angle term proportional to
            distance, in radians per metre, standing for refraction's effect on
            the vertical -- the term that makes a long trigonometric height much
            worse than a short one.
        sigma_instrument_height / sigma_target_height: In metres. Routinely the
            dominant error in short-sight height differences, which is exactly
            why they are on the profile rather than assumed to be zero.
    """

    id: str
    name: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    calibration_date: str = ""
    calibration_reference: str = ""

    collimation: Quantity = field(default_factory=lambda: Quantity.exact(0.0, Unit.RADIAN))
    vertical_index: Quantity = field(default_factory=lambda: Quantity.exact(0.0, Unit.RADIAN))
    trunnion_tilt: Quantity = field(default_factory=lambda: Quantity.exact(0.0, Unit.RADIAN))

    edm_additive: Quantity = field(default_factory=lambda: Quantity.exact(0.0, Unit.METRE))
    edm_scale: Quantity = field(
        default_factory=lambda: Quantity.exact(1.0, Unit.DIMENSIONLESS)
    )
    cyclic_error_amplitude: Quantity = field(
        default_factory=lambda: Quantity.exact(0.0, Unit.METRE)
    )
    cyclic_error_wavelength: float = 0.0

    applies_edm_constant: bool = False
    applies_atmospheric: bool = False
    atmospheric_model: AtmosphericModel = AtmosphericModel.BARRELL_SEARS
    #: The refractive index the EDM assumes when no atmospheric correction is
    #: applied -- the reference condition its ppm scale is defined against.
    reference_refractive_index: float = 1.0002830

    edm: EdmSpecification = field(
        default_factory=lambda: EdmSpecification(constant=0.002, proportional=2e-6)
    )
    sigma_direction: float = 5.0e-6
    sigma_zenith: float = 5.0e-6
    sigma_zenith_refraction: float = 0.0
    sigma_instrument_height: float = 0.001
    sigma_target_height: float = 0.001

    def __post_init__(self) -> None:
        _require_id(self.id, "instrument")
        for name, quantity, unit in (
            ("collimation", self.collimation, Unit.RADIAN),
            ("vertical_index", self.vertical_index, Unit.RADIAN),
            ("trunnion_tilt", self.trunnion_tilt, Unit.RADIAN),
            ("edm_additive", self.edm_additive, Unit.METRE),
            ("edm_scale", self.edm_scale, Unit.DIMENSIONLESS),
            ("cyclic_error_amplitude", self.cyclic_error_amplitude, Unit.METRE),
        ):
            _require_unit(quantity, unit, f"instrument.{name}")

        if self.cyclic_error_amplitude.value != 0.0 and self.cyclic_error_wavelength <= 0.0:
            raise ValidationError(
                "cyclic_error_without_wavelength",
                instrument=self.id,
                expected=(
                    "a positive cyclic_error_wavelength whenever an amplitude is given; "
                    "the correction is periodic in the distance and has no meaning without it"
                ),
            )
        for name, value in (
            ("sigma_direction", self.sigma_direction),
            ("sigma_zenith", self.sigma_zenith),
            ("sigma_zenith_refraction", self.sigma_zenith_refraction),
            ("sigma_instrument_height", self.sigma_instrument_height),
            ("sigma_target_height", self.sigma_target_height),
        ):
            if value < 0.0:
                raise ValidationError(
                    "instrument_sigma_negative",
                    instrument=self.id,
                    parameter=name,
                    received=value,
                    expected="a non-negative standard deviation",
                )

    @property
    def label(self) -> str:
        return self.name or self.id

    # -- stochastic model -------------------------------------------------

    def distance_sigma(self, distance: float) -> float:
        """Standard deviation of a slope distance, from the EDM specification."""
        return self.edm.sigma(distance)

    def zenith_sigma(self, distance: float = 0.0) -> float:
        """Standard deviation of a zenith angle, including the refraction term."""
        return self.sigma_zenith + self.sigma_zenith_refraction * abs(distance)

    def direction_quantity(self, value: float, *, sets: int = 1) -> Quantity:
        """A direction reading with the profile's nominal precision attached."""
        return Quantity.approximate(
            value,
            self.sigma_direction / (sets**0.5),
            Unit.RADIAN,
            Strategy.NOMINAL_PRECISION,
        )

    def zenith_quantity(self, value: float, distance: float = 0.0, *, sets: int = 1) -> Quantity:
        return Quantity.approximate(
            value,
            self.zenith_sigma(distance) / (sets**0.5),
            Unit.RADIAN,
            Strategy.NOMINAL_PRECISION,
        )

    def distance_quantity(self, value: float, *, sets: int = 1) -> Quantity:
        return Quantity.approximate(
            value,
            self.distance_sigma(value) / (sets**0.5),
            Unit.METRE,
            Strategy.NOMINAL_PRECISION,
        )

    def instrument_height_quantity(self, value: float) -> Quantity:
        return Quantity.from_std_dev(value, self.sigma_instrument_height, Unit.METRE)

    def target_height_quantity(self, value: float) -> Quantity:
        return Quantity.from_std_dev(value, self.sigma_target_height, Unit.METRE)

    # -- serialisation ----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "collimation": self.collimation.to_dict(),
            "vertical_index": self.vertical_index.to_dict(),
            "trunnion_tilt": self.trunnion_tilt.to_dict(),
            "edm_additive": self.edm_additive.to_dict(),
            "edm_scale": self.edm_scale.to_dict(),
            "cyclic_error_amplitude": self.cyclic_error_amplitude.to_dict(),
            "cyclic_error_wavelength": self.cyclic_error_wavelength,
            "applies_edm_constant": self.applies_edm_constant,
            "applies_atmospheric": self.applies_atmospheric,
            "atmospheric_model": self.atmospheric_model.name,
            "reference_refractive_index": self.reference_refractive_index,
            "edm": self.edm.to_dict(),
            "sigma_direction": self.sigma_direction,
            "sigma_zenith": self.sigma_zenith,
            "sigma_zenith_refraction": self.sigma_zenith_refraction,
            "sigma_instrument_height": self.sigma_instrument_height,
            "sigma_target_height": self.sigma_target_height,
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
    def from_dict(cls, payload: dict[str, Any]) -> InstrumentProfile:
        return cls(
            id=payload["id"],
            name=payload.get("name", ""),
            manufacturer=payload.get("manufacturer", ""),
            model=payload.get("model", ""),
            serial_number=payload.get("serial_number", ""),
            calibration_date=payload.get("calibration_date", ""),
            calibration_reference=payload.get("calibration_reference", ""),
            collimation=Quantity.from_dict(payload["collimation"]),
            vertical_index=Quantity.from_dict(payload["vertical_index"]),
            trunnion_tilt=Quantity.from_dict(payload["trunnion_tilt"]),
            edm_additive=Quantity.from_dict(payload["edm_additive"]),
            edm_scale=Quantity.from_dict(payload["edm_scale"]),
            cyclic_error_amplitude=Quantity.from_dict(payload["cyclic_error_amplitude"]),
            cyclic_error_wavelength=float(payload.get("cyclic_error_wavelength", 0.0)),
            applies_edm_constant=bool(payload.get("applies_edm_constant", False)),
            applies_atmospheric=bool(payload.get("applies_atmospheric", False)),
            atmospheric_model=AtmosphericModel[
                payload.get("atmospheric_model", AtmosphericModel.BARRELL_SEARS.name)
            ],
            reference_refractive_index=float(
                payload.get("reference_refractive_index", 1.0002830)
            ),
            edm=EdmSpecification.from_dict(payload["edm"]),
            sigma_direction=float(payload["sigma_direction"]),
            sigma_zenith=float(payload["sigma_zenith"]),
            sigma_zenith_refraction=float(payload.get("sigma_zenith_refraction", 0.0)),
            sigma_instrument_height=float(payload["sigma_instrument_height"]),
            sigma_target_height=float(payload["sigma_target_height"]),
        )


@dataclass
class ProfileLibrary:
    """The instrument and reflector profiles available to a project.

    Profiles export and import as files, so an organisation can distribute a
    calibrated instrument definition to its staff (``specs/15`` section 2.2).
    That is why this is a plain serialisable container rather than a wrapper
    over ``QgsSettings``: the same library is readable in a test, in a script
    and in the plugin.
    """

    instruments: dict[str, InstrumentProfile] = field(default_factory=dict)
    reflectors: dict[str, ReflectorProfile] = field(default_factory=dict)
    levels: dict[str, LevelProfile] = field(default_factory=dict)
    #: The accuracy classes lines are judged against (FR-503). In the library
    #: rather than in Global Settings because an organisation distributes its
    #: specification the same way it distributes a calibrated instrument, and a
    #: project routinely runs more than one class of levelling at once.
    levelling_classes: dict[str, LevellingClass] = field(default_factory=dict)
    #: Which profile is used when an observation names none.
    default_instrument: str = ""
    default_reflector: str = ""
    default_level: str = ""
    default_levelling_class: str = ""

    def add_instrument(self, profile: InstrumentProfile) -> None:
        if profile.id in self.instruments:
            raise ValidationError(
                "duplicate_instrument_profile",
                instrument=profile.id,
                expected="a unique profile id; rename or replace the existing one",
            )
        self.instruments[profile.id] = profile
        if not self.default_instrument:
            self.default_instrument = profile.id

    def add_reflector(self, profile: ReflectorProfile) -> None:
        if profile.id in self.reflectors:
            raise ValidationError(
                "duplicate_reflector_profile",
                reflector=profile.id,
                expected="a unique profile id; rename or replace the existing one",
            )
        self.reflectors[profile.id] = profile
        if not self.default_reflector:
            self.default_reflector = profile.id

    def instrument(self, instrument_id: str | None) -> InstrumentProfile:
        """Resolve an instrument reference, falling back to the default.

        Raises rather than inventing a profile: a fabricated instrument constant
        is a silent systematic error in every distance it touches.
        """
        wanted = instrument_id or self.default_instrument
        if not wanted:
            raise ValidationError(
                "no_instrument_profile",
                expected=(
                    "an instrument profile, either named on the observation or set as the "
                    "library default. GeoComp does not invent instrument constants"
                ),
            )
        try:
            return self.instruments[wanted]
        except KeyError:
            raise ValidationError(
                "unknown_instrument_profile",
                instrument=wanted,
                expected=f"one of: {', '.join(sorted(self.instruments)) or '(none defined)'}",
            ) from None

    def reflector(self, reflector_id: str | None) -> ReflectorProfile | None:
        """Resolve a reflector reference.

        Unlike an instrument, ``None`` is a legitimate answer: a reflectorless
        measurement has no prism and therefore no prism constant.
        """
        wanted = reflector_id or self.default_reflector
        if not wanted:
            return None
        try:
            return self.reflectors[wanted]
        except KeyError:
            raise ValidationError(
                "unknown_reflector_profile",
                reflector=wanted,
                expected=f"one of: {', '.join(sorted(self.reflectors)) or '(none defined)'}",
            ) from None

    # -- levels and levelling classes (phase P4) --------------------------

    def add_level(self, profile: LevelProfile) -> None:
        if profile.id in self.levels:
            raise ValidationError(
                "duplicate_level_profile",
                level=profile.id,
                expected="a unique profile id; rename or replace the existing one",
            )
        self.levels[profile.id] = profile
        if not self.default_level:
            self.default_level = profile.id

    def add_levelling_class(self, levelling_class: LevellingClass) -> None:
        if levelling_class.id in self.levelling_classes:
            raise ValidationError(
                "duplicate_levelling_class",
                levelling_class=levelling_class.id,
                expected="a unique class id; rename or replace the existing one",
            )
        self.levelling_classes[levelling_class.id] = levelling_class
        if not self.default_levelling_class:
            self.default_levelling_class = levelling_class.id

    def level(self, level_id: str | None) -> LevelProfile:
        """Resolve a level reference, falling back to the default.

        Raises rather than inventing a profile, for the same reason
        :meth:`instrument` does: the precision figures on this record become the
        weights of every height difference the instrument observed.
        """
        wanted = level_id or self.default_level
        if not wanted:
            raise ValidationError(
                "no_level_profile",
                expected=(
                    "a level profile, either named on the line or set as the library "
                    "default. GeoComp does not invent instrument precisions"
                ),
            )
        try:
            return self.levels[wanted]
        except KeyError:
            raise ValidationError(
                "unknown_level_profile",
                level=wanted,
                expected=f"one of: {', '.join(sorted(self.levels)) or '(none defined)'}",
            ) from None

    def levelling_class(self, class_id: str | None) -> LevellingClass | None:
        """Resolve an accuracy class.

        ``None`` is a legitimate answer, unlike for a level profile: a line
        observed under no stated specification still has a misclosure, and
        reporting it without a verdict is more useful than refusing to compute
        it (``specs/10`` section 3).
        """
        wanted = class_id or self.default_levelling_class
        if not wanted:
            return None
        try:
            return self.levelling_classes[wanted]
        except KeyError:
            raise ValidationError(
                "unknown_levelling_class",
                levelling_class=wanted,
                expected=(
                    f"one of: {', '.join(sorted(self.levelling_classes)) or '(none defined)'}"
                ),
            ) from None

    def replace_level(self, profile: LevelProfile) -> None:
        """Overwrite a level profile in place -- what a re-calibration produces."""
        self.levels[profile.id] = profile

    def replace_instrument(self, profile: InstrumentProfile) -> None:
        """Overwrite a profile in place -- what a re-calibration produces."""
        self.instruments[profile.id] = profile

    def rename_instrument(self, old_id: str, new_id: str) -> InstrumentProfile:
        profile = self.instrument(old_id)
        _require_id(new_id, "instrument")
        if new_id in self.instruments:
            raise ValidationError("duplicate_instrument_profile", instrument=new_id)
        del self.instruments[old_id]
        renamed = replace(profile, id=new_id)
        self.instruments[new_id] = renamed
        if self.default_instrument == old_id:
            self.default_instrument = new_id
        return renamed

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "instruments": [p.to_dict() for p in self.instruments.values()],
            "reflectors": [p.to_dict() for p in self.reflectors.values()],
            "levels": [p.to_dict() for p in self.levels.values()],
            "levelling_classes": [c.to_dict() for c in self.levelling_classes.values()],
        }
        for key, value in (
            ("default_instrument", self.default_instrument),
            ("default_reflector", self.default_reflector),
            ("default_level", self.default_level),
            ("default_levelling_class", self.default_levelling_class),
        ):
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ProfileLibrary:
        return cls(
            instruments={
                p["id"]: InstrumentProfile.from_dict(p) for p in payload.get("instruments", ())
            },
            reflectors={
                p["id"]: ReflectorProfile.from_dict(p) for p in payload.get("reflectors", ())
            },
            levels={p["id"]: LevelProfile.from_dict(p) for p in payload.get("levels", ())},
            levelling_classes={
                c["id"]: LevellingClass.from_dict(c)
                for c in payload.get("levelling_classes", ())
            },
            default_instrument=payload.get("default_instrument", ""),
            default_reflector=payload.get("default_reflector", ""),
            default_level=payload.get("default_level", ""),
            default_levelling_class=payload.get("default_levelling_class", ""),
        )


def _require_id(value: str, kind: str) -> None:
    if not value or not value.strip():
        raise ValidationError(
            f"{kind}_profile_without_id",
            expected="a non-empty id; observations reference profiles by it",
        )


def _require_unit(quantity: Quantity, unit: Unit, name: str) -> None:
    if quantity.unit is not unit:
        raise ValidationError(
            "profile_wrong_unit",
            parameter=name,
            received=quantity.unit.name,
            expected=unit.name,
        )
