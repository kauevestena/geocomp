# SPDX-License-Identifier: GPL-2.0-or-later
"""Instrument profiles, edited as named profiles (FR-061, FR-069; specs/15 §2.2).

A department owns several total stations, levels and gravimeters, and their
constants are named profiles rather than one set of values. Until P12c-16 a
profile was edited only as a JSON document. This module is everything the
profile window does that is not drawing a window, so all of it is tested without
QGIS:

* **what can be edited, and in which unit** (:data:`FIELDS`). A surveyor reads an
  index error in seconds of arc (or cc, or µrad, as the interface is set), a
  prism constant in millimetres, an EDM's proportional term in ppm. The profile
  stores radians, metres and plain ratios. Each field says which it is, and
  :func:`shown` and :func:`edited` convert both ways;
* **what is done to a library**: add, duplicate, delete, choose the default,
  import another library's profiles and export some of this one's.

Every edit is applied to the profile's own serialised form and read back through
its ``from_dict``, so a value the profile refuses (a negative standard deviation,
a counter-reading gravimeter without its table) is refused here with the
profile's own words, and nothing that could not be saved can be built.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.instruments.gravimeter import GravimeterProfile, ReadingUnit
from geocomp.core.instruments.level import LevellingClass, LevelProfile
from geocomp.core.instruments.profiles import (
    AtmosphericModel,
    InstrumentProfile,
    ProfileLibrary,
    ReflectorProfile,
)

__all__ = [
    "FIELDS",
    "KINDS",
    "Field",
    "Kind",
    "add_profile",
    "duplicate_profile",
    "edited",
    "export_profiles",
    "import_profiles",
    "remove_profile",
    "set_default",
    "shown",
]


@dataclass(frozen=True)
class Kind:
    """One kind of profile a library holds.

    Attributes:
        key: The library attribute holding them, and the kind's name here.
        profile: The profile class.
        default: The library attribute naming the default one.
    """

    key: str
    profile: type
    default: str


#: The kinds, in the order the window shows them.
KINDS: tuple[Kind, ...] = (
    Kind("instruments", InstrumentProfile, "default_instrument"),
    Kind("reflectors", ReflectorProfile, "default_reflector"),
    Kind("levels", LevelProfile, "default_level"),
    Kind("levelling_classes", LevellingClass, "default_levelling_class"),
    Kind("gravimeters", GravimeterProfile, "default_gravimeter"),
)

_KINDS = {kind.key: kind for kind in KINDS}


@dataclass(frozen=True)
class Field:
    """One editable value of a profile.

    Attributes:
        path: Where it is in the profile's serialised form, ``("edm",
            "constant")`` for a nested one.
        editor: ``text``, ``flag``, ``number``, ``quantity`` (a value and its
            standard deviation) or ``choice``.
        unit: How it is shown: ``angle`` (the interface's small-angle unit),
            ``angle_per_km``, ``mm``, ``mm_per_root_km``, ``ppm``,
            ``ppm_offset`` (a scale shown as its departure from one), ``ugal``,
            ``m`` or ``""`` for a plain number.
        choices: The stored values a ``choice`` can take.
    """

    path: tuple[str, ...]
    editor: str
    unit: str = ""
    choices: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        """A stable name for the field, for labels and for tests."""
        return ".".join(self.path)


def _text(*names: str) -> tuple[Field, ...]:
    return tuple(Field((name,), "text") for name in names)


#: Every editable field of every kind. The id is not among them: a profile is
#: renamed by duplicating it, because observations reference it by id.
FIELDS: dict[str, tuple[Field, ...]] = {
    "instruments": (
        *_text("name", "manufacturer", "model", "serial_number", "calibration_date", "calibration_reference"),
        Field(("collimation",), "quantity", "angle"),
        Field(("vertical_index",), "quantity", "angle"),
        Field(("trunnion_tilt",), "quantity", "angle"),
        Field(("edm_additive",), "quantity", "mm"),
        Field(("edm_scale",), "quantity", "ppm_offset"),
        Field(("cyclic_error_amplitude",), "quantity", "mm"),
        Field(("cyclic_error_wavelength",), "number", "m"),
        Field(("applies_edm_constant",), "flag"),
        Field(("applies_atmospheric",), "flag"),
        Field(
            ("atmospheric_model",),
            "choice",
            choices=tuple(model.name for model in AtmosphericModel),
        ),
        Field(("reference_refractive_index",), "number"),
        Field(("edm", "constant"), "number", "mm"),
        Field(("edm", "proportional"), "number", "ppm"),
        Field(("edm", "scale"), "number"),
        Field(("sigma_direction",), "number", "angle"),
        Field(("sigma_zenith",), "number", "angle"),
        Field(("sigma_zenith_refraction",), "number", "angle_per_km"),
        Field(("sigma_instrument_height",), "number", "mm"),
        Field(("sigma_target_height",), "number", "mm"),
    ),
    "reflectors": (
        *_text("name", "manufacturer", "model", "calibration_date", "calibration_reference"),
        Field(("additive_constant",), "quantity", "mm"),
        Field(("applies_internally",), "flag"),
    ),
    "levels": (
        *_text("name", "manufacturer", "model", "serial_number", "calibration_date", "calibration_reference"),
        Field(("collimation",), "quantity", "angle"),
        Field(("applies_collimation",), "flag"),
        Field(("sigma_per_km",), "number", "mm_per_root_km"),
        Field(("sigma_per_setup",), "number", "mm"),
        Field(("sigma_reading",), "number", "mm"),
        Field(("stadia_factor",), "number"),
        Field(("sigma_stadia_reading",), "number", "mm"),
    ),
    "levelling_classes": (
        *_text("name", "source"),
        Field(("tolerance_coefficient",), "number", "mm_per_root_km"),
        Field(("max_sight_length",), "number", "m"),
        Field(("max_sight_imbalance",), "number", "m"),
        Field(("max_accumulated_imbalance",), "number", "m"),
    ),
    "gravimeters": (
        *_text("name", "model", "serial", "source"),
        Field(("reading_unit",), "choice", choices=tuple(unit.value for unit in ReadingUnit)),
        Field(("calibration_factor",), "quantity"),
        Field(("sigma_reading",), "number", "ugal"),
        Field(("applies_tide",), "flag"),
    ),
}

#: Stored value times this is the shown value. Angles depend on the interface
#: and are passed in.
_FACTORS = {
    "": 1.0,
    "m": 1.0,
    "mm": 1.0e3,
    "mm_per_root_km": 1.0e3,
    "ppm": 1.0e6,
    "ppm_offset": 1.0e6,
    "ugal": 1.0e8,
}


def _factor(unit: str, small_angle: float) -> float:
    if unit == "angle":
        return small_angle
    if unit == "angle_per_km":
        return small_angle * 1.0e3
    return _FACTORS[unit]


def _get(payload: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = payload
    for name in path:
        value = value.get(name) if isinstance(value, dict) else None
    return value


def _set(payload: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    for name in path[:-1]:
        payload = payload.setdefault(name, {})
    payload[path[-1]] = value


def shown(payload: dict[str, Any], field: Field, *, small_angle: float) -> Any:
    """The field's value as the window shows it.

    Text, a flag or a choice as stored; a number in its unit; a quantity as
    ``(value, standard deviation)`` in its unit. *small_angle* is the number of
    the interface's small-angle units in a radian.
    """
    stored = _get(payload, field.path)
    if field.editor == "text":
        return stored or ""
    if field.editor == "flag":
        return bool(stored)
    if field.editor == "choice":
        return stored if stored is not None else field.choices[0]
    factor = _factor(field.unit, small_angle)
    offset = 1.0 if field.unit == "ppm_offset" else 0.0
    if field.editor == "number":
        return (float(stored or 0.0) - offset) * factor
    value = float(stored["value"]) if stored else offset
    variance = float(stored["variance"]) if stored else 0.0
    return (value - offset) * factor, math.sqrt(variance) * factor


def edited(
    kind: str, payload: dict[str, Any], values: dict[str, Any], *, small_angle: float
) -> Any:
    """The profile with *values* (by :attr:`Field.key`, as :func:`shown` gives
    them) written into it, read back through its own ``from_dict``.

    Raises:
        ValidationError: Whatever the profile refuses, in its own words, and
            ``profile_value_not_a_number`` for a number that is not one.
    """
    fields = {field.key: field for field in FIELDS[kind]}
    result = copy.deepcopy(payload)
    for key, value in values.items():
        field = fields[key]
        if field.editor in ("text", "choice"):
            _set(result, field.path, str(value).strip())
            continue
        if field.editor == "flag":
            _set(result, field.path, bool(value))
            continue
        factor = _factor(field.unit, small_angle)
        offset = 1.0 if field.unit == "ppm_offset" else 0.0
        try:
            if field.editor == "number":
                _set(result, field.path, _number(value) / factor + offset)
                continue
            number, sigma = (_number(part) for part in value)
        except (TypeError, ValueError) as error:
            raise ValidationError(
                "profile_value_not_a_number", parameter=key, received=str(value)
            ) from error
        quantity = dict(_get(result, field.path) or {"unit": _UNITS.get(kind, {}).get(key, "DIMENSIONLESS")})
        quantity.setdefault("mode", "RIGOROUS")
        quantity["value"] = number / factor + offset
        quantity["variance"] = (sigma / factor) ** 2
        _set(result, field.path, quantity)
    # Optional text fields are left out when empty, as the profiles write them.
    for field in FIELDS[kind]:
        if field.editor == "text" and _get(result, field.path) == "":
            del result[field.path[0]]
    return _KINDS[kind].profile.from_dict(result)


def _number(value: Any) -> float:
    """A number typed with a decimal point or a decimal comma (FR-094)."""
    if isinstance(value, str):
        return float(value.strip().replace(",", "."))
    return float(value)


#: The unit of a quantity a payload might not have yet.
_UNITS = {
    "gravimeters": {"calibration_factor": "DIMENSIONLESS"},
}


# -- the library ------------------------------------------------------------


def _profiles(library: ProfileLibrary, kind: str) -> dict[str, Any]:
    return getattr(library, _KINDS[kind].key)


def add_profile(library: ProfileLibrary, kind: str, profile_id: str) -> Any:
    """A new profile of *kind* with the class's defaults, added under *profile_id*.

    Raises:
        ValidationError: ``duplicate_profile`` when the id is taken, and what
            the profile class says of an empty id.
    """
    profiles = _profiles(library, kind)
    if profile_id in profiles:
        raise ValidationError("duplicate_profile", received=profile_id)
    profile = _blank(kind, profile_id)
    _place(library, kind, profile)
    return profile


def _blank(kind: str, profile_id: str) -> Any:
    return _KINDS[kind].profile(id=profile_id.strip())


def _place(library: ProfileLibrary, kind: str, profile: Any) -> None:
    """Put *profile* in the library; where its kind has no default, it becomes it.

    The library's own ``add_instrument`` and its siblings do the same. A library
    built in the window without it had profiles and no default, and every run
    that named no instrument refused it.
    """
    _profiles(library, kind)[profile.id] = profile
    attribute = _KINDS[kind].default
    if not getattr(library, attribute):
        setattr(library, attribute, profile.id)


def duplicate_profile(library: ProfileLibrary, kind: str, source_id: str, new_id: str) -> Any:
    """A copy of *source_id* under *new_id*: how a profile is renamed, and how a
    second instrument of the same model starts."""
    profiles = _profiles(library, kind)
    if new_id in profiles:
        raise ValidationError("duplicate_profile", received=new_id)
    payload = profiles[source_id].to_dict()
    payload["id"] = new_id.strip()
    profile = _KINDS[kind].profile.from_dict(payload)
    _place(library, kind, profile)
    return profile


def remove_profile(library: ProfileLibrary, kind: str, profile_id: str) -> None:
    """Delete a profile; a default that named it names nothing."""
    del _profiles(library, kind)[profile_id]
    attribute = _KINDS[kind].default
    if getattr(library, attribute) == profile_id:
        setattr(library, attribute, "")


def set_default(library: ProfileLibrary, kind: str, profile_id: str) -> None:
    """Make *profile_id* the one used when an observation names none."""
    if profile_id and profile_id not in _profiles(library, kind):
        raise ValidationError("unknown_profile", received=profile_id)
    setattr(library, _KINDS[kind].default, profile_id)


def import_profiles(library: ProfileLibrary, other: ProfileLibrary) -> tuple[list[str], list[str]]:
    """Add *other*'s profiles to *library*, every kind.

    A profile whose id is already in the library is **not** replaced: a
    calibration someone distributed does not silently overwrite the one in use.
    It is listed instead, so the window can say which were left. Where this
    library has no default of a kind, the other's default comes with it.

    Returns:
        The ids added and the ids left, each as ``kind/id``.
    """
    added: list[str] = []
    kept: list[str] = []
    for kind in KINDS:
        mine, theirs = _profiles(library, kind.key), _profiles(other, kind.key)
        had_default = bool(getattr(library, kind.default))
        for profile_id, profile in theirs.items():
            if profile_id in mine:
                kept.append(f"{kind.key}/{profile_id}")
            else:
                _place(library, kind.key, profile)
                added.append(f"{kind.key}/{profile_id}")
        their_default = getattr(other, kind.default)
        if not had_default and f"{kind.key}/{their_default}" in added:
            setattr(library, kind.default, their_default)
    return added, kept


def export_profiles(library: ProfileLibrary, chosen: dict[str, list[str]]) -> ProfileLibrary:
    """A library of only the *chosen* profiles, by kind, to give to someone else.

    A default travels with it when the profile it names does.
    """
    exported = ProfileLibrary()
    for kind in KINDS:
        wanted = chosen.get(kind.key, [])
        profiles = _profiles(library, kind.key)
        _profiles(exported, kind.key).update({pid: profiles[pid] for pid in wanted})
        default = getattr(library, kind.default)
        if default in wanted:
            setattr(exported, kind.default, default)
    return exported
