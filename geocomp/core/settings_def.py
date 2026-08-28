# SPDX-License-Identifier: GPL-2.0-or-later
"""Declarative definitions of every GeoComp setting.

Specified in ``specs/15-ui-menu-and-settings.md`` section 2 (FR-060 to FR-069).

This module is pure data: it declares *what* settings exist, their types,
defaults, and which scopes may set them. It performs no resolution and touches
no storage -- ``geocomp.services.settings_service`` does that against
``QgsSettings`` and the project store.

Keeping the declarations here, outside the QGIS layer, buys three things: the
Global Settings window is generated rather than hand-built, so a new setting
cannot exist without a UI; the layered resolution (FR-068) is testable without
QGIS; and the section list is a single source shared by the dialog, the
resolver and the documentation.

Sections are ordered equipment-first, then cross-cutting, per the specified
dialog layout. P0 populates only the Interface section (FR-067); the equipment
sections are declared but filled by the phases that need them -- Total Station
and Stochastic model in P3, Reference systems in P5, Paths and engines in P6,
GNSS in P7, Gravimeter in P8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "SECTIONS",
    "SETTINGS",
    "Scope",
    "SectionDef",
    "SettingDef",
    "SettingType",
    "setting",
    "settings_in_section",
]


class Scope(Enum):
    """Where a setting value came from.

    Resolution order is ``RUN`` then ``PROJECT`` then ``GLOBAL`` then
    ``DEFAULT`` (FR-068). The order is the declaration order, and
    :meth:`precedence` depends on it.
    """

    RUN = "run"
    PROJECT = "project"
    GLOBAL = "global"
    DEFAULT = "default"

    @property
    def precedence(self) -> int:
        """Lower wins. ``RUN`` is 0; ``DEFAULT`` is last."""
        return list(Scope).index(self)


class SettingType(Enum):
    """The value type of a setting, which drives both the editor widget and validation."""

    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    CHOICE = "choice"
    PATH = "path"
    DIRECTORY = "directory"
    CRS = "crs"
    COLOR = "color"


@dataclass(frozen=True)
class SettingDef:
    """One configurable value.

    Attributes:
        key: Dotted identifier, ``section.name``. Stable across releases: it is
            the storage key in ``QgsSettings`` and in the project store, so
            renaming one needs a migration.
        section: Id of the :class:`SectionDef` it appears under.
        type: Value type.
        default: The built-in default, used when no scope supplies a value.
        scopes: Which scopes may set it. Everything may be set globally; a
            setting that must not vary per project omits ``Scope.PROJECT``.
        choices: Permitted values, for ``SettingType.CHOICE``.
        requirement: The requirement id this setting satisfies, so the
            traceability matrix can be checked mechanically.
        label_code / help_code: Translation keys. Never English text -- this
            module is inside the QGIS-free core and cannot phrase user-facing
            strings (NFR-002, FR-091).
    """

    key: str
    section: str
    type: SettingType
    default: Any
    requirement: str
    scopes: frozenset[Scope] = field(
        default_factory=lambda: frozenset({Scope.RUN, Scope.PROJECT, Scope.GLOBAL})
    )
    choices: tuple[str, ...] | None = None
    minimum: float | None = None
    maximum: float | None = None

    def __post_init__(self) -> None:
        if not self.key.startswith(f"{self.section}."):
            raise ValueError(f"setting key {self.key!r} must start with its section {self.section!r}")
        if self.type is SettingType.CHOICE:
            if not self.choices:
                raise ValueError(f"choice setting {self.key!r} declares no choices")
            if self.default not in self.choices:
                raise ValueError(f"default {self.default!r} of {self.key!r} is not among its choices")

    @property
    def label_code(self) -> str:
        """Translation key for this setting's label."""
        return f"setting.{self.key}.label"

    @property
    def help_code(self) -> str:
        """Translation key for this setting's help text."""
        return f"setting.{self.key}.help"

    def validate(self, value: Any) -> None:
        """Raise :class:`~geocomp.core.errors.ValidationError` if *value* is not acceptable."""
        from geocomp.core.errors import ValidationError

        if self.type is SettingType.CHOICE and value not in (self.choices or ()):
            raise ValidationError(
                "setting_not_a_choice", key=self.key, received=value, expected=list(self.choices or ())
            )
        if self.type in (SettingType.INT, SettingType.FLOAT):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValidationError(
                    "setting_wrong_type",
                    key=self.key,
                    received=type(value).__name__,
                    expected=self.type.value,
                )
            if self.minimum is not None and value < self.minimum:
                raise ValidationError(
                    "setting_below_minimum", key=self.key, received=value, minimum=self.minimum
                )
            if self.maximum is not None and value > self.maximum:
                raise ValidationError(
                    "setting_above_maximum", key=self.key, received=value, maximum=self.maximum
                )
        if self.type is SettingType.BOOL and not isinstance(value, bool):
            raise ValidationError(
                "setting_wrong_type", key=self.key, received=type(value).__name__, expected="bool"
            )


@dataclass(frozen=True)
class SectionDef:
    """One entry in the Global Settings side menu."""

    id: str
    order: int
    #: Equipment sections are listed first and separated from the cross-cutting
    #: ones, per the dialog layout in specs/15 section 2.
    is_equipment: bool
    requirement: str

    @property
    def label_code(self) -> str:
        return f"settings.section.{self.id}.label"


SECTIONS: tuple[SectionDef, ...] = (
    SectionDef("total_station", 10, True, "FR-061"),
    SectionDef("level", 20, True, "FR-061"),
    SectionDef("gnss", 30, True, "FR-063"),
    SectionDef("gravimeter", 40, True, "FR-061"),
    SectionDef("stochastic", 50, False, "FR-064"),
    SectionDef("reference_systems", 60, False, "FR-065"),
    SectionDef("paths", 70, False, "FR-066"),
    SectionDef("interface", 80, False, "FR-067"),
)

#: Values for ``interface.mode``. See specs/18 section 6.
MODE_BASIC = "basic"
MODE_ADVANCED = "advanced"

#: Values for ``interface.language``. ``system`` follows the QGIS UI language,
#: which is the default required by FR-092.
LANGUAGE_SYSTEM = "system"

#: Values for ``total_station.atmospheric_model``. Mirrors
#: :class:`~geocomp.core.instruments.profiles.AtmosphericModel`, as lower-case
#: strings because a setting value is stored text, not a Python enum.
ATMOSPHERIC_MODELS = ("barrell_sears", "leica", "trimble")

#: Values for ``total_station.traverse_adjustment``. Both are offered and clearly
#: distinguished: the classical rules are what students are taught and what many
#: specifications still require, and they are *not* least squares (specs/09 §4.1).
TRAVERSE_COMPASS = "compass"
TRAVERSE_TRANSIT = "transit"
TRAVERSE_LEAST_SQUARES = "least_squares"

#: Values for ``level.weighting`` (FR-504). Length weighting suits long lines
#: with consistent sight lengths; setup weighting suits short, irregular ones
#: where the per-setup reading error dominates. Neither is derivable from the
#: other, which is why specs/10 section 4 offers both rather than picking one.
WEIGHTING_LENGTH = "length"
WEIGHTING_SETUPS = "setups"

SETTINGS: tuple[SettingDef, ...] = (
    # -- Total Station (FR-061, FR-062). Added in phase P3. -------------------
    #
    # Instrument and reflector *profiles* are not settings: they are named,
    # structured records with their own uncertainties, so they live in
    # geocomp.core.instruments and are stored as documents (specs/15 §2.2).
    # What is here is the configuration that is genuinely a single value.
    SettingDef(
        key="total_station.atmospheric_model",
        section="total_station",
        type=SettingType.CHOICE,
        default="barrell_sears",
        choices=ATMOSPHERIC_MODELS,
        requirement="FR-062",
    ),
    SettingDef(
        key="total_station.default_temperature_celsius",
        section="total_station",
        type=SettingType.FLOAT,
        default=20.0,
        minimum=-90.0,
        maximum=60.0,
        requirement="FR-062",
    ),
    SettingDef(
        key="total_station.default_pressure_hpa",
        section="total_station",
        type=SettingType.FLOAT,
        default=1013.25,
        minimum=100.0,
        maximum=1100.0,
        requirement="FR-062",
    ),
    SettingDef(
        key="total_station.default_humidity_percent",
        section="total_station",
        type=SettingType.FLOAT,
        default=60.0,
        minimum=0.0,
        maximum=100.0,
        requirement="FR-062",
    ),
    # The uncertainty of the defaults, not just the defaults. A temperature
    # nobody measured is not known to the same precision as one somebody read
    # off a thermometer, and FR-204 requires that difference to propagate.
    SettingDef(
        key="total_station.default_temperature_sigma",
        section="total_station",
        type=SettingType.FLOAT,
        default=5.0,
        minimum=0.0,
        maximum=50.0,
        requirement="FR-204",
    ),
    SettingDef(
        key="total_station.default_pressure_sigma_hpa",
        section="total_station",
        type=SettingType.FLOAT,
        default=10.0,
        minimum=0.0,
        maximum=200.0,
        requirement="FR-204",
    ),
    SettingDef(
        key="total_station.refraction_coefficient",
        section="total_station",
        type=SettingType.FLOAT,
        default=0.13,
        minimum=-1.0,
        maximum=1.0,
        requirement="FR-405",
    ),
    # k is poorly known and varies through the day; its uncertainty is the
    # dominant error source on long trigonometric heights (specs/09 §2.6), so
    # it is configurable rather than assumed exact.
    SettingDef(
        key="total_station.refraction_coefficient_sigma",
        section="total_station",
        type=SettingType.FLOAT,
        default=0.05,
        minimum=0.0,
        maximum=1.0,
        requirement="FR-405",
    ),
    SettingDef(
        key="total_station.face_distance_tolerance",
        section="total_station",
        type=SettingType.FLOAT,
        default=0.005,
        minimum=0.0,
        maximum=10.0,
        requirement="FR-400",
    ),
    SettingDef(
        key="total_station.collimation_tolerance",
        section="total_station",
        type=SettingType.FLOAT,
        default=1.0e-4,
        minimum=0.0,
        maximum=0.1,
        requirement="FR-400",
    ),
    SettingDef(
        key="total_station.traverse_adjustment",
        section="total_station",
        type=SettingType.CHOICE,
        default=TRAVERSE_LEAST_SQUARES,
        choices=(TRAVERSE_LEAST_SQUARES, TRAVERSE_COMPASS, TRAVERSE_TRANSIT),
        requirement="FR-406",
    ),
    SettingDef(
        key="total_station.traverse_relative_precision",
        section="total_station",
        type=SettingType.INT,
        default=5000,
        minimum=100,
        maximum=1000000,
        requirement="FR-406",
    ),
    SettingDef(
        key="total_station.traverse_angular_tolerance_per_station",
        section="total_station",
        type=SettingType.FLOAT,
        default=1.45e-4,
        minimum=0.0,
        maximum=0.1,
        requirement="FR-406",
    ),
    # -- Level (FR-061, FR-503, FR-504). Added in phase P4. -------------------
    #
    # Level profiles and levelling accuracy classes are not settings, for the
    # same reason instrument profiles are not: they are named, structured
    # records with their own uncertainties and their own provenance, so they
    # live in geocomp.core.instruments.level. What is here is the configuration
    # that is genuinely one value.
    SettingDef(
        key="level.weighting",
        section="level",
        type=SettingType.CHOICE,
        default=WEIGHTING_LENGTH,
        choices=(WEIGHTING_LENGTH, WEIGHTING_SETUPS),
        requirement="FR-504",
    ),
    # Zero means "no tolerance configured", and a closure check then reports the
    # misclosure with no verdict. Deliberate: k differs by country, by class
    # within a country and by edition of the standard, and a default that is
    # wrong does not fail loudly -- it silently accepts a line that should have
    # been re-run. specs/10 section 3.
    SettingDef(
        key="level.tolerance_coefficient",
        section="level",
        type=SettingType.FLOAT,
        default=0.0,
        minimum=0.0,
        maximum=1.0,
        requirement="FR-503",
    ),
    SettingDef(
        key="level.max_sight_length",
        section="level",
        type=SettingType.FLOAT,
        default=0.0,
        minimum=0.0,
        maximum=500.0,
        requirement="FR-500",
    ),
    SettingDef(
        key="level.max_sight_imbalance",
        section="level",
        type=SettingType.FLOAT,
        default=0.0,
        minimum=0.0,
        maximum=100.0,
        requirement="FR-500",
    ),
    # The one that actually matters. Per-setup imbalances of alternating sign
    # cost nothing; it is their *sum* that drives the residual collimation
    # error over a line (specs/10 section 2.1).
    SettingDef(
        key="level.max_accumulated_imbalance",
        section="level",
        type=SettingType.FLOAT,
        default=0.0,
        minimum=0.0,
        maximum=1000.0,
        requirement="FR-500",
    ),
    # Refraction across water varies rapidly and asymmetrically, so the
    # equidistant-sights model is deliberately more conservative than the
    # equal-sights one and says so in its output (specs/10 section 2.2). The
    # factor is configurable because its right value depends on the crossing,
    # and one is nothing to defend.
    SettingDef(
        key="level.reciprocal_variance_inflation",
        section="level",
        type=SettingType.FLOAT,
        default=2.0,
        minimum=1.0,
        maximum=100.0,
        requirement="FR-501",
    ),
    SettingDef(
        key="level.apply_orthometric_correction",
        section="level",
        type=SettingType.BOOL,
        default=False,
        requirement="FR-504",
    ),
    # The explicit acknowledgement specs/10 section 3 requires: GeoComp does not
    # adjust a line that failed its tolerance until someone says to.
    SettingDef(
        key="level.adjust_failing_lines",
        section="level",
        type=SettingType.BOOL,
        default=False,
        requirement="FR-503",
    ),
    # -- Stochastic model (FR-064). Added in phase P3. ------------------------
    #
    # Deliberately zero by default, meaning "no type default configured": step 3
    # of the specs/05 §5 precedence then supplies nothing and the resolution
    # refuses rather than inventing a weight. A fresh installation should refuse.
    SettingDef(
        key="stochastic.default_sigma_direction",
        section="stochastic",
        type=SettingType.FLOAT,
        default=0.0,
        minimum=0.0,
        maximum=0.1,
        requirement="FR-064",
    ),
    SettingDef(
        key="stochastic.default_sigma_zenith_angle",
        section="stochastic",
        type=SettingType.FLOAT,
        default=0.0,
        minimum=0.0,
        maximum=0.1,
        requirement="FR-064",
    ),
    SettingDef(
        key="stochastic.default_sigma_slope_distance",
        section="stochastic",
        type=SettingType.FLOAT,
        default=0.0,
        minimum=0.0,
        maximum=100.0,
        requirement="FR-064",
    ),
    SettingDef(
        key="stochastic.default_sigma_height_difference",
        section="stochastic",
        type=SettingType.FLOAT,
        default=0.0,
        minimum=0.0,
        maximum=100.0,
        requirement="FR-064",
    ),
    SettingDef(
        key="stochastic.outlier_alpha",
        section="stochastic",
        type=SettingType.FLOAT,
        default=0.001,
        minimum=1e-6,
        maximum=0.5,
        requirement="FR-064",
    ),
    SettingDef(
        key="stochastic.outlier_beta",
        section="stochastic",
        type=SettingType.FLOAT,
        default=0.20,
        minimum=1e-6,
        maximum=0.9,
        requirement="FR-064",
    ),
    SettingDef(
        key="stochastic.confidence_level",
        section="stochastic",
        type=SettingType.FLOAT,
        default=0.95,
        minimum=0.5,
        maximum=0.9999,
        requirement="FR-064",
    ),
    # -- Interface (FR-067). The only section populated in phase P0. ----------
    SettingDef(
        key="interface.language",
        section="interface",
        type=SettingType.CHOICE,
        default=LANGUAGE_SYSTEM,
        choices=(LANGUAGE_SYSTEM, "en", "pt_BR", "es"),
        requirement="FR-067",
        scopes=frozenset({Scope.GLOBAL}),
    ),
    SettingDef(
        key="interface.mode",
        section="interface",
        type=SettingType.CHOICE,
        default=MODE_BASIC,
        choices=(MODE_BASIC, MODE_ADVANCED),
        requirement="FR-070",
        scopes=frozenset({Scope.RUN, Scope.PROJECT, Scope.GLOBAL}),
    ),
    SettingDef(
        key="interface.distance_unit",
        section="interface",
        type=SettingType.CHOICE,
        default="metre",
        choices=("metre", "foot", "us_survey_foot"),
        requirement="FR-067",
    ),
    SettingDef(
        key="interface.angle_format",
        section="interface",
        type=SettingType.CHOICE,
        default="dms",
        choices=("dms", "decimal_degrees", "gon", "radian"),
        requirement="FR-067",
    ),
    SettingDef(
        key="interface.coordinate_decimals",
        section="interface",
        type=SettingType.INT,
        default=4,
        minimum=0,
        maximum=9,
        requirement="FR-067",
    ),
    SettingDef(
        key="interface.angle_decimals",
        section="interface",
        type=SettingType.INT,
        default=1,
        minimum=0,
        maximum=6,
        requirement="FR-067",
    ),
    SettingDef(
        key="interface.log_level",
        section="interface",
        type=SettingType.CHOICE,
        default="info",
        choices=("debug", "info", "warning", "critical"),
        requirement="FR-009",
        scopes=frozenset({Scope.GLOBAL}),
    ),
    SettingDef(
        key="interface.show_toolbar",
        section="interface",
        type=SettingType.BOOL,
        default=True,
        requirement="FR-007",
        scopes=frozenset({Scope.GLOBAL}),
    ),
)

_BY_KEY = {definition.key: definition for definition in SETTINGS}
_SECTION_IDS = {section.id for section in SECTIONS}


def setting(key: str) -> SettingDef:
    """Return the definition for *key*.

    Raises:
        KeyError: if no such setting is declared. Deliberately not a
            ``GeoCompError``: an unknown settings key is a programming mistake,
            not a condition to report to a user.
    """
    return _BY_KEY[key]


def settings_in_section(section_id: str) -> tuple[SettingDef, ...]:
    """Return the settings declared under *section_id*, in declaration order."""
    return tuple(definition for definition in SETTINGS if definition.section == section_id)


def _validate_module() -> None:
    """Consistency checks that would otherwise become runtime surprises."""
    for definition in SETTINGS:
        if definition.section not in _SECTION_IDS:
            raise ValueError(f"setting {definition.key!r} names unknown section {definition.section!r}")
        if not definition.scopes:
            raise ValueError(f"setting {definition.key!r} declares no scopes")
        if Scope.DEFAULT in definition.scopes:
            raise ValueError(f"setting {definition.key!r} may not declare DEFAULT as a settable scope")
    if len(_BY_KEY) != len(SETTINGS):
        raise ValueError("duplicate setting key declared")
    if len({section.id for section in SECTIONS}) != len(SECTIONS):
        raise ValueError("duplicate section id declared")


_validate_module()
