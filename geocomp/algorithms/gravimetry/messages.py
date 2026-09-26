# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for the errors the gravimetry algorithms surface (phase P8b).

Each says what failed, why, and what to do about it (NFR-006). Importing this
module registers them; :mod:`geocomp.algorithms.gravimetry` does.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

TEMPLATES: dict[str, MessageTemplate] = {
    "data.gravimeter_format_unknown": MessageTemplate(
        "This file is not a gravimeter export GeoComp can read. Expected %1.",
        "expected",
    ),
    "data.gravimeter_line_unreadable": MessageTemplate(
        "Line %1 of '%2' could not be read: %3. Correct or remove the line and run again.",
        "line",
        "source",
        "expected",
    ),
    "data.gravimeter_file_empty": MessageTemplate(
        "'%1' holds no readings: expected %2.",
        "source",
        "expected",
    ),
    "data.gravimeter_csv_naive_time": MessageTemplate(
        "Line %1 of '%2' gives the time '%3' without its offset from UTC. The tide depends "
        "on the time to the minute, so a time without a zone is a guess; write it as, for "
        "example, 2013-09-15T05:57:01Z or 2013-09-15T02:57:01-03:00.",
        "line",
        "source",
        "received",
    ),
    "data.gravimeter_csv_columns": MessageTemplate(
        "The CSV '%1' lacks required columns: it has %2, and needs %3.",
        "source",
        "received",
        "expected",
    ),
    "data.gravimeter_header_location": MessageTemplate(
        "The CG-5 header field %1 of '%2' reads '%3', which is not a latitude or longitude "
        "with its hemisphere. The tide needs the survey's location.",
        "field",
        "source",
        "received",
    ),
    "validation.gravimeter_clock_unsettled": MessageTemplate(
        "GeoComp cannot tell which way this file's GMT difference runs, and computing the "
        "tide needs UTC. Give the offset of the file's times from UTC explicitly, or keep "
        "the instrument's own tide correction.",
    ),
    "validation.gravimeter_reading_without_precision": MessageTemplate(
        "The readings of '%1' state no precision and its profile gives none. GeoComp does "
        "not invent a weight: set a reading precision floor, or a nominal precision in the "
        "gravimeter profile.",
        "gravimeter",
    ),
    "validation.no_gravimeter_profile": MessageTemplate(
        "No gravimeter profile was named and the profile library sets no default. Add one "
        "to the library, or run without a library to use the file's own instrument names.",
    ),
    "validation.unknown_gravimeter_profile": MessageTemplate(
        "The readings name the gravimeter '%1', which the profile library does not hold: "
        "expected %2. Add a profile with that id, carrying the instrument's calibration.",
        "gravimeter",
        "expected",
    ),
    "validation.gravity_reading_without_location": MessageTemplate(
        "Reading '%1' needs a tide correction and has no latitude and longitude to compute "
        "it for. Add the location to the file, or keep an instrument-applied tide.",
        "reading",
    ),
    "validation.gravity_reading_tide_not_removed": MessageTemplate(
        "Reading '%1' has had no tide removed, and the tide model is set to none. Leaving "
        "the tide in costs a few hundred microgal that change by the hour; choose Longman's "
        "model, or confirm that the instrument applied its own.",
        "reading",
    ),
    "validation.gravity_drift_not_estimable": MessageTemplate(
        "The drift of session '%1' cannot be estimated with the station values: no station "
        "was read again at enough different times for a degree-%2 drift. Re-occupy a "
        "station in that session, lower the degree, or split the session.",
        "session",
        "degree",
    ),
    "validation.gravity_drift_base_insufficient": MessageTemplate(
        "Session '%1' cannot be pre-corrected: its base station %2 was read %3 time(s), "
        "and a degree-%4 drift needs one more reading than its degree. Estimate the drift "
        "with the station values instead, or lower the degree.",
        "session",
        "base_station",
        "base_occupations",
        "degree",
    ),
    "validation.gravity_session_mixes_instruments": MessageTemplate(
        "Session '%1' holds readings from several instruments (%2). Drift belongs to an "
        "instrument, so each needs its own session.",
        "session",
        "received",
    ),
    "validation.gravity_station_without_location": MessageTemplate(
        "Station '%1' has no location, so its adjusted gravity has nowhere to be reported. "
        "Give its readings a latitude and longitude.",
        "station",
    ),
    "validation.gravity_station_not_observed": MessageTemplate(
        "No reading or absolute value refers to %1, so its gravity cannot be held or "
        "adjusted. Check the station names against the readings.",
        "received",
    ),
    "validation.gravimeter_reading_outside_table": MessageTemplate(
        "A counter reading of %1 is outside the gravimeter's calibration table: expected "
        "%2.",
        "received",
        "expected",
    ),
    "validation.duplicate_gravity_reading": MessageTemplate(
        "The reading '%1' appears twice. Remove the duplicate line and run again.",
        "reading",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
