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
    # -- a levelling book's rows, setups and lines (P12c-8) -----------------------
    # Each refusal is reported as a finding, worded by the frame it is reported
    # in with the refusal's own words as the reason.
    "data.level_missing_value": MessageTemplate(
        "'%1' is empty.",
        "field",
    ),
    "data.level_unreadable_number": MessageTemplate(
        "'%2', given for '%1', is not a number.",
        "field",
        "received",
    ),
    "data.level_unknown_sight": MessageTemplate(
        "'%1' is not a kind of sight the mapping knows (%2).",
        "received",
        "expected",
    ),
    "finding.level_book_row_refused": MessageTemplate(
        "Row %1: %2",
        "row",
        "reason",
    ),
    "finding.level_setup_refused": MessageTemplate(
        "Setup %1: %2",
        "setup",
        "reason",
    ),
    "finding.level_line_refused": MessageTemplate(
        "Line %1: %2",
        "line",
        "reason",
    ),
    "finding.level_setup_malformed": MessageTemplate(
        "Setup %1 has %2 backsight(s) and %3 foresight(s); it needs exactly one backsight and "
        "at least one foresight.",
        "setup",
        "backsights",
        "foresights",
    ),
    # -- what a levelling reduction or network reports (P12c-8) -----------------
    "finding.closure_out_of_tolerance": MessageTemplate(
        "%1 misclosed by %2 mm over %3 km, beyond the %4 mm permitted by class %5. GeoComp "
        "will not adjust a line that failed its tolerance without an explicit acknowledgement.",
        "subject",
        "misclosure",
        "length",
        "permitted",
        "class",
    ),
    "finding.closure_not_judged_without_class": MessageTemplate(
        "%1 misclosed by %2 mm, which has not been judged against a tolerance because no "
        "levelling class was given. The misclosure is reported; whether it is acceptable is not.",
        "subject",
        "misclosure",
    ),
    "finding.closure_not_judged_without_coefficient": MessageTemplate(
        "%1 misclosed by %2 mm, which has not been judged against a tolerance because the class "
        "states no tolerance coefficient. The misclosure is reported; whether it is acceptable "
        "is not.",
        "subject",
        "misclosure",
    ),
    "finding.closure_not_judged_without_length": MessageTemplate(
        "%1 misclosed by %2 mm, which has not been judged against a tolerance because no sight "
        "distances were recorded, so its length is unknown. The misclosure is reported; whether "
        "it is acceptable is not.",
        "subject",
        "misclosure",
    ),
    "finding.closure_exceeds_its_own_precision": MessageTemplate(
        "%1 misclosed by %2 mm, which is %3 times its own propagated standard deviation. That "
        "is not accumulated random error, so distributing it proportionally would spread one "
        "mistake evenly along the line and make it harder to find. Adjust the network and let "
        "data snooping locate it instead.",
        "subject",
        "misclosure",
        "ratio",
    ),
    "finding.closure_consistent_with_its_precision": MessageTemplate(
        "%1 misclosed by %2 mm, %3 times its own propagated standard deviation. That is "
        "consistent with accumulated random error, which is the case proportional distribution "
        "is correct for.",
        "subject",
        "misclosure",
        "ratio",
    ),
    "finding.levelling_line_length_unknown": MessageTemplate(
        "The line %1 recorded no sight distances, so its length is unknown. Length weighting "
        "and the k*sqrt(L) tolerance both need it, and will refuse rather than assume a length "
        "of zero.",
        "line",
    ),
    "finding.levelling_line_accumulated_imbalance": MessageTemplate(
        "The line %1 accumulated %2 m of sight imbalance, beyond the %3 m its class permits. It "
        "is the accumulated figure, not the per-setup one, that multiplies the collimation "
        "error over a line.",
        "line",
        "imbalance",
        "permitted",
    ),
    "finding.levelling_line_balanced": MessageTemplate(
        "The line %1 is exactly balanced, so the collimation error contributes neither a "
        "correction nor an uncertainty, whatever its value. This is what makes equal sights the "
        "preferred method.",
        "line",
    ),
    "finding.levelling_side_shots_not_adjusted": MessageTemplate(
        "%1 side shot(s) were levelled from these lines and are not in the network: %2. A spur "
        "observed once has no redundancy, so adjusting it would change nothing; their heights "
        "follow from the adjusted line. Adjust the network from its setups to include every "
        "point.",
        "count",
        "stations",
    ),
    "finding.levelling_weighted_by_propagation": MessageTemplate(
        "The network was weighted by each line's propagated reading uncertainty, since no "
        "k*sqrt(L) or k*sqrt(n) model was configured. That figure knows nothing of refraction, "
        "staff calibration or a tripod settling, so expect a variance factor above one.",
    ),
    "finding.levelling_weighted_by_model": MessageTemplate(
        "The network was weighted by %1, replacing each line's propagated reading uncertainty.",
        "model",
    ),
    "finding.levelling_network_is_free": MessageTemplate(
        "No benchmark was supplied, so the network is free: it has one datum defect, and "
        "determines every height difference but no height. Adjust it with an inner or minimum "
        "constraint.",
    ),
    "finding.levelling_other_technique_added": MessageTemplate(
        "%1 trigonometric height difference(s) joined the network, each weighted by its own "
        "propagated uncertainty.",
        "count",
    ),
    "finding.levelling_other_technique_added_new_points": MessageTemplate(
        "%1 trigonometric height difference(s) joined the network, each weighted by its own "
        "propagated uncertainty; they reach %2 point(s) no line did.",
        "count",
        "added",
    ),
    "finding.height_converted_through_geoid": MessageTemplate(
        "%1: the ellipsoidal height %2 m was converted to the orthometric height %3 m through "
        "%4 (N = %5 m). The model's uncertainty is in the result, which is now +/- %6 mm "
        "rather than %7 mm.",
        "station",
        "from",
        "to",
        "geoid",
        "undulation",
        "now",
        "before",
    ),
    "finding.levelling_line_very_short": MessageTemplate(
        "The line %1 is %2 m long, so a length-weighted standard deviation for it is almost "
        "zero, and its weight almost infinite.",
        "line",
        "length",
    ),
    "finding.levelling_setups_clustered": MessageTemplate(
        "%1 setup(s) carried several foresights and entered the network as correlated "
        "clusters. They share their backsight, so it cancels in every difference the "
        "adjustment forms between two points of one setup, which makes those differences "
        "better determined, not worse.",
        "count",
    ),
    "finding.level_setup_without_distances": MessageTemplate(
        "Setup %1 recorded no sight distances, so its balance cannot be checked and no "
        "collimation correction can be applied. Record the distances, or read three wires and "
        "let them be derived.",
        "setup",
    ),
    "finding.level_sight_too_long": MessageTemplate(
        "The sight to %1 from setup %2 is %3 m, beyond the %4 m its class permits. Long sights "
        "magnify both refraction and the residual collimation error.",
        "station",
        "setup",
        "length",
        "permitted",
    ),
    "finding.level_setup_imbalanced": MessageTemplate(
        "Setup %1 is out of balance by %2 m on the sight to %3, beyond the %4 m its class "
        "permits.",
        "setup",
        "imbalance",
        "station",
        "permitted",
    ),
    "finding.level_imbalance_without_instrument": MessageTemplate(
        "Setup %1 is out of balance by %2 m and no level profile was supplied, so no "
        "collimation correction was applied. Supply the two-peg test result to correct it, or "
        "balance the sights so it does not matter.",
        "setup",
        "imbalance",
    ),
    "finding.reciprocal_variance_inflated": MessageTemplate(
        "The variance of this crossing was multiplied by %1. Refraction over water varies "
        "rapidly and asymmetrically, and the two reciprocal observations were not simultaneous, "
        "so the symmetry the method relies on holds only approximately.",
        "factor",
    ),
    "finding.reciprocal_variance_not_inflated": MessageTemplate(
        "This crossing was reduced with no variance inflation, so its uncertainty assumes the "
        "two reciprocal observations saw identical refraction. They were not simultaneous, so "
        "they did not.",
    ),
    "finding.reciprocal_determinations_disagree": MessageTemplate(
        "The two banks give height differences that differ by %1 m. The method assumes the "
        "refraction was the same for both, and a discrepancy this size says it was not.",
        "discrepancy",
    ),
    "finding.orthometric_correction_negligible": MessageTemplate(
        "The normal orthometric correction for this section is %1 mm, below the %2 mm at which "
        "it could matter to any levelling. Applying it changes nothing.",
        "correction",
        "threshold",
    ),
    "finding.orthometric_correction_applied": MessageTemplate(
        "The normal orthometric correction for this section is %1 mm, at mean latitude %2 "
        "degrees and mean height %3 m. This is the normal correction, from the ellipsoid's "
        "gravity field; the rigorous one needs observed gravity along the line.",
        "correction",
        "latitude",
        "height",
    ),
    "finding.three_wire_half_sum": MessageTemplate(
        "The three wires read at %1 from setup %2 give (upper + lower) / 2 - middle = %3 m, "
        "which should be zero. One of the three was misread, or they were entered in the wrong "
        "columns.",
        "station",
        "setup",
        "residual",
    ),
    "finding.three_wire_half_sum_outside_a_setup": MessageTemplate(
        "The three wires read at %1 give (upper + lower) / 2 - middle = %2 m, which should be "
        "zero. One of the three was misread, or they were entered in the wrong columns.",
        "station",
        "residual",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
