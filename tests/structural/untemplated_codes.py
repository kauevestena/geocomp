# SPDX-License-Identifier: GPL-2.0-or-later
"""The codes that still reach the user without a sentence: P12c-7's baseline.

NFR-006: an error message says what failed, why, and what the user can do. A
code with no template says none of that -- the user reads "GeoComp could not
complete the operation (data.some_code)" and nothing else. When P12c-7 first
counted, 457 of the codes GeoComp raises had no template; it wrote the 81 of
the engine package, where a failure is most often the user's input meeting
DynAdjust or RTKLIB, and froze the rest here. Its second pull request wrote the
28 of the file readers the algorithms use -- RINEX, field and levelling books
and their mappings, geoid grids, the tables export -- and its third the 67 of
the levelling and total-station techniques, which a user's observations reach;
its fourth the 51 of GNSS, gravimetry and integration, which finish the
techniques; its fifth the 61 of the adjustment, geodesy, statistics,
pre-analysis and the drawing of ellipses; and its sixth the 44 of the
instrument profiles, the report templates and the settings service.

The list may only shrink. ``tests/structural/test_message_templates.py`` fails
on a code raised without a template that is not listed here -- a new code
arrives with its words -- and on a listed code that has gained a template or is
no longer raised, so an entry cannot outlive its reason. Some are guards no
user input reaches (a matrix of the wrong shape passed between two functions);
those still need words, because a defect is exactly when they surface.

Grouped by the directory that raises each code first.
"""

from __future__ import annotations

UNTEMPLATED: frozenset[str] = frozenset(
    {
        # core/ (49)
        "data.basemap_catalogue_unreadable",
        "data.covariance_duplicate_labels",
        "data.covariance_label_count",
        "data.covariance_not_positive_semidefinite",
        "data.covariance_not_square",
        "data.covariance_not_symmetric",
        "data.covariance_unit_count",
        "data.geoid_grid_not_finite",
        "data.geoid_grid_too_small",
        "validation.approximate_without_strategy",
        "validation.atan2_at_origin",
        "validation.basemap_duplicate_id",
        "validation.basemap_not_configured",
        "validation.basemap_url_carries_a_credential",
        "validation.basemap_url_without_tile_tokens",
        "validation.basemap_without_attribution",
        "validation.basemap_without_id",
        "validation.basemap_without_url",
        "validation.basemap_zoom_range",
        "validation.compound_unit_not_supported",
        "validation.correlated_scalar_path",
        "validation.coverage_not_ordered",
        "validation.display_angle_format_unknown",
        "validation.display_decimals_out_of_range",
        "validation.display_distance_unit_unknown",
        "validation.division_by_zero",
        "validation.geoid_outside_coverage",
        "validation.geoid_without_id",
        "validation.geoid_without_sigma",
        "validation.height_conversion_unsupported",
        "validation.height_wrong_unit",
        "validation.hypot_at_origin",
        "validation.incompatible_height_types",
        "validation.incompatible_units",
        "validation.jacobian_not_2d",
        "validation.jacobian_shape_mismatch",
        "validation.log_of_non_positive",
        "validation.negative_variance",
        "validation.not_a_quantity",
        "validation.output_label_count",
        "validation.output_unit_count",
        "validation.power_of_dimensioned_quantity",
        "validation.printed_half_width_not_positive",
        "validation.relative_uncertainty_of_zero",
        "validation.rigorous_with_strategies",
        "validation.sqrt_at_zero",
        "validation.sqrt_of_negative",
        "validation.unknown_covariance_label",
        "validation.value_count_mismatch",
        # core/models/ (45)
        "data.active_observation_with_rejection",
        "data.antenna_height_unit",
        "data.baseline_frame_unknown",
        "data.cluster_duplicate_members",
        "data.cluster_size_mismatch",
        "data.cluster_without_members",
        "data.constrained_station_without_position",
        "data.duplicate_campaign",
        "data.duplicate_cluster",
        "data.duplicate_gnss_session",
        "data.duplicate_network",
        "data.duplicate_observation",
        "data.duplicate_station",
        "data.gnss_session_ends_before_it_starts",
        "data.gnss_session_without_id",
        "data.observation_arity",
        "data.observation_component_count",
        "data.observation_requires_cluster",
        "data.observation_setup_height_unit",
        "data.observation_type_ignores_setup_heights",
        "data.observation_value_not_a_quantity",
        "data.observation_value_unit",
        "data.station_without_id",
        "validation.adjusted_gravity_unit",
        "validation.constraint_unknown_components",
        "validation.constraint_without_components",
        "validation.constraint_without_position",
        "validation.epoch_instant_naive",
        "validation.epoch_not_finite",
        "validation.epoch_required",
        "validation.free_constraint_with_detail",
        "validation.gravity_constraint_unit",
        "validation.gravity_constraint_without_value",
        "validation.gravity_value_without_gravity_component",
        "validation.observation_is_not_scalar",
        "validation.position_component_count",
        "validation.position_component_not_a_quantity",
        "validation.position_component_unit",
        "validation.position_without_crs",
        "validation.schema_version_too_new",
        "validation.solution_without_crs",
        "validation.station_not_in_solution",
        "validation.unknown_position_component",
        "validation.weighted_constraint_without_covariance",
        "validation.weighted_gravity_constraint_without_uncertainty",
        # io/ (31) -- all in krumm.py and adjust.py, which read the RD-11 and ADJUST
        # reference corpora for the tests and scripts; no algorithm reaches them.
        "data.adjust_angle_out_of_range",
        "data.adjust_azimuths_unsupported",
        "data.adjust_cannot_express_observation",
        "data.adjust_control_without_covariance",
        "data.adjust_control_without_sigmas",
        "data.adjust_declared_counts_disagree",
        "data.adjust_fewer_stations_than_declared",
        "data.adjust_file_half_valued",
        "data.adjust_file_too_short",
        "data.adjust_header_not_five_counts",
        "data.adjust_header_not_integers",
        "data.adjust_not_a_number",
        "data.adjust_observation_row_unrecognised",
        "data.adjust_observation_station_unknown",
        "data.adjust_station_row_too_short",
        "data.krumm_angle_unreadable",
        "data.krumm_baseline_antenna_heights",
        "data.krumm_coordinate_row_too_short",
        "data.krumm_datum_token_unreadable",
        "data.krumm_datum_unknown",
        "data.krumm_dynamic_datum_unsupported",
        "data.krumm_free_datum_partial",
        "data.krumm_handler_unimplemented",
        "data.krumm_levelling_length_not_positive",
        "data.krumm_mixed_dimensionality",
        "data.krumm_observation_station_unknown",
        "data.krumm_row_too_short",
        "data.krumm_section_unknown",
        "data.krumm_section_unsupported",
        "data.krumm_setup_heights_incomplete",
        "data.krumm_value_not_a_number",
    }
)
