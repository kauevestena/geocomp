# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared plumbing for the gravimetry algorithms (phase P8b).

The same needs the levelling and GNSS packages have -- settings to resolve, a
document to read and write, one way of phrasing errors -- plus the two gravity
adds: a **display unit**, and a **profile for every instrument** a file names.

**Every default here comes from the settings service**, never from a literal,
for the reason ``specs/15`` section 2.3 records: a setting the Global Settings
window offers and nothing reads is worse than no setting.

**Stored in SI, shown in mGal or µGal** (``specs/12`` section 3). Documents,
solutions and layer values that feed a computation are m/s^2; the display unit
applies to what a person reads -- report tables, the corrections CSV, the
layers' gravity columns, which name their unit.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from qgis.core import QgsProcessingException
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.errors import GeoCompError
from geocomp.core.instruments import ProfileLibrary
from geocomp.core.instruments.gravimeter import GravimeterProfile
from geocomp.core.techniques.gravimetry import (
    GravityReading,
    ReducedReading,
    TideModel,
)
from geocomp.core.uncertainty import Quantity, Strategy, UncertaintyMode
from geocomp.core.units import (
    METRES_PER_SECOND_SQUARED_PER_MGAL,
    METRES_PER_SECOND_SQUARED_PER_UGAL,
    Unit,
)

__all__ = [
    "DOCUMENT_FORMAT",
    "DOCUMENT_VERSION",
    "assumed_profile",
    "display_decimals",
    "display_unit",
    "gravimeter_library",
    "gravimeter_setting",
    "gravity_label",
    "read_readings_document",
    "tide_model_from",
    "to_display",
    "translate_error",
    "unit_symbol",
    "with_sensor_height",
    "write_readings_document",
]

# The settings this package reads, written out in full so that
# `tests/structural/test_settings_are_honoured.py` finds each one, and so a
# typo is a NameError here rather than a silent miss at run time.
TIDE_MODEL_KEY = "gravimeter.tide_model"
TIDE_AMPLIFICATION_KEY = "gravimeter.tide_amplification"
DRIFT_MODE_KEY = "gravimeter.drift_mode"
DRIFT_DEGREE_KEY = "gravimeter.drift_degree"
PRECISION_FLOOR_KEY = "gravimeter.precision_floor"
DISPLAY_UNIT_KEY = "gravimeter.display_unit"

#: What *Pre-processing* writes and *Gravimetric network adjustment* reads.
DOCUMENT_FORMAT = "geocomp.gravity_readings"
DOCUMENT_VERSION = 1

_CONTEXT = "GeoCompGravimetry"

_PER_UNIT = {
    "mgal": METRES_PER_SECOND_SQUARED_PER_MGAL,
    "ugal": METRES_PER_SECOND_SQUARED_PER_UGAL,
}
# The same resolution in either unit: a tenth of a microgal, which is below
# every gravimeter's precision and above the rounding of a printed reading.
_DECIMALS = {"mgal": 4, "ugal": 1}


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def gravimeter_setting(key: str) -> Any:
    """Resolve a full setting key through the run/project/global scopes (FR-068)."""
    from geocomp.services.settings_service import settings

    return settings.value(key)


# -- display ----------------------------------------------------------------


def display_unit() -> str:
    """``"mgal"`` or ``"ugal"``, as the Gravimeter settings say (FR-067)."""
    unit = gravimeter_setting(DISPLAY_UNIT_KEY)
    return unit if unit in _PER_UNIT else "mgal"


def unit_symbol(unit: str) -> str:
    """The symbol, which is the same in every language and is not translated."""
    return {"mgal": "mGal", "ugal": "µGal"}[unit]


def to_display(value: float, unit: str) -> float:
    """An acceleration in m/s^2, in the display unit. Display only: never stored."""
    return value / _PER_UNIT[unit]


def display_decimals(unit: str) -> int:
    return _DECIMALS[unit]


def gravity_label(text: str, unit: str) -> str:
    """A column or table heading with its unit, e.g. ``Gravity (mGal)``."""
    return f"{text} ({unit_symbol(unit)})"


# -- settings to options ------------------------------------------------------


def tide_model_from(value: str) -> TideModel | None:
    """The settings value to the model, ``None`` for "none"."""
    return None if value == "none" else TideModel(value)


# -- profiles -----------------------------------------------------------------


def assumed_profile(instrument: str, floor: float) -> GravimeterProfile:
    """A profile for an instrument the user configured none for.

    The instrument's own scale is used -- a CG-5 or a Burris already reads in
    mGal on its factory calibration -- so the factor is one. **It is not exact**:
    no calibration was supplied, so its value is an assumption, and the factor
    says so (``MODEL_ASSUMED``). That label reaches every difference the
    instrument contributes and so the solution's ``uncertainty_mode``, which is
    the point (FR-203): a network with no calibration behind it does not get to
    call itself rigorous. Its uncertainty cannot be stated, so none is
    propagated, and the pre-processing notes say that too.
    """
    return GravimeterProfile(
        id=instrument,
        name=instrument,
        calibration_factor=Quantity(
            value=1.0,
            variance=0.0,
            unit=Unit.DIMENSIONLESS,
            mode=UncertaintyMode.APPROXIMATE,
            strategies=frozenset({Strategy.MODEL_ASSUMED}),
        ),
        sigma_reading=floor,
        source=_tr("assumed: no gravimeter profile was given"),
    )


def gravimeter_library(
    path: str, instruments: tuple[str, ...], floor: float, notes: list[str]
) -> ProfileLibrary:
    """The profiles to reduce with: the given library, or one assumed per instrument.

    A library that lacks an instrument the file names is refused rather than
    completed with an assumed profile: a user who wrote a library meant its
    calibrations to be used, and silently using none for one instrument would
    hide exactly the mistake they would want to hear about.
    """
    if not path:
        library = ProfileLibrary()
        for instrument in instruments:
            library.add_gravimeter(assumed_profile(instrument, floor))
        notes.append(
            _tr(
                "No gravimeter profile was given, so each instrument's own scale was used "
                "with a calibration factor of one whose uncertainty is unknown and not "
                "propagated. The result is labelled approximate for it. Give a profile "
                "library with each instrument's calibration to remove the assumption."
            )
        )
        return library

    from geocomp.algorithms.levelling.common import load_json

    try:
        library = ProfileLibrary.from_dict(load_json(path, parameter="PROFILES"))
    except GeoCompError as exc:
        raise QgsProcessingException(translate_error(exc)) from exc
    except (KeyError, TypeError, ValueError) as exc:
        # A library written by hand, missing a field: say which, rather than
        # let a bare KeyError reach the log as a traceback.
        raise QgsProcessingException(
            _tr("'%1' could not be read as a gravimeter profile library: %2 is missing or invalid.")
            .replace("%1", path)
            .replace("%2", str(exc))
        ) from exc
    try:
        for instrument in instruments:
            library.gravimeter(instrument)
    except GeoCompError as exc:
        raise QgsProcessingException(translate_error(exc)) from exc
    return library


def with_sensor_height(
    readings: tuple[GravityReading, ...], height: float | None, sigma: float
) -> list[GravityReading]:
    """Give every reading that carries no sensor height the run's.

    A reading that brought its own -- a CSV row with ``sensor_height_m`` -- keeps
    it: a height measured at that setup is better evidence than one typed for the
    whole file.
    """
    if height is None:
        return list(readings)
    quantity = (
        Quantity.from_std_dev(height, sigma, Unit.METRE)
        if sigma > 0.0
        else Quantity.exact(height, Unit.METRE)
    )
    return [
        reading if reading.sensor_height is not None else replace(reading, sensor_height=quantity)
        for reading in readings
    ]


# -- the readings document ------------------------------------------------------


def write_readings_document(
    path: str,
    *,
    reduced: list[ReducedReading],
    library: ProfileLibrary,
    source: str,
    file_format: str,
    reduction: dict[str, Any],
    notes: list[str],
) -> None:
    """Write what *Pre-processing* produced, for the network to read.

    It carries the profiles the readings were reduced with, so the network
    propagates the same calibration the reduction applied -- not whatever the
    library file on disk says by the time the network is run.
    """
    from geocomp.algorithms.levelling.common import write_document

    write_document(
        path,
        {
            "format": DOCUMENT_FORMAT,
            "version": DOCUMENT_VERSION,
            "source": source,
            "file_format": file_format,
            "reduction": reduction,
            "profiles": library.to_dict(),
            "notes": list(notes),
            "readings": [item.to_dict() for item in reduced],
        },
    )


def read_readings_document(
    path: str, *, parameter: str = "READINGS"
) -> tuple[list[ReducedReading], ProfileLibrary, dict[str, Any]]:
    """Read a document *Pre-processing* wrote: readings, profiles, and the rest."""
    from geocomp.algorithms.levelling.common import load_json

    payload = load_json(path, parameter=parameter)
    if payload.get("format") != DOCUMENT_FORMAT:
        raise QgsProcessingException(
            _tr(
                "'%1' is not a reduced gravity readings document. Run 'Pre-processing "
                "(scale, tide, drift)' on the gravimeter file first."
            ).replace("%1", path)
        )
    if int(payload.get("version", 0)) > DOCUMENT_VERSION:
        raise QgsProcessingException(
            _tr(
                "'%1' was written by a newer GeoComp (document version %2). Update GeoComp "
                "to read it."
            )
            .replace("%1", path)
            .replace("%2", str(payload.get("version")))
        )
    try:
        reduced = [ReducedReading.from_dict(item) for item in payload.get("readings", ())]
        library = ProfileLibrary.from_dict(payload.get("profiles", {}))
    except GeoCompError as exc:
        raise QgsProcessingException(translate_error(exc)) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise QgsProcessingException(
            _tr("'%1' could not be read as reduced gravity readings: %2")
            .replace("%1", path)
            .replace("%2", str(exc))
        ) from exc
    if not reduced:
        raise QgsProcessingException(
            _tr("'%1' holds no readings.").replace("%1", path)
        )
    return reduced, library, payload


def translate_error(error: GeoCompError) -> str:
    """Phrase a core error for Processing, at the boundary where phrasing is allowed."""
    from geocomp.services.messages import message_for

    return message_for(error)


def source_name(path: str) -> str:
    return Path(path).name
