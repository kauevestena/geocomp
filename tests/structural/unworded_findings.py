# SPDX-License-Identifier: GPL-2.0-or-later
"""The findings that still reach the reader as an English sentence: P12c-8's baseline.

FR-091 and ``specs/18`` section 2: the core never phrases a sentence, and the
presentation layer words what the user reads. A ``Finding`` carried only an
English ``message`` until P12c-8, and every report, log line and dialog showed
it whatever the language. P12c-8 gave findings a ``context`` and a template,
``finding.<code>``. Its first pull request worded the importers' findings and
the field books' refused rows, network inspection and the pre-analysis design.
These are the techniques' findings that are left: levelling and the total
station.

The list may only shrink. ``tests/structural/test_message_templates.py`` fails
on a finding made without a template that is not listed here, and on a listed
code that has gained a template or is no longer made.

Grouped by the directory that makes each finding.
"""

from __future__ import annotations

UNWORDED: frozenset[str] = frozenset(
    {
        # core/techniques/levelling/ (25)
        "finding.closure_consistent_with_its_precision",
        "finding.closure_exceeds_its_own_precision",
        "finding.closure_not_judged",
        "finding.closure_out_of_tolerance",
        "finding.height_converted_through_geoid",
        "finding.level_imbalance_without_instrument",
        "finding.level_setup_imbalanced",
        "finding.level_setup_without_distances",
        "finding.level_sight_too_long",
        "finding.levelling_line_accumulated_imbalance",
        "finding.levelling_line_balanced",
        "finding.levelling_line_length_unknown",
        "finding.levelling_line_very_short",
        "finding.levelling_network_is_free",
        "finding.levelling_other_technique_added",
        "finding.levelling_setups_clustered",
        "finding.levelling_side_shots_not_adjusted",
        "finding.levelling_weighted_by_model",
        "finding.levelling_weighted_by_propagation",
        "finding.orthometric_correction_applied",
        "finding.orthometric_correction_negligible",
        "finding.reciprocal_determinations_disagree",
        "finding.reciprocal_variance_inflated",
        "finding.reciprocal_variance_not_inflated",
        "finding.three_wire_half_sum",
        # core/techniques/total_station/ (17)
        "finding.angular_misclosure_beyond_tolerance",
        "finding.collimation_beyond_tolerance",
        "finding.collimation_drift",
        "finding.collinear_known_points",
        "finding.danger_circle",
        "finding.edm_constant_applied_by_instrument",
        "finding.face_distance_discrepancy",
        "finding.leapfrog_sights_imbalanced",
        "finding.near_vertical_sight",
        "finding.no_atmospheric_data",
        "finding.open_traverse_unchecked",
        "finding.prism_constant_applied_by_instrument",
        "finding.relative_precision_beyond_tolerance",
        "finding.single_face_pointing",
        "finding.vertical_index_beyond_tolerance",
        "finding.vertical_index_drift",
        "finding.weak_intersection_geometry",
    }
)
