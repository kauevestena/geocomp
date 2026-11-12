# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for what a typed job refuses (``specs/15`` section 7; phase P14a).

``geocomp.jobs`` reads what was typed and refuses what it cannot read, by code.
These are the words. Each says what is wrong and what to type instead (NFR-006):
a cell that cannot be read is the commonest thing a window ever has to say, and
"invalid value" would be the least useful way of saying it.

The angle refusals differ by convention on purpose. ``87.3115`` is refused in a
job typed as degrees, minutes and seconds, and what the user needs to hear is
not that it is wrong but that this job takes angles another way -- and where to
change that.

Importing this module registers the templates; :mod:`geocomp.gui.workbench`
imports it.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

TEMPLATES: dict[str, MessageTemplate] = {
    # -- a cell ------------------------------------------------------------
    "validation.typed_angle_not_dms": MessageTemplate(
        "'%1' is not an angle in degrees, minutes and seconds. Enter it as three numbers, "
        "such as 87 31 15.",
        "received",
    ),
    "validation.typed_angle_fraction_misplaced": MessageTemplate(
        "'%1' has decimals where an angle in degrees, minutes and seconds takes none: only its "
        "last part may have them. Enter it as 87 31 15.5, or change the angle convention in "
        "the Field book window's first step.",
        "received",
    ),
    "validation.typed_angle_sexagesimal_out_of_range": MessageTemplate(
        "'%1' has sixty or more minutes or seconds. Correct it: minutes and seconds run from "
        "0 to 59.",
        "received",
    ),
    "validation.typed_angle_not_packed": MessageTemplate(
        "'%1' is not an angle typed as DDD.MMSS. Enter it as 87.3115 for 87 degrees 31 minutes "
        "15 seconds, or change the angle convention in the Field book window's first step.",
        "received",
    ),
    "validation.typed_angle_not_a_number": MessageTemplate(
        "'%1' is not an angle typed as one decimal number. Enter it as 87.5208, or change the "
        "angle convention in the Field book window's first step.",
        "received",
    ),
    "validation.typed_choice_unknown": MessageTemplate(
        "'%1' is not a value this column takes. Enter one of: %2.",
        "received",
        "expected",
    ),
    "validation.typed_number_unreadable": MessageTemplate(
        "'%1' is not a number. Enter it in digits with a decimal point or comma, such as 13.204.",
        "received",
    ),
    "validation.typed_integer_unreadable": MessageTemplate(
        "'%1' is not a whole number. Enter it in digits only, such as 2.",
        "received",
    ),
    # -- the job file --------------------------------------------------------
    "validation.job_file_not_a_job": MessageTemplate(
        "'%1' is not a GeoComp job file. Choose a file saved from a GeoComp window; its name "
        "ends in .gcjob.",
        "path",
    ),
    "validation.job_file_newer": MessageTemplate(
        "'%1' was saved by a later GeoComp: its job format is %2 and this version reads up to "
        "%3. Update GeoComp to open it.",
        "path",
        "version",
        "supported",
    ),
    "validation.job_file_unreadable": MessageTemplate(
        "'%1' could not be read as a job file (%2). Check that the file is there and complete.",
        "path",
        "reason",
    ),
    "validation.job_other_technique": MessageTemplate(
        "'%1' is the job of another technique. Open it from that technique's windows in the "
        "GeoComp menu.",
        "path",
    ),
    "storage.job_not_saved": MessageTemplate(
        "The job could not be saved to '%1' (%2). Choose a folder you can write in.",
        "path",
        "reason",
    ),
    # -- the total-station field book ----------------------------------------
    "validation.field_book_cells_unreadable": MessageTemplate(
        "%1 cell(s) of the field book cannot be read. Correct the cells marked in the Field "
        "book window first.",
        "count",
    ),
    "validation.field_book_empty": MessageTemplate(
        "The field book holds no pointing yet. Enter the observations in the Field book window "
        "first.",
    ),
    "validation.readings_document_not_readings": MessageTemplate(
        "'%1' is not a GeoComp readings document. Choose the file Import field book wrote.",
        "path",
    ),
    "validation.readings_document_malformed": MessageTemplate(
        "'%1' is not a readings document as GeoComp writes it (%2). Choose the file Import "
        "field book wrote.",
        "path",
        "reason",
    ),
    # -- known points and orientations ----------------------------------------
    "validation.known_points_unreadable": MessageTemplate(
        "%1 cell(s) of the known points cannot be read. Correct the cells marked.",
        "count",
    ),
    "validation.known_point_incomplete": MessageTemplate(
        "Row %1 of the known points lacks its name or a coordinate. Give its name, easting, "
        "northing and height; enter 0 for the height where the survey has none.",
        "row",
    ),
    "validation.known_point_repeated": MessageTemplate(
        "The known point '%1' is given twice. Remove one of its rows.",
        "point",
    ),
    "validation.known_points_missing": MessageTemplate(
        "No known point is given. Add at least the station the instrument occupied, with its "
        "coordinates.",
    ),
    "validation.orientations_unreadable": MessageTemplate(
        "%1 azimuth(s) cannot be read. Correct the cells marked.",
        "count",
    ),
    "validation.orientation_incomplete": MessageTemplate(
        "Row %1 of the orientations lacks its station or its azimuth. Give both, or remove "
        "the row.",
        "row",
    ),
    "validation.known_point_unplaced": MessageTemplate(
        "Row %1 of the known points lacks its name, its easting or its northing. Give all "
        "three, or remove the row.",
        "row",
    ),
    # -- resection and forward intersection (P14b) -----------------------------
    "validation.resection_no_station": MessageTemplate(
        "No occupied station is chosen. Choose the station to resect in the Resection "
        "window's first step.",
    ),
    "validation.sightings_unreadable": MessageTemplate(
        "%1 azimuth(s) of the sightings cannot be read. Correct the cells marked.",
        "count",
    ),
    "validation.sighting_incomplete": MessageTemplate(
        "Row %1 of the sightings lacks its station or its azimuth. Give both, or remove the "
        "row.",
        "row",
    ),
    "validation.sighting_repeated": MessageTemplate(
        "Station '%1' has two sightings. Keep one: the intersection takes one azimuth from "
        "each station.",
        "station",
    ),
    "validation.sighting_station_unknown": MessageTemplate(
        "Station '%1' has a sighting but no coordinates. Add it to the known points.",
        "station",
    ),
    # -- the levelling field book and its benchmarks (P14c) ---------------------
    "validation.level_book_cells_unreadable": MessageTemplate(
        "%1 cell(s) of the levelling field book cannot be read. Correct the cells marked in "
        "the Levelling field book window first.",
        "count",
    ),
    "validation.level_book_empty": MessageTemplate(
        "The levelling field book holds no reading yet. Enter the readings in the Levelling "
        "field book window first.",
    ),
    "validation.benchmarks_unreadable": MessageTemplate(
        "%1 cell(s) of the benchmarks cannot be read. Correct the cells marked.",
        "count",
    ),
    "validation.benchmark_incomplete": MessageTemplate(
        "Row %1 of the benchmarks lacks its name or its height. Give both, or remove the row.",
        "row",
    ),
    "validation.benchmark_repeated": MessageTemplate(
        "The benchmark '%1' is given twice. Remove one of its rows.",
        "name",
    ),
    "validation.benchmark_name_unusable": MessageTemplate(
        "The benchmark name '%1' holds one of %2, which the network's list of benchmarks is "
        "written with. Rename it without them.",
        "name",
        "marks",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
