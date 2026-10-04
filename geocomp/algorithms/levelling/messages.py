# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for what the levelling algorithms refuse (``specs/10``; phase P12a).

Each says what happened and what to do about it (NFR-006). The orthometric
correction arrived in the network adjustment in P12a, and with it two refusals
whose whole value is the list of stations they name: shown as their codes, a
user with forty marks would be left to find the missing three by hand.

Importing this module registers the templates; :mod:`geocomp.algorithms.levelling`
imports it.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

TEMPLATES: dict[str, MessageTemplate] = {
    "validation.orthometric_correction_without_position": MessageTemplate(
        "The orthometric correction needs the latitude of every station a line ends at, "
        "and these have no position in the station positions layer: %1. Add them, check "
        "the station id field, or turn the correction off.",
        "received",
    ),
    "validation.orthometric_correction_without_height": MessageTemplate(
        "The orthometric correction needs an approximate height for every station, and "
        "these have none: %1. Connect them to a benchmark, or turn the correction off.",
        "received",
    ),
    # -- the levelling book and its mapping (P12c-7) ----------------------------
    "validation.unknown_level_mapping_field": MessageTemplate(
        "The mapping names %1, which GeoComp does not know as a levelling-book field. "
        "Expected %2.",
        "received",
        "expected",
    ),
    "validation.stadia_factor_not_positive": MessageTemplate(
        "The stadia constant must be positive, usually 100; %1 was given.",
        "received",
    ),
    "validation.ambiguous_level_layout": MessageTemplate(
        "The mapping '%1' mixes the columns of two book layouts (%2). Map station and sight "
        "for a book with one row per reading, or backsight_station and foresight_station for "
        "one row per setup, not both.",
        "mapping",
        "received",
    ),
    "validation.unrecognised_level_layout": MessageTemplate(
        "The mapping '%1' does not show which book layout it is: it maps %2. Map station and "
        "sight for a book with one row per reading, or backsight_station and "
        "foresight_station for one row per setup.",
        "mapping",
        "received",
    ),
    "validation.level_mapping_incomplete": MessageTemplate(
        "The mapping '%1' maps %2, and needs %3.",
        "mapping",
        "received",
        "expected",
    ),
    "validation.level_book_empty": MessageTemplate(
        "The levelling book has no data: it needs a header row and at least one row of "
        "readings.",
    ),
    # -- the readings, setups, lines and network the core refuses (P12c-7) ------
    "validation.staff_reading_without_station": MessageTemplate(
        "A staff reading names no station. Every reading needs the point the staff stood on.",
    ),
    "validation.staff_reading_not_a_quantity": MessageTemplate(
        "The reading on '%1' carries no uncertainty; every reading needs one.",
        "station",
    ),
    "validation.staff_reading_wrong_unit": MessageTemplate(
        "The %1 of the reading on '%2' is in %3; give it in metres.",
        "parameter",
        "station",
        "received",
    ),
    "validation.negative_sight_distance": MessageTemplate(
        "The sight distance to '%1' is negative (%2). Check the book's distance column.",
        "station",
        "received",
    ),
    "validation.three_wire_out_of_order": MessageTemplate(
        "The three-wire readings %1 are not in the order lower, middle, upper. A staff is "
        "read upwards, so the values were probably entered in the wrong columns.",
        "received",
    ),
    "validation.three_wire_reading_not_a_quantity": MessageTemplate(
        "The %1 wire reading carries no uncertainty; every reading needs one.",
        "component",
    ),
    "validation.three_wire_wrong_unit": MessageTemplate(
        "The %1 wire reading is in %2; give it in metres.",
        "component",
        "received",
    ),
    "validation.level_setup_without_id": MessageTemplate(
        "A setup has no id. Readings and findings refer to a setup by its id; give every "
        "setup one.",
    ),
    "validation.level_setup_without_foresight": MessageTemplate(
        "The setup '%1' has no foresight: a backsight alone gives no height difference.",
        "setup",
    ),
    "validation.level_setup_repeats_a_station": MessageTemplate(
        "The setup '%1' sights the same station more than once (%2). A second sight onto "
        "the same point from one setup adds nothing; check the station names.",
        "setup",
        "received",
    ),
    "validation.levelling_line_without_id": MessageTemplate(
        "A levelling line has no id. Closures and findings refer to a line by its id; give "
        "every line one.",
    ),
    "validation.levelling_line_without_setups": MessageTemplate(
        "The levelling line '%1' has no setups. Check the book's line and setup columns.",
        "line",
    ),
    "validation.levelling_line_discontinuous": MessageTemplate(
        "The levelling line '%1' breaks at setup '%2': its backsight is on %3, where %4 was "
        "expected.",
        "line",
        "setup",
        "received",
        "expected",
    ),
    "validation.known_difference_wrong_unit": MessageTemplate(
        "A known height difference is in %1; give it in metres.",
        "received",
    ),
    "validation.height_difference_wrong_unit": MessageTemplate(
        "A height difference is in %1; give it in metres.",
        "received",
    ),
    "validation.loop_without_lines": MessageTemplate(
        "The loop '%1' has no lines. A loop is a sequence of levelling lines that returns to "
        "where it began.",
        "loop",
    ),
    "validation.loop_discontinuous": MessageTemplate(
        "The loop '%1' is broken at line '%2', which joins %3 and does not continue from the "
        "line before it: expected %4.",
        "loop",
        "line",
        "received",
        "expected",
    ),
    "validation.loop_does_not_close": MessageTemplate(
        "The loop '%1' ends at %2 and does not return to where it began: expected %3.",
        "loop",
        "received",
        "expected",
    ),
    "validation.section_runs_disagree": MessageTemplate(
        "The two runs of a double-run section join different stations (%1). Both runs of a "
        "section go between the same two stations, in either direction.",
        "received",
    ),
    "validation.unknown_weighting_mode": MessageTemplate(
        "'%1' is not a weighting mode; use length or setups.",
        "received",
    ),
    "validation.levelling_network_without_lines": MessageTemplate(
        "The levelling network '%1' has no reduced lines, so there is nothing to adjust.",
        "network",
    ),
    "validation.levelling_network_without_setups": MessageTemplate(
        "The levelling network '%1' has no reduced setups, so there is nothing to adjust.",
        "network",
    ),
    "validation.benchmark_not_in_network": MessageTemplate(
        "No levelling line of '%1' reaches the benchmarks %2. A constraint on a station no "
        "line reaches does nothing, and would hide that the network is unconstrained; check "
        "their names, or remove them.",
        "network",
        "received",
    ),
    "validation.benchmark_height_wrong_unit": MessageTemplate(
        "The height of the benchmark '%1' is in %2; give it in metres.",
        "station",
        "received",
    ),
    "validation.benchmark_without_height_type": MessageTemplate(
        "The benchmark '%1' does not say which kind of height it has (orthometric, normal or "
        "ellipsoidal), so it cannot be checked against the others.",
        "station",
    ),
    "validation.weighted_benchmark_without_uncertainty": MessageTemplate(
        "The benchmark '%1' is a weighted constraint with no uncertainty, which is a fixed "
        "constraint under another name. Give its height an uncertainty, or hold it fixed.",
        "station",
    ),
    "validation.geoid_model_named_without_grid": MessageTemplate(
        "The geoid model '%1' is named but its grid was not given, and the benchmarks mix "
        "height types (%2). A name records which model was used but cannot compute an "
        "undulation: give the geoid grid, or convert the heights first.",
        "geoid_model",
        "received",
    ),
    "validation.benchmark_without_position": MessageTemplate(
        "The benchmark '%1' has a %2 height to convert with the geoid '%3', and no position: "
        "a geoid undulation depends on where the station is. Give the benchmark its latitude "
        "and longitude.",
        "station",
        "received",
        "geoid",
    ),
    "validation.line_length_unknown": MessageTemplate(
        "The length of the levelling line '%1' is unknown, because it has no sight distances, "
        "and weighting by length needs it. Weight by setup count instead, or record the "
        "distances.",
        "line",
    ),
    "validation.line_extent_not_positive": MessageTemplate(
        "The levelling line '%1' has a %2 of %3, which cannot weight it: a zero would give it "
        "no uncertainty and an infinite weight. Check its sight distances or setups.",
        "line",
        "kind",
        "received",
    ),
    "validation.orthometric_correction_wrong_unit": MessageTemplate(
        "A height difference for the orthometric correction is in %1; give it in metres.",
        "received",
    ),
    "validation.latitude_out_of_range": MessageTemplate(
        "The %1 latitude %2 (radians) lies outside -90 to 90 degrees. Check the stations' "
        "positions.",
        "parameter",
        "received",
    ),
    "validation.variance_inflation_below_one": MessageTemplate(
        "The variance inflation of a reciprocal crossing must be at least 1; %1 was given. A "
        "smaller factor would claim the method is better than its readings.",
        "received",
    ),
    "validation.reciprocal_pair_same_station": MessageTemplate(
        "A reciprocal pair at setup '%1' reads the same station, '%2', on both banks. A "
        "reciprocal crossing needs one station on each bank.",
        "setup",
        "station",
    ),
    "validation.reciprocal_pairs_disagree": MessageTemplate(
        "The two pairs of a reciprocal crossing join different stations: the second joins %1, "
        "where %2 was expected.",
        "received",
        "expected",
    ),
    "validation.reciprocal_second_pair_reversed": MessageTemplate(
        "The second pair of a reciprocal crossing is reversed: its near reading is on %1, "
        "where %2 was expected.",
        "received",
        "expected",
    ),
    "validation.station_not_foresighted": MessageTemplate(
        "Station '%1' is not foresighted from setup '%2', which foresights %3.",
        "station",
        "setup",
        "expected",
    ),
    # -- level profiles and levelling classes (P12c-7) -------------------------
    "validation.level_profile_without_id": MessageTemplate(
        "A level profile has no id; observations refer to a profile by it. Give every profile "
        "one.",
    ),
    "validation.levelling_class_without_id": MessageTemplate(
        "A levelling class has no id; lines and reports refer to a class by it. Give every "
        "class one.",
    ),
    "validation.level_stadia_factor_not_positive": MessageTemplate(
        "The stadia constant of the level '%1' must be positive, usually 100; %2 was given.",
        "level",
        "received",
    ),
    "validation.level_sigma_negative": MessageTemplate(
        "The %2 of the level '%1' is %3; a standard deviation cannot be negative.",
        "level",
        "parameter",
        "received",
    ),
    "validation.level_without_reading_sigma": MessageTemplate(
        "The level profile '%1' has no reading standard deviation, and GeoComp does not invent "
        "one: a fabricated weight corrupts every statistic computed from it. Give the profile "
        "its sigma_reading.",
        "level",
    ),
    "validation.levelling_class_negative_limit": MessageTemplate(
        "The %2 of the levelling class '%1' is %3; a limit cannot be negative, and zero means "
        "unconstrained.",
        "levelling_class",
        "parameter",
        "received",
    ),
    "validation.negative_line_length": MessageTemplate(
        "A levelling line length cannot be negative; %1 km was given.",
        "received",
    ),
    "validation.negative_setup_count": MessageTemplate(
        "The number of setups for the level '%1' cannot be negative; %2 was given.",
        "level",
        "received",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
