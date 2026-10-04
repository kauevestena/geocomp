# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for what a combination refuses (``specs/13``, phase P9b).

Each says what failed, why, and what to do about it (NFR-006). The combination
refuses more than a single-technique adjustment does -- frames, epochs, height
systems, holds -- and every one of those refusals names the input or the
station, because "the inputs cannot be combined" is true and no use.

Importing this module registers the templates; :mod:`geocomp.algorithms.integration`
imports it.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

TEMPLATES: dict[str, MessageTemplate] = {
    "validation.combination_frame_irreconcilable": MessageTemplate(
        "The input '%1' is in %2, which GeoComp cannot transform from. Give it in "
        "ITRF2000 to ITRF2020 or SIRGAS 2000, or in a UTM or Transverse Mercator "
        "projection of one of them. Combining it untransformed would absorb a datum "
        "shift into the residuals.",
        "input",
        "received",
    ),
    "validation.combination_input_without_frame": MessageTemplate(
        "The input '%1' holds a position (%2) but does not say what frame it is in. "
        "State the frame when the network is built -- for GNSS baselines, the frame "
        "of the base coordinates.",
        "input",
        "subject",
    ),
    "validation.combination_input_without_epoch": MessageTemplate(
        "The input '%1' holds a position (%2) but not its epoch. GeoComp does not "
        "assume one: the frame moves, and the same coordinates at two epochs are two "
        "different places.",
        "input",
        "subject",
    ),
    "validation.combination_epoch_without_velocity": MessageTemplate(
        "In the input '%1', %2 must be moved to the combination's epoch, and no "
        "velocity was given for it. Supply one in the velocities file; zero is not "
        "assumed -- it is a decimetre a decade in most of Brazil.",
        "input",
        "subject",
    ),
    "validation.combination_epoch_required": MessageTemplate(
        "State the epoch of the combination (a decimal year). None of the inputs "
        "states one GeoComp could take, and it does not assume one.",
    ),
    "validation.combination_station_held_differently": MessageTemplate(
        "The station '%1' is held by two inputs (%2) at positions %3 m apart. Hold "
        "it in one input only, or correct the one that is wrong: two holds a "
        "distance apart force that distance into the residuals.",
        "station",
        "received",
        "separation",
    ),
    "validation.combination_projected_hold": MessageTemplate(
        "The input '%1' holds the station '%2' in grid coordinates. In a geocentric "
        "combination a grid height is not the ellipsoidal height the frame holds. "
        "Hold the station through the GNSS input instead (Fixed stations), or leave "
        "it free in this one.",
        "input",
        "station",
    ),
    "validation.combination_benchmark_held_exactly": MessageTemplate(
        "The input '%1' holds the benchmark '%2' exactly. In a geocentric combination "
        "a benchmark's height holds h - N, and holding it exactly would make the "
        "geoid exact there. Give the benchmark its uncertainty (height±sigma) when "
        "adjusting the levelling network.",
        "input",
        "station",
    ),
    "validation.combination_frames_differ": MessageTemplate(
        "The inputs are in different coordinate reference systems (%1). A combination "
        "without GNSS is adjusted in the inputs' own system, so they must share one.",
        "inputs",
    ),
    "validation.combination_gnss_in_local_frame": MessageTemplate(
        "The input '%1' holds GNSS observations (%2), which need a geocentric frame. "
        "Use a combination that includes the GNSS network.",
        "input",
        "observation",
    ),
    "validation.combination_station_without_horizontal": MessageTemplate(
        "%1 station(s) are reached only through heights, so nothing determines where "
        "they are horizontally: %2. Tie them in with a GNSS vector or a total-station "
        "observation, hold them horizontally, or adjust the levelling on its own.",
        "count",
        "stations",
    ),
    "validation.combination_disconnected": MessageTemplate(
        "The inputs fall into %1 pieces that share no station, so they cannot be "
        "adjusted as one network. A combination is tied together by the stations the "
        "techniques have in common.",
        "received",
    ),
    "validation.combination_geoid_in_local_frame": MessageTemplate(
        "A geoid model was given, but this combination is in a local system (%1) where "
        "every height is what its input says it is. Leave the geoid out.",
        "frame",
    ),
    "validation.mixed_height_types": MessageTemplate(
        "Orthometric heights (from levelling) meet the ellipsoidal heights the "
        "geocentric frame computes, and no geoid model relates them. Choose a geoid "
        "model: without one they differ by the undulation, tens of metres in much of "
        "Brazil.",
    ),
    "validation.height_difference_type_unstated": MessageTemplate(
        "The height difference '%1' does not say whether it is orthometric or "
        "ellipsoidal. Rebuild its network with the current GeoComp, which records it.",
        "observation",
    ),
    "validation.epoch_change_without_velocity": MessageTemplate(
        "A position must move from epoch %1 and no velocity was given for it. Supply "
        "one in the velocities file.",
        "received",
    ),
    # -- the geoid grid an integration is given (P12c-7) -------------------------
    "validation.geoid_format_unsupported": MessageTemplate(
        "'%1' is not a geoid grid format GeoComp reads. Give a GTX grid (.gtx) or an ESRI "
        "ASCII grid (.asc, .txt, .grd); QGIS or gdal_translate can convert one.",
        "received",
    ),
    "data.geoid_file_truncated": MessageTemplate(
        "The geoid grid '%1' is truncated: it has %2 bytes, and the format needs %3.",
        "path",
        "received",
        "needed",
    ),
    "data.geoid_header_not_usable": MessageTemplate(
        "The header of the geoid grid '%1' does not describe a usable grid (%2): it needs at "
        "least 2 by 2 nodes and a positive spacing, in degrees.",
        "path",
        "received",
    ),
    "data.geoid_header_incomplete": MessageTemplate(
        "The header of the geoid grid '%1' is not a complete ESRI ASCII header: it lacks %2.",
        "path",
        "missing",
    ),
    "data.geoid_cell_count": MessageTemplate(
        "The geoid grid '%1' has %2 values where its header promises %3, for a grid of %4 by "
        "%5. The file is truncated or damaged.",
        "path",
        "received",
        "cells",
        "rows",
        "columns",
    ),
    "data.geoid_grid_has_no_data": MessageTemplate(
        "The geoid grid '%1' has cells without data (value %2). Such a cell would be "
        "interpolated into a plausible-looking undulation, so the grid is refused. Use a grid "
        "that covers the network completely.",
        "path",
        "received",
    ),
    # -- the combination the core refuses (P12c-7) ------------------------------
    "validation.combination_gravity_without_its_network": MessageTemplate(
        "Gravity observations (%1) were merged into the geometric network, where they would be "
        "adjusted as if free of drift. Give the gravity as its own network, built with its "
        "drift model.",
        "observations",
    ),
    "validation.combination_routed_to_dynadjust": MessageTemplate(
        "This combination was routed to DynAdjust (%1) and cannot be adjusted here. Choose "
        "GeoComp's own engine, or the DynAdjust path.",
        "reason",
    ),
    "validation.engine_unknown": MessageTemplate(
        "'%1' is not an adjustment engine; expected %2.",
        "received",
        "expected",
    ),
    "validation.combination_station_without_position": MessageTemplate(
        "The station '%2' of '%1' has no approximate position, which the combination needs to "
        "know which way is up there. Give it an approximate position.",
        "input",
        "station",
    ),
    # -- geoid models and the heights they relate (P12c-7) -----------------------
    "validation.geoid_without_id": MessageTemplate(
        "A geoid model has no id; a solution records which model produced its heights by it. "
        "Give the model one.",
    ),
    "data.geoid_grid_too_small": MessageTemplate(
        "The geoid model '%1' has a grid of shape %2; interpolation needs a two-dimensional grid "
        "of at least 2 by 2 nodes.",
        "geoid",
        "shape",
    ),
    "data.geoid_grid_not_finite": MessageTemplate(
        "The geoid model '%1' has nodes without a value. A no-data value in the grid would be "
        "interpolated into a plausible-looking height; fill the grid, or use one that covers the "
        "area completely.",
        "geoid",
    ),
    "validation.geoid_without_sigma": MessageTemplate(
        "The geoid model '%1' states an accuracy of %2. A geoid model is not exact, and its "
        "uncertainty often limits a combined height solution; give its stated accuracy in "
        "metres, as a positive number.",
        "geoid",
        "received",
    ),
    "validation.geoid_outside_coverage": MessageTemplate(
        "The point at latitude, longitude %2 lies outside the coverage of the geoid model '%1', "
        "which spans latitudes %3 to %4 and longitudes %5 to %6. A geoid model quoted beyond "
        "its coverage gives a confidently wrong height; use a model that covers the point.",
        "geoid",
        "received",
        "south",
        "north",
        "west",
        "east",
    ),
    "validation.coverage_not_ordered": MessageTemplate(
        "The coverage of a geoid model is not in order: its south bound must lie below its north "
        "bound, and its west bound west of its east. Check the bounds the grid declares.",
    ),
    "validation.height_conversion_unsupported": MessageTemplate(
        "Heights cannot be converted between %1. A geoid relates ellipsoidal and orthometric "
        "heights only; normal heights need a quasi-geoid, which is a different model.",
        "received",
    ),
    "validation.height_wrong_unit": MessageTemplate(
        "The %1 is in %2, where %3 was expected.",
        "parameter",
        "received",
        "expected",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
