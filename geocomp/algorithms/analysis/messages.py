# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for the errors the analysis algorithms surface.

:mod:`geocomp.services.messages` deliberately does not grow into a catalogue of
every error in the project; each phase registers the templates for the errors it
can raise. These are phase P2's.

NFR-006 asks a message to say **what failed, why, and what the user can do about
it**. A template that only restates the code is not finished, and the third part
is the one usually missing: "the normal matrix is singular" is true and useless,
where "stations 7 and 8 are connected only by observations that do not determine
their height" can be acted on.

Importing this module registers the templates; :mod:`geocomp.algorithms.analysis`
imports it so that any algorithm in the package has them available.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

#: Code -> template. Keyed by the full namespaced code, and every interpolated
#: key is one the raising site actually passes -- a template naming a key that is
#: never supplied renders "(not set)" to the user.
TEMPLATES: dict[str, MessageTemplate] = {
    # -- reading the network document ------------------------------------
    "data.document_not_an_object": MessageTemplate(
        "This file does not hold a GeoComp network: its top level is %1, and a network "
        "document is a JSON object. Check that you chose the right file.",
        "received",
    ),
    "data.document_not_a_network": MessageTemplate(
        "This JSON file is not a GeoComp network document: it has no network identifier. "
        "Expected a network document, with its identifier and its list of stations.",
    ),
    "data.document_holds_several_networks": MessageTemplate(
        "This project file holds %1 networks, so GeoComp cannot tell which one you mean. "
        "Export the network you want to analyse and choose that file instead.",
        "received",
    ),
    "data.document_malformed_network": MessageTemplate(
        "This network document could not be read: %1. It may have been written by a "
        "different version of GeoComp, or edited by hand.",
        "received",
    ),
    "data.network_integrity": MessageTemplate(
        "The network '%1' is not internally consistent: %2 observation(s) or cluster(s) name "
        "something it does not have, or a cluster's covariance does not fit its members. Run "
        "Inspect network to see each problem.",
        "network",
        "count",
    ),
    # -- what the network is missing --------------------------------------
    "computation.no_active_observations": MessageTemplate(
        "The network '%1' has no active observations, so there is nothing to adjust. "
        "Observations marked as rejected do not take part; re-activate the ones you want "
        "to use.",
        "network",
    ),
    "computation.no_observations": MessageTemplate(
        "No observations were supplied; the adjustment needs at least one active observation.",
    ),
    "computation.no_planned_observations": MessageTemplate(
        "The planned network '%1' contains no observations, so there is no design to "
        "evaluate. Add the observations you intend to make, with their assumed precisions.",
        "network",
    ),
    "validation.no_estimable_parameters": MessageTemplate(
        "Every station in this network is held fixed, so there is nothing to estimate. Free at "
        "least one station, or one of its components.",
    ),
    "validation.missing_approximate_coordinates": MessageTemplate(
        "Station '%1' has no approximate %2, and the linearised adjustment needs a point to "
        "linearise about. Supply approximate coordinates, or generate them from the "
        "observations.",
        "station",
        "component",
    ),
    "validation.fixed_station_without_position": MessageTemplate(
        "Station '%1' is held fixed but carries no position, so there is no value to hold "
        "it at. Give it coordinates, or release the constraint.",
        "station",
    ),
    "validation.no_stations_for_datum": MessageTemplate(
        "No stations were given to define the datum on; give at least one estimated station.",
    ),
    "data.observation_without_uncertainty": MessageTemplate(
        "Observation '%1' carries no uncertainty, so it cannot be weighted. GeoComp does not "
        "invent a weight, because a fabricated one silently corrupts every statistic; give the "
        "observation its standard deviation.",
        "observation",
    ),
    "data.cluster_rows_mismatch": MessageTemplate(
        "Correlated cluster '%1' supplies %2 observation rows but a %3 covariance matrix. "
        "The two must agree, in the same order.",
        "cluster",
        "rows",
        "covariance",
    ),
    # -- observations the adjustment cannot use ---------------------------
    "validation.observation_type_not_supported": MessageTemplate(
        "Observation '%1' is of type %2, which the in-house adjustment does not implement. %3",
        "observation",
        "type",
        "expected",
    ),
    "validation.observation_wrong_dimensionality": MessageTemplate(
        "Observation '%1' of type %2 cannot contribute to a %3 adjustment. Choose a "
        "coordinate frame the observation can constrain, or exclude it.",
        "observation",
        "type",
        "frame",
    ),
    "validation.observation_not_a_gravity_type": MessageTemplate(
        "Observation '%1' is of type %2, which is not a gravity observation, so it cannot "
        "take part in a gravity adjustment.",
        "observation",
        "type",
    ),
    # -- the geometry itself ----------------------------------------------
    "computation.coincident_stations": MessageTemplate(
        "Observation '%1' connects stations that are at the same approximate position "
        "(%2), so its direction is undefined. Correct the approximate coordinates.",
        "observation",
        "stations",
    ),
    "computation.degenerate_zenith_angle": MessageTemplate(
        "Observation '%1' between %2 has no horizontal separation at the approximate "
        "coordinates, so the zenith angle cannot be linearised there. Correct the "
        "approximate coordinates.",
        "observation",
        "stations",
    ),
    # -- solving ----------------------------------------------------------
    "computation.rank_deficient_normal_matrix": MessageTemplate(
        "The network does not determine %1 combination(s) of unknowns: %2. Add "
        "observations that fix them, or define the datum with inner or minimum "
        "constraints so the remaining freedom is removed deliberately.",
        "deficiency",
        "undetermined",
    ),
    "computation.constrained_system_singular": MessageTemplate(
        "The datum constraints do not remove the network's remaining freedom (%1 "
        "constraint(s) applied). Check that the stations defining the datum are enough to "
        "fix it.",
        "constraints",
    ),
    "computation.adjustment_did_not_converge": MessageTemplate(
        "The adjustment of '%1' did not converge: after %2 iteration(s) the largest "
        "correction was still %3, against a threshold of %4. Approximate coordinates that "
        "are far from the truth are the usual cause; a blunder large enough to drag the "
        "solution is the other. No coordinates are returned, because iterate %2 of a "
        "diverging sequence is not a result.",
        "network",
        "iterations",
        "max_correction",
        "threshold",
    ),
    # -- importing a field book (P12c-6) -------------------------------------
    "validation.mapping_missing_required_fields": MessageTemplate(
        "The field mapping supplies no column for %1, which every import needs: at least the "
        "station and the two angles. Give a mapping that names them, or a field book whose "
        "header does.",
        "received",
    ),
    # -- scale (NFR-008) ----------------------------------------------------
    "computation.adjustment_needs_scipy": MessageTemplate(
        "This network is too large to adjust without SciPy: %1 observation rows and %2 "
        "unknowns would need about %3 MiB held densely, and this machine allows %4 MiB. "
        "Install SciPy into QGIS's Python and run it again; the sparse solver it provides "
        "adjusts 10,000 stations in a few hundred MiB. Beyond about 10,000 stations, adjust "
        "the network with DynAdjust's segmentation.",
        "rows",
        "parameters",
        "footprint_mib",
        "limit_mib",
    ),
    "computation.adjustment_too_large_for_dense": MessageTemplate(
        "This computation needs the whole network held densely, about %3 MiB for %1 "
        "observation rows and %2 unknowns, and this machine allows %4 MiB. Variance "
        "component estimation is such a computation: run the adjustment without it, or "
        "estimate the components on a part of the network.",
        "rows",
        "parameters",
        "footprint_mib",
        "limit_mib",
    ),
    "computation.sparse_solver_needs_scipy": MessageTemplate(
        "The sparse solver was asked for, but SciPy is not installed in QGIS's Python. "
        "Install SciPy, or let GeoComp choose the solver."
    ),
    "computation.variance_components_need_dense": MessageTemplate(
        "Variance components cannot be estimated with the sparse solver: the estimator "
        "reads the whole residual cofactor matrix, which that solver never forms. Let "
        "GeoComp choose the solver."
    ),
    "computation.adjustment_did_not_run": MessageTemplate(
        "The adjustment of '%1' produced no iterations at all. This is an internal error; "
        "please report it with the network that caused it.",
        "network",
    ),
    # -- the field book and its mapping (P12c-7) --------------------------------
    # Shared with the levelling book, whose mapping refuses the same things.
    "validation.field_book_not_found": MessageTemplate(
        "The field book '%1' could not be read. Choose an existing, readable CSV or .xlsx "
        "file.",
        "received",
    ),
    "data.coordinate_row_unreadable": MessageTemplate(
        "Row %2 of '%1' is not a station followed by its easting, northing and height, in "
        "metres. Correct the row, or remove it.",
        "path",
        "row",
    ),
    "data.coordinate_table_empty": MessageTemplate(
        "'%1' holds no station coordinates. Each row gives a station, then its easting, "
        "northing and height, in metres.",
        "path",
    ),
    "data.workbook_unreadable": MessageTemplate(
        "'%1' could not be read as an .xlsx workbook: it is damaged, or it has no "
        "worksheet. Save it again from the spreadsheet program, or export it as CSV.",
        "path",
    ),
    "validation.mapping_without_name": MessageTemplate(
        "The field mapping has no name. Give it one: a mapping is saved and reused by its "
        "name.",
    ),
    "validation.unknown_decimal_separator": MessageTemplate(
        "'%1' is not a decimal separator; use '.', ',' or 'auto'.",
        "received",
    ),
    "validation.negative_skip_rows": MessageTemplate(
        "The number of rows to skip cannot be negative (%1).",
        "received",
    ),
    "validation.duplicate_mapped_field": MessageTemplate(
        "Each field can be mapped once, and %1 is mapped more than once. Map each to a "
        "single column.",
        "received",
    ),
    "validation.mapping_without_field": MessageTemplate(
        "A column of the mapping names no field. Choose the field it fills, or remove it.",
    ),
    "validation.mapping_without_source": MessageTemplate(
        "The field '%1' has neither a source column nor a constant value. Choose a column, or "
        "give a value for every row.",
        "field",
    ),
    "validation.unknown_mapping_field": MessageTemplate(
        "The mapping names %1, which GeoComp does not know as a field-book field. Expected %2.",
        "received",
        "expected",
    ),
    # -- total-station readings, reductions and surveys (P12c-7) ----------------
    "validation.setup_without_station": MessageTemplate(
        "A setup names no station. Every setup needs the station the instrument occupied.",
    ),
    "validation.reading_without_target": MessageTemplate(
        "A reading names no target. Every reading needs the station or point it sighted.",
    ),
    "validation.non_positive_set_number": MessageTemplate(
        "The set number must be at least 1; %1 was given.",
        "received",
    ),
    "validation.reading_wrong_unit": MessageTemplate(
        "The %1 of a reading is in %2, where %3 was expected.",
        "parameter",
        "received",
        "expected",
    ),
    "validation.face_pair_wrong_faces": MessageTemplate(
        "A pair of readings has the faces %1, where face left and then face right were "
        "expected.",
        "received",
    ),
    "validation.face_pair_different_targets": MessageTemplate(
        "The two faces of a pair point at different targets (%1); both faces of a pair sight "
        "the same target.",
        "received",
    ),
    "validation.sight_wrong_unit": MessageTemplate(
        "The %1 of the sight to '%2' is in %3, where %4 was expected.",
        "parameter",
        "station",
        "received",
        "expected",
    ),
    "validation.atmosphere_wrong_unit": MessageTemplate(
        "The %1 of the atmosphere is in %2, where %3 was expected.",
        "parameter",
        "received",
        "expected",
    ),
    "validation.temperature_wrong_unit": MessageTemplate(
        "The temperature is in %1; the atmospheric correction takes kelvin.",
        "received",
    ),
    "validation.temperature_not_absolute": MessageTemplate(
        "%1 is not an absolute temperature: in kelvin it must be above zero. Check the "
        "temperature readings.",
        "received",
    ),
    "validation.humidity_out_of_range": MessageTemplate(
        "The relative humidity must lie between 0 and 1; %1 was given.",
        "received",
    ),
    "validation.non_positive_wavelength": MessageTemplate(
        "The EDM carrier wavelength must be positive, in micrometres; %1 was given. Check the "
        "instrument profile.",
        "received",
    ),
    "validation.reduction_wrong_unit": MessageTemplate(
        "The %1 of a reduction is in %2, where %3 was expected.",
        "parameter",
        "received",
        "expected",
    ),
    "validation.scale_factor_wrong_unit": MessageTemplate(
        "The point scale factor is in %1; it is a dimensionless number.",
        "received",
    ),
    "validation.height_below_earth_centre": MessageTemplate(
        "A height of %1 m is below the centre of the Earth, so the reduction is impossible. "
        "Check the station's height.",
        "received",
    ),
    # -- the grid reduction (FR-405, P12c-14) -----------------------------------
    "validation.grid_reduction_without_position": MessageTemplate(
        "Reducing distances to the grid needs an approximate position for every station a "
        "distance ends at, and these have none: %1. Give them approximate coordinates, or "
        "turn the reduction off.",
        "received",
    ),
    "validation.grid_reduction_without_height": MessageTemplate(
        "Reducing distances to the ellipsoid needs a height for every station a distance ends "
        "at, and the positions of these do not say what their height is measured from: %1. "
        "Give the heights, or turn the reduction off.",
        "received",
    ),
    "validation.grid_reduction_without_undulation": MessageTemplate(
        "The approximate heights of these stations are orthometric: %1. Reducing a distance "
        "to the ellipsoid needs the ellipsoidal height, so give the geoid undulation, or turn "
        "the reduction off.",
        "received",
    ),
    "validation.grid_reduction_of_clustered_distance": MessageTemplate(
        "These distances are part of a correlated cluster, whose covariance describes them "
        "as measured, and reducing them would leave it describing other values: %1. Reduce "
        "them before they are clustered, or turn the reduction off.",
        "received",
    ),
    "validation.correlation_out_of_range": MessageTemplate(
        "A correlation coefficient must lie between -1 and 1.",
    ),
    "validation.unsupported_observation_dimension": MessageTemplate(
        "A %1-dimensional adjustment is not supported; GeoComp adjusts in 1, 2 or 3 "
        "dimensions.",
        "received",
    ),
    "validation.traverse_without_legs": MessageTemplate(
        "The traverse has no legs. A traverse needs at least one leg between two stations.",
    ),
    "validation.connected_traverse_without_closing_point": MessageTemplate(
        "A connected traverse needs the known point it arrives at, and none was given.",
    ),
    "validation.leg_angle_wrong_unit": MessageTemplate(
        "The angle of the leg %1 is in %2; give it in radians.",
        "leg",
        "received",
    ),
    "validation.leg_distance_wrong_unit": MessageTemplate(
        "The distance of the leg %1 is in %2; give it in metres.",
        "leg",
        "received",
    ),
    "validation.resection_needs_three_points": MessageTemplate(
        "A resection needs at least three known points, and %1 were sighted: fewer cannot "
        "fix both a position and an orientation.",
        "received",
    ),
    "validation.resection_direction_to_unknown_point": MessageTemplate(
        "The resection sights %1, which have no known position. Every point sighted in a "
        "resection needs one.",
        "received",
    ),
    "computation.resection_on_a_known_point": MessageTemplate(
        "The resection's station falls on the known point '%1' it sights. The occupied "
        "station must be distinct from every point sighted.",
        "point",
    ),
    "computation.resection_indeterminate": MessageTemplate(
        "The resection cannot determine the station: its equations are singular, and the "
        "known points are not on a common circle with it. Check the directions for a "
        "blunder.",
    ),
    "computation.resection_did_not_converge": MessageTemplate(
        "The resection did not converge in %1 iterations. Check the approximate coordinates, "
        "and the directions for a blunder.",
        "iterations",
    ),
    "validation.intersection_needs_two_stations": MessageTemplate(
        "An intersection needs at least two stations sighting the target, and %1 did.",
        "received",
    ),
    "computation.intersection_on_a_station": MessageTemplate(
        "The intersected target falls on the station '%1' that sights it. The target must be "
        "distinct from every station sighting it.",
        "station",
    ),
    "computation.intersection_indeterminate": MessageTemplate(
        "The intersection cannot determine the point: the sightings are nearly parallel, and "
        "rays that do not cross determine nothing however many there are. Sight it from a "
        "station at a wider angle.",
    ),
    "computation.intersection_did_not_converge": MessageTemplate(
        "The intersection did not converge in %1 iterations. Check the azimuths for a "
        "blunder.",
        "iterations",
    ),
    # -- the adjustment, its weights and variance components (P12c-7) -----------
    "validation.direction_without_setup": MessageTemplate(
        "The direction '%1' belongs to no setup or direction set, so it has no orientation "
        "unknown and would be adjusted as an absolute azimuth. Give it its setup.",
        "observation",
    ),
    "validation.gnss_baseline_frame_mismatch": MessageTemplate(
        "The GNSS baseline '%1' is in %2, not in the network's own frame. Differenced against "
        "coordinates in another frame it would be wrong by a rotation, with nothing to say so; "
        "rotate it into the network's frame first.",
        "observation",
        "received",
    ),
    "validation.gravity_drift_times_missing": MessageTemplate(
        "The gravity observation '%1' has a drift term (%2) but not the times it depends on, so "
        "the drift cannot be evaluated. Build the gravity network from its readings, which "
        "records them.",
        "observation",
        "owner",
    ),
    "validation.gravity_drift_scale_invalid": MessageTemplate(
        "The drift time scale of the gravity observation '%1' must be a positive number of "
        "seconds; %2 was given.",
        "observation",
        "received",
    ),
    "computation.degenerate_sight": MessageTemplate(
        "The observation '%1' between %2 is a sight of zero length or exactly vertical, which "
        "determines no direction. Check the two stations' coordinates.",
        "observation",
        "stations",
    ),
    "validation.observation_type_not_geocentric": MessageTemplate(
        "The observation '%1' is a %2, which the geocentric adjustment cannot use; it takes %3.",
        "observation",
        "type",
        "expected",
    ),
    "validation.height_type_unsupported": MessageTemplate(
        "The height observation '%1' is %2; the geocentric adjustment takes ellipsoidal or "
        "orthometric heights.",
        "observation",
        "received",
    ),
    "validation.geocentric_frame_projected_position": MessageTemplate(
        "The station '%1' has a %2 position, which the geocentric adjustment cannot hold. Give "
        "it cartesian or geodetic coordinates.",
        "station",
        "received",
    ),
    "validation.geocentric_frame_partial_geodetic_constraint": MessageTemplate(
        "The station '%1' holds only %2 of its geodetic coordinates. Hold latitude, longitude "
        "and height together, or use a cartesian constraint; a height alone is entered as a "
        "height observation.",
        "station",
        "received",
    ),
    "validation.geocentric_frame_orthometric_constraint": MessageTemplate(
        "The station '%1' holds an orthometric height on its position, and the geocentric "
        "adjustment holds ellipsoidal heights. Enter the orthometric height as an "
        "orthometric-height observation, which the geoid relates to the frame.",
        "station",
    ),
    "validation.fixed_station_without_gravity": MessageTemplate(
        "The station '%1' is held fixed in gravity but has no gravity value to hold. Give its "
        "gravity value.",
        "station",
    ),
    "data.weighted_constraint_components_missing": MessageTemplate(
        "The weighted constraint on '%1' has a covariance over %2, which does not cover the "
        "constrained components %3.",
        "station",
        "received",
        "expected",
    ),
    "data.weighted_constraint_singular": MessageTemplate(
        "The weighted constraint on '%1' (%2) has a singular covariance: a direction in it is "
        "infinitely precise, which is a fixed constraint written as a weighted one. Fix those "
        "components instead, or correct the covariance.",
        "station",
        "components",
    ),
    "validation.undulation_without_position": MessageTemplate(
        "The station '%1' needs a geoid undulation and has no approximate position to look it "
        "up at. Give it one.",
        "station",
    ),
    "validation.unknown_defect_component": MessageTemplate(
        "'%1' is not a datum-defect component GeoComp knows.",
        "received",
    ),
    "validation.unknown_solver": MessageTemplate(
        "'%1' is not a solver; expected %2.",
        "received",
        "expected",
    ),
    "validation.not_a_difference_frame": MessageTemplate(
        "A difference network is one of heights or of gravity values; %1 is neither.",
        "received",
    ),
    "validation.known_value_for_unknown_station": MessageTemplate(
        "A known value is given for '%1', which is not a station of the network. Check its name.",
        "station",
    ),
    "validation.weighting_coefficient_not_positive": MessageTemplate(
        "The weighting coefficient must be positive; %1 was given. A zero would claim every "
        "difference is exact and give it an infinite weight.",
        "received",
    ),
    "validation.weighting_unsupported_unit": MessageTemplate(
        "Weighting by extent is defined for height and gravity differences, not for %1.",
        "received",
    ),
    "validation.weighting_unit_mismatch": MessageTemplate(
        "An observation in %1 cannot be weighted by a model for %2.",
        "received",
        "expected",
    ),
    "validation.negative_extent": MessageTemplate(
        "A %1 of %2 cannot weight an observation; the extent must not be negative.",
        "kind",
        "received",
    ),
    "validation.weighting_gave_zero_sigma": MessageTemplate(
        "An observation with a %1 of %2 gets no uncertainty and so an infinite weight, which "
        "would dominate the network. Check its extent.",
        "kind",
        "extent",
    ),
    "validation.variance_component_group_unknown": MessageTemplate(
        "'%1' is not a variance-component group of this adjustment; the groups are %2.",
        "received",
        "expected",
    ),
    "validation.variance_component_cluster_split": MessageTemplate(
        "The correlated cluster '%1' has members in different variance-component groups (%2), "
        "and a covariance cannot be rescaled by two factors at once. Put the whole cluster in "
        "one group.",
        "cluster",
        "received",
    ),
    "computation.variance_component_negative": MessageTemplate(
        "The variance factor of the group '%1' came out negative (%2): its residuals are "
        "smaller than its model allows. The group has too little redundancy, or its "
        "stochastic model is wrong in shape rather than in scale.",
        "group",
        "received",
    ),
    "computation.variance_component_unestimable": MessageTemplate(
        "The variance component of the group '%1' cannot be estimated: its redundancy is only "
        "%2, so its residuals barely depend on its own weights. Fix its weights, or merge it "
        "with another group.",
        "group",
        "received",
    ),
    "computation.variance_components_singular": MessageTemplate(
        "The residuals cannot tell the variance-component groups %1 apart. Merge them, or fix "
        "the weights of one.",
        "received",
    ),
    "computation.variance_components_not_converged": MessageTemplate(
        "The variance components did not settle in %1 iterations (last factors: %2). A group "
        "with little redundancy can oscillate; merge it with another, or fix its weights.",
        "iterations",
        "received",
    ),
    # -- geodesy: ellipsoids, frames, projections (P12c-7) -----------------------
    "computation.geodetic_angle_wrong_unit": MessageTemplate(
        "The %1 is in %2; give it in radians.",
        "component",
        "received",
    ),
    "computation.geodetic_length_wrong_unit": MessageTemplate(
        "The %1 is in %2; give it in metres.",
        "component",
        "received",
    ),
    "computation.cartesian_to_geodetic_degenerate": MessageTemplate(
        "The point %1 lies too near the centre of the Earth to have geodetic coordinates. Check "
        "its cartesian coordinates.",
        "received",
    ),
    "validation.ellipsoid_unknown": MessageTemplate(
        "'%1' is not an ellipsoid GeoComp knows; it knows %2.",
        "received",
        "expected",
    ),
    "validation.ellipsoid_semi_major_axis_not_positive": MessageTemplate(
        "The ellipsoid '%1' has a semi-major axis of %2; it must be positive.",
        "ellipsoid",
        "received",
    ),
    "validation.ellipsoid_inverse_flattening_invalid": MessageTemplate(
        "The ellipsoid '%1' has an inverse flattening of %2; it must be greater than 1, and a "
        "sphere's is infinite.",
        "ellipsoid",
        "received",
    ),
    "validation.frame_unknown": MessageTemplate(
        "'%1' is not a reference frame GeoComp holds transformations for; it holds %2. WGS 84 "
        "is not one: its realisations differ by decimetres, and the name does not say which.",
        "received",
        "expected",
    ),
    "validation.frame_transformation_unavailable": MessageTemplate(
        "GeoComp holds no transformation between the frames %1.",
        "received",
    ),
    "validation.transformation_time_specific": MessageTemplate(
        "The transformation %1 holds only at its own epoch, and the coordinates are at %2. "
        "Move them to that epoch with a velocity first.",
        "transformation",
        "received",
    ),
    "validation.utm_zone_out_of_range": MessageTemplate(
        "UTM zone %1 does not exist; the zones run from 1 to 60.",
        "received",
    ),
    "computation.inverse_projection_did_not_converge": MessageTemplate(
        "The grid coordinate %1 could not be converted back to latitude and longitude; it lies "
        "outside the projection's domain.",
        "received",
    ),
    "computation.projection_outside_domain": MessageTemplate(
        "The point is %1 degrees from the central meridian of %2, beyond where the projection "
        "is accurate; GeoComp refuses rather than give a coordinate with an error nobody can "
        "see. Use a projection centred nearer the point.",
        "received",
        "projection",
    ),
    "computation.point_scale_factor_undefined_at_the_pole": MessageTemplate(
        "The point scale factor is undefined at latitude %1 degrees, where a parallel has no "
        "length.",
        "received",
    ),
    # -- statistics and error ellipses (P12c-7) ----------------------------------
    "validation.probability_out_of_range": MessageTemplate(
        "A probability for %1 must lie between 0 and 1; %2 was given.",
        "operation",
        "received",
    ),
    "validation.degrees_of_freedom_out_of_range": MessageTemplate(
        "%1 needs at least 1 degree of freedom, and has %2: a network with no redundancy has no "
        "test to apply. Add observations.",
        "operation",
        "received",
    ),
    "validation.incomplete_gamma_domain": MessageTemplate(
        "The incomplete gamma function is undefined for a = %1, x = %2.",
        "a",
        "x",
    ),
    "validation.incomplete_beta_domain": MessageTemplate(
        "The incomplete beta function is undefined for a = %1, b = %2, x = %3.",
        "a",
        "b",
        "x",
    ),
    "validation.confidence_out_of_range": MessageTemplate(
        "The confidence level must lie strictly between 0 and 1; %1 was given.",
        "received",
    ),
    "validation.ellipse_wrong_dimension": MessageTemplate(
        "An error ellipse needs a 2 by 2 or 3 by 3 covariance block, and was given one of shape "
        "%1.",
        "shape",
    ),
    "validation.relative_ellipse_dimension_mismatch": MessageTemplate(
        "A relative ellipse needs the same number of components for both stations, and was "
        "given %1 and %2.",
        "first",
        "second",
    ),
    # -- drawing ellipses on the map (P12c-7) ------------------------------------
    "validation.ellipse_too_few_vertices": MessageTemplate(
        "An ellipse needs at least 8 vertices to be drawn as an ellipse; %1 was given.",
        "received",
    ),
    "validation.scale_reference_not_positive": MessageTemplate(
        "The scale reference must be a positive radius, in the map's units; %1 was given.",
        "received",
    ),
    "validation.extent_not_positive": MessageTemplate(
        "The map extent %1 has no area; it needs a positive width and height.",
        "received",
    ),
    "validation.target_fraction_out_of_range": MessageTemplate(
        "The ellipse size, as a fraction of the map extent, must be above 0 and at most 1; %1 "
        "was given.",
        "received",
    ),
    "validation.exaggeration_not_finite": MessageTemplate(
        "The exaggeration factor %1 is not finite; an infinite factor gives the ellipses no "
        "size.",
        "received",
    ),
    "validation.exaggeration_not_positive": MessageTemplate(
        "The ellipse exaggeration must be a positive, finite factor; %1 was given. Every drawn "
        "result states the factor it was drawn with.",
        "received",
    ),
    # -- the pre-analysis design (P12c-7) ----------------------------------------
    "geocomp.no_default_sigma": MessageTemplate(
        "GeoComp has no assumed precision for a planned %1, and will not invent one. State its "
        "precision.",
        "observation_type",
    ),
    "geocomp.station_without_id": MessageTemplate(
        "A planned station has no name; give it one.",
    ),
    "geocomp.duplicate_station": MessageTemplate(
        "Another planned station is already named '%1'; give this one a different name.",
        "station",
    ),
    "geocomp.observation_without_stations": MessageTemplate(
        "A planned observation names no stations; it connects two.",
    ),
    "geocomp.unknown_observation": MessageTemplate(
        "The design has no observation '%1'.",
        "observation",
    ),
    "geocomp.unknown_station": MessageTemplate(
        "The design has no station '%1'.",
        "station",
    ),
    # -- instrument profiles and the stochastic model (P12c-7) -----------------
    "validation.no_instrument_profile": MessageTemplate(
        "No instrument profile applies: none is named on the observation, and the library has "
        "no default. GeoComp does not invent instrument constants; give an Instrument profiles "
        "file, or name a profile.",
    ),
    "validation.no_level_profile": MessageTemplate(
        "No level profile applies: none is named on the line, and the library has no default. "
        "GeoComp does not invent instrument precisions; give an Instrument profiles file, or "
        "name a profile.",
    ),
    "validation.unknown_instrument_profile": MessageTemplate(
        "There is no instrument profile '%1'; expected %2.",
        "instrument",
        "expected",
    ),
    "validation.unknown_reflector_profile": MessageTemplate(
        "There is no reflector profile '%1'; expected %2.",
        "reflector",
        "expected",
    ),
    "validation.unknown_level_profile": MessageTemplate(
        "There is no level profile '%1'; expected %2.",
        "level",
        "expected",
    ),
    "validation.unknown_levelling_class": MessageTemplate(
        "There is no levelling class '%1'; expected %2.",
        "levelling_class",
        "expected",
    ),
    # -- the profile window (FR-069, P12c-16) ------------------------------------
    "data.profile_library_not_an_object": MessageTemplate(
        "%1 holds JSON, but not a profile library: a library is an object with lists of "
        "instruments, reflectors, levels and gravimeters.",
        "path",
    ),
    "validation.duplicate_profile": MessageTemplate(
        "A profile with the id '%1' is already in the library. Choose another id.",
        "received",
    ),
    "validation.unknown_profile": MessageTemplate(
        "The library has no profile with the id '%1'.",
        "received",
    ),
    "validation.profile_value_not_a_number": MessageTemplate(
        "The value given for %1 is not a number: '%2'. Enter a number, with a point or "
        "a comma for the decimals.",
        "parameter",
        "received",
    ),
    "validation.duplicate_instrument_profile": MessageTemplate(
        "Two instrument profiles share the id '%1'. Rename or replace one of them.",
        "instrument",
    ),
    "validation.duplicate_reflector_profile": MessageTemplate(
        "Two reflector profiles share the id '%1'. Rename or replace one of them.",
        "reflector",
    ),
    "validation.duplicate_level_profile": MessageTemplate(
        "Two level profiles share the id '%1'. Rename or replace one of them.",
        "level",
    ),
    "validation.duplicate_levelling_class": MessageTemplate(
        "Two levelling classes share the id '%1'. Rename or replace one of them.",
        "levelling_class",
    ),
    "validation.duplicate_gravimeter_profile": MessageTemplate(
        "Two gravimeter profiles share the id '%1'. Rename or replace one of them.",
        "gravimeter",
    ),
    "validation.profile_wrong_unit": MessageTemplate(
        "The %1 of an instrument profile is in %2, where %3 was expected.",
        "parameter",
        "received",
        "expected",
    ),
    "validation.edm_specification_negative": MessageTemplate(
        "The EDM %1 is %2; a precision cannot be negative.",
        "parameter",
        "received",
    ),
    "validation.instrument_sigma_negative": MessageTemplate(
        "The %2 of the instrument '%1' is %3; a standard deviation cannot be negative.",
        "instrument",
        "parameter",
        "received",
    ),
    "validation.cyclic_error_without_wavelength": MessageTemplate(
        "The instrument profile '%1' gives a cyclic-error amplitude without its wavelength; the "
        "correction is periodic in the distance and means nothing without one.",
        "instrument",
    ),
    "validation.non_positive_set_count": MessageTemplate(
        "The number of sets must be at least 1; %1 was given.",
        "received",
    ),
    "validation.unknown_observation_kind": MessageTemplate(
        "'%1' is not a kind of observation GeoComp weights; expected %2.",
        "kind",
        "expected",
    ),
    "validation.missing_stochastic_model": MessageTemplate(
        "The %2 '%1' has no standard deviation: none was imported, no instrument profile gives "
        "one, and no default is set. GeoComp does not invent one, because a fabricated weight "
        "corrupts every statistic computed from it. Set the default in Global Settings, under "
        "Stochastic model, or give an instrument profile.",
        "observation",
        "kind",
    ),
    "validation.default_sigma_negative": MessageTemplate(
        "The default standard deviation for %1 is %2; it cannot be negative. Correct it in "
        "Global Settings, under Stochastic model.",
        "kind",
        "received",
    ),
    "validation.stated_sigma_negative": MessageTemplate(
        "The observation '%1' states a standard deviation of %2; it cannot be negative.",
        "observation",
        "received",
    ),
    # -- the data model: stations, observations, clusters, positions (P12c-7) ---
    "data.station_without_id": MessageTemplate(
        "A station has no id; observations and solutions refer to a station by it. Give every "
        "station one.",
    ),
    "data.constrained_station_without_position": MessageTemplate(
        "The station '%1' is constrained but has no coordinates to be held at. Give them, or "
        "make the station free.",
        "station",
    ),
    "data.duplicate_station": MessageTemplate(
        "The network '%2' has two stations with the id '%1'. Give each station its own id, or "
        "merge the two.",
        "station",
        "network",
    ),
    "data.duplicate_observation": MessageTemplate(
        "The network '%2' has two observations with the id '%1'. Give each observation its "
        "own id.",
        "observation",
        "network",
    ),
    "data.duplicate_cluster": MessageTemplate(
        "The network '%2' has two clusters with the id '%1'. Give each cluster its own id.",
        "cluster",
        "network",
    ),
    "validation.free_constraint_with_detail": MessageTemplate(
        "A free station carries a position, components or a gravity value to be held at. "
        "Remove them, or constrain the station as fixed or weighted.",
    ),
    "validation.constraint_without_position": MessageTemplate(
        "A station constrained as %1 has no coordinates to be held at. Give them, or make the "
        "station free.",
        "mode",
    ),
    "validation.constraint_without_components": MessageTemplate(
        "A station constrained as %1 does not say which components the constraint holds. Name "
        "them, such as height, or make the station free.",
        "mode",
    ),
    "validation.constraint_unknown_components": MessageTemplate(
        "A constraint names components its position does not have (%1); expected among %2.",
        "received",
        "expected",
    ),
    "validation.weighted_constraint_without_covariance": MessageTemplate(
        "A weighted constraint has no covariance. Without an uncertainty it is a fixed "
        "constraint under another name: give its covariance, or make it fixed.",
    ),
    "validation.gravity_value_without_gravity_component": MessageTemplate(
        "A constraint gives a gravity value but does not hold gravity, so the value would be "
        "silently ignored. Add gravity to its components, or remove the value.",
    ),
    "validation.gravity_constraint_without_value": MessageTemplate(
        "A station's gravity is constrained as %1, but no known gravity is given. Give it in "
        "m/s², or remove gravity from the constrained components.",
        "mode",
    ),
    "validation.gravity_constraint_unit": MessageTemplate(
        "A gravity constraint is in %1, where %2 was expected.",
        "received",
        "expected",
    ),
    "validation.weighted_gravity_constraint_without_uncertainty": MessageTemplate(
        "A weighted gravity constraint has no variance. Without an uncertainty it is a fixed "
        "constraint under another name: give its variance, or make it fixed.",
    ),
    "data.observation_arity": MessageTemplate(
        "The observation '%1' is a %2 and joins %3 station(s), where that type joins %4.",
        "observation",
        "type",
        "received",
        "expected",
    ),
    "data.observation_component_count": MessageTemplate(
        "The observation '%1' is a %2 with %3 value(s), where that type has %4.",
        "observation",
        "type",
        "received",
        "expected",
    ),
    "data.observation_value_not_a_quantity": MessageTemplate(
        "The %2 of the observation '%1' carries no uncertainty. Every observation in GeoComp "
        "carries its standard deviation; give one.",
        "observation",
        "component",
    ),
    "data.observation_value_unit": MessageTemplate(
        "The %2 of the observation '%1' is in %3, where %4 was expected.",
        "observation",
        "component",
        "received",
        "expected",
    ),
    "data.observation_requires_cluster": MessageTemplate(
        "The observation '%1' is a %2, whose components are correlated, but it belongs to no "
        "cluster. Treating them as independent falsifies the adjustment; give it the cluster "
        "that carries its covariance.",
        "observation",
        "type",
    ),
    "data.active_observation_with_rejection": MessageTemplate(
        "The observation '%1' is active but carries a rejection record. Mark it rejected, or "
        "remove the record.",
        "observation",
    ),
    "data.observation_setup_height_unit": MessageTemplate(
        "The %2 of the observation '%1' is %3, where a length in metres was expected.",
        "observation",
        "field",
        "received",
    ),
    "data.observation_type_ignores_setup_heights": MessageTemplate(
        "The observation '%1' is a %2 and gives %3, which that type does not use. GeoComp "
        "would ignore it, and an ignored instrument height is a metre-scale error that looks "
        "like nothing. Remove it, or use %4.",
        "observation",
        "type",
        "field",
        "expected",
    ),
    "validation.observation_is_not_scalar": MessageTemplate(
        "The observation '%1' has %2 components, where one was expected.",
        "observation",
        "components",
    ),
    "data.baseline_frame_unknown": MessageTemplate(
        "The baseline '%1' records its frame as '%2', which GeoComp does not know; expected %3.",
        "observation",
        "received",
        "expected",
    ),
    "data.cluster_without_members": MessageTemplate(
        "The cluster '%1' has no member observations. Give it its observations, or remove it.",
        "cluster",
    ),
    "data.cluster_duplicate_members": MessageTemplate(
        "The cluster '%1' lists an observation twice. Each member appears once, in the order "
        "of the covariance.",
        "cluster",
    ),
    "data.cluster_size_mismatch": MessageTemplate(
        "The cluster '%1' has %2 observation(s) and a covariance of size %3, which does not "
        "cover every component of every member. A GNSS baseline contributes three rows, so the "
        "size is a whole multiple of the number of members.",
        "cluster",
        "observations",
        "covariance",
    ),
    "validation.position_component_count": MessageTemplate(
        "A position has %1 component(s), where three were expected.",
        "received",
    ),
    "validation.position_component_not_a_quantity": MessageTemplate(
        "The %1 of a position carries no uncertainty (it is a %2). Every coordinate in GeoComp "
        "carries its standard deviation; give one.",
        "component",
        "received",
    ),
    "validation.position_component_unit": MessageTemplate(
        "The %1 of a position is in %2, where %3 was expected.",
        "component",
        "received",
        "expected",
    ),
    "validation.position_without_crs": MessageTemplate(
        "A position has no coordinate reference system, and GeoComp does not infer one. Give "
        "it, such as EPSG:4674.",
    ),
    "validation.unknown_position_component": MessageTemplate(
        "A position has no component '%1'; expected %2.",
        "component",
        "expected",
    ),
    "validation.incompatible_height_types": MessageTemplate(
        "Heights of different types (%1) cannot be combined without a geoid model: the result "
        "would be wrong by the geoid undulation and still look reasonable. Give a geoid model, "
        "or heights of one type.",
        "received",
    ),
    # -- epochs and solutions (P12c-7) -----------------------------------------
    "validation.epoch_not_finite": MessageTemplate(
        "The epoch %1 is not a finite decimal year; give one such as 2024.5.",
        "received",
    ),
    "validation.epoch_instant_naive": MessageTemplate(
        "A time was given without its time zone. GeoComp stores times in UTC and will not guess "
        "the zone; give the time with its offset, such as +00:00.",
    ),
    "validation.epoch_required": MessageTemplate(
        "'%2' has no reference epoch, which is needed to %1. GeoComp will not assume one, "
        "because an assumed epoch produces a confidently wrong displacement; give the epoch.",
        "operation",
        "subject",
    ),
    "validation.adjusted_gravity_unit": MessageTemplate(
        "The adjusted gravity of the station '%1' is in %2, where %3 was expected.",
        "station",
        "received",
        "expected",
    ),
    "validation.solution_without_crs": MessageTemplate(
        "The solution '%1' has no coordinate reference system, and GeoComp does not infer one. "
        "Give the solution its CRS.",
        "solution",
    ),
    "validation.station_not_in_solution": MessageTemplate(
        "The solution '%1' has no station '%2'. Check the station's id, and that this is the "
        "solution that adjusted it.",
        "solution",
        "station",
    ),
    # -- uncertainties and covariance matrices (P12c-7) --------------------------
    "data.covariance_not_square": MessageTemplate(
        "A covariance matrix has the shape %1; a covariance matrix is square. Check the matrix "
        "the observations or the solution carry.",
        "shape",
    ),
    "data.covariance_label_count": MessageTemplate(
        "A covariance matrix of size %2 names %1 component(s); it must name one per row.",
        "labels",
        "size",
    ),
    "data.covariance_duplicate_labels": MessageTemplate(
        "A covariance matrix names the same component twice, so its rows cannot be told apart. "
        "Give each component its own name.",
    ),
    "data.covariance_unit_count": MessageTemplate(
        "A covariance matrix of size %2 gives %1 unit(s); it must give one per row.",
        "units",
        "size",
    ),
    "data.covariance_not_symmetric": MessageTemplate(
        "A covariance matrix is not symmetric: the entries for %2 differ by %1 from their mirror "
        "images. A covariance matrix is symmetric, so the matrix was written or read wrongly.",
        "asymmetry",
        "at",
    ),
    "data.covariance_not_positive_semidefinite": MessageTemplate(
        "A covariance matrix is not positive semi-definite: its smallest eigenvalue is %1. No set "
        "of uncertainties produces such a matrix, so it was mistyped, truncated, or assembled "
        "from parts that do not belong together.",
        "smallest_eigenvalue",
    ),
    "validation.unknown_covariance_label": MessageTemplate(
        "A covariance matrix has no component '%1'.",
        "label",
    ),
    "validation.value_count_mismatch": MessageTemplate(
        "%1 value(s) were given for a covariance matrix over %2 components; give one per "
        "component.",
        "received",
        "expected",
    ),
    "validation.negative_variance": MessageTemplate(
        "The value %1 has a variance of %2; a variance cannot be negative.",
        "value",
        "variance",
    ),
    "validation.rigorous_with_strategies": MessageTemplate(
        "A value is marked rigorous but names approximations (%1). A value that used an "
        "approximation is approximate; this is an internal error, please report it.",
        "strategies",
    ),
    "validation.approximate_without_strategy": MessageTemplate(
        "The value %1 is marked approximate without saying how its uncertainty was estimated. "
        "This is an internal error; please report it.",
        "value",
    ),
    "validation.relative_uncertainty_of_zero": MessageTemplate(
        "A relative uncertainty was asked of a value of zero, where it is undefined.",
    ),
    "validation.correlated_scalar_path": MessageTemplate(
        "Two correlated values were combined (%1) as if they were independent, which would "
        "misstate the uncertainty of the result. This is an internal error; please report it "
        "with the data that caused it.",
        "operation",
    ),
    "validation.incompatible_units": MessageTemplate(
        "%1 cannot be applied to values in %2: the units do not fit the operation.",
        "operation",
        "received",
    ),
    "validation.compound_unit_not_supported": MessageTemplate(
        "Values in %2 cannot be combined (%1): the result would need a compound unit, which "
        "GeoComp does not track.",
        "operation",
        "received",
    ),
    "validation.not_a_quantity": MessageTemplate(
        "A %1 was given where a number or a value with its uncertainty was expected.",
        "received",
    ),
    "validation.division_by_zero": MessageTemplate(
        "A value (%1) was divided by zero. Check the input for a zero where a divisor is "
        "expected, such as a zero distance.",
        "numerator",
    ),
    "validation.power_of_dimensioned_quantity": MessageTemplate(
        "A value in %1 cannot be raised to the power %2: the result would need a compound unit, "
        "which GeoComp does not track.",
        "unit",
        "exponent",
    ),
    "validation.log_of_non_positive": MessageTemplate(
        "The logarithm of %1 is undefined; it needs a positive value.",
        "value",
    ),
    "validation.sqrt_of_negative": MessageTemplate(
        "The square root of %1 is undefined; it needs a value that is not negative.",
        "value",
    ),
    "validation.sqrt_at_zero": MessageTemplate(
        "The uncertainty of a square root cannot be propagated at zero, where its derivative is "
        "infinite.",
    ),
    "validation.atan2_at_origin": MessageTemplate(
        "A direction was asked of two coincident points, where it is undefined. Check for two "
        "stations with the same coordinates.",
    ),
    "validation.hypot_at_origin": MessageTemplate(
        "The uncertainty of a length cannot be propagated between two coincident points. Check "
        "for two stations with the same coordinates.",
    ),
    "validation.printed_half_width_not_positive": MessageTemplate(
        "The rounding of a printed covariance matrix was given as %1; it is half the place value "
        "of the last digit printed, which is positive. This is an internal error; please report "
        "it.",
        "half_width",
    ),
    "validation.jacobian_not_2d": MessageTemplate(
        "A Jacobian of shape %1 was given to propagate an uncertainty; it must be a matrix. This "
        "is an internal error; please report it.",
        "shape",
    ),
    "validation.jacobian_shape_mismatch": MessageTemplate(
        "A Jacobian of shape %1 cannot propagate a covariance matrix of size %2: it needs one "
        "column per component. This is an internal error; please report it.",
        "jacobian",
        "covariance",
    ),
    "validation.output_label_count": MessageTemplate(
        "A propagation produces %1 value(s) but names %2. This is an internal error; please "
        "report it.",
        "rows",
        "labels",
    ),
    "validation.output_unit_count": MessageTemplate(
        "A propagation gives %1 unit(s) for %2 named value(s). This is an internal error; please "
        "report it.",
        "units",
        "labels",
    ),
    # -- the reference-corpus readers: ADJUST and Krumm's examples (P12c-7) -----
    # Only the validation tests and scripts/ read these files, but a refusal is
    # read by whoever runs them, so it says what is wrong as any other does.
    "data.adjust_file_too_short": MessageTemplate(
        "'%1' has %2 line(s); an Adjust file starts with a title line and a counts line.",
        "path",
        "received",
    ),
    "data.adjust_header_not_five_counts": MessageTemplate(
        "The counts line of '%1' reads '%2'; an Adjust file gives five counts: distances, "
        "angles, azimuths, control stations and total stations.",
        "path",
        "received",
    ),
    "data.adjust_header_not_integers": MessageTemplate(
        "The counts line of '%1' reads '%2', which is not five whole numbers.",
        "path",
        "received",
    ),
    "data.adjust_azimuths_unsupported": MessageTemplate(
        "'%1' declares %2 azimuth observation(s), which GeoComp does not read: no example of an "
        "azimuth row exists to check its layout against, and a guessed layout reads a "
        "plausible wrong number.",
        "path",
        "received",
    ),
    "data.adjust_fewer_stations_than_declared": MessageTemplate(
        "'%1' has %2 line(s) after its header, fewer than the %3 stations it declares.",
        "path",
        "received",
        "expected",
    ),
    "data.adjust_file_half_valued": MessageTemplate(
        "'%1' gives values for %2 of its observation rows and not for the others. A file is "
        "either a plan, with no values, or a set of measurements, with all of them.",
        "path",
        "received",
    ),
    "data.adjust_declared_counts_disagree": MessageTemplate(
        "The counts line of '%1' declares %2, but the file holds %3. The counts are the "
        "format's own check, so GeoComp cannot tell which was intended.",
        "path",
        "declared",
        "found",
    ),
    "data.adjust_cannot_express_observation": MessageTemplate(
        "The network cannot be written as the Adjust file '%1': it has observations of type "
        "%2, and the format holds only horizontal distances and horizontal angles. Written "
        "without them, the file would be a different network.",
        "path",
        "received",
    ),
    "data.adjust_not_a_number": MessageTemplate(
        "In '%1', the %2 '%3' is not a number, on the line: %4",
        "path",
        "field",
        "received",
        "line",
    ),
    "data.adjust_station_row_too_short": MessageTemplate(
        "A station row of '%1' is too short; it gives a name and two coordinates: %2",
        "path",
        "line",
    ),
    "data.adjust_observation_station_unknown": MessageTemplate(
        "An observation row of '%1' names stations that are not in the coordinate block (%3): "
        "%2",
        "path",
        "line",
        "received",
    ),
    "data.adjust_control_without_sigmas": MessageTemplate(
        "The control station '%2' in '%1' gives no standard deviations. A control station in "
        "this format is weighted, not held, so two standard deviations follow its "
        "coordinates: %3",
        "path",
        "station",
        "line",
    ),
    "data.adjust_observation_row_unrecognised": MessageTemplate(
        "An observation row of '%1' has %3 value(s), which is neither a distance (2 or 4) nor "
        "an angle (3 or 7): %2",
        "path",
        "line",
        "received",
    ),
    "data.adjust_control_without_covariance": MessageTemplate(
        "The station '%2' cannot be written to '%1' as control: the format gives a control "
        "station two standard deviations and has no way to say it is held exactly. Give it a "
        "weighted constraint with its covariance.",
        "path",
        "station",
    ),
    "data.adjust_angle_out_of_range": MessageTemplate(
        "An angle in '%1' has minutes or seconds of 60 or more (%3): %2",
        "path",
        "line",
        "received",
    ),
    "data.krumm_angle_unreadable": MessageTemplate(
        "'%1' is not an angle in degrees, minutes and seconds, such as 12°34'56\", on the "
        "line: %2",
        "received",
        "line",
    ),
    "data.krumm_value_not_a_number": MessageTemplate(
        "'%1' is not a number, on the line: %2",
        "received",
        "line",
    ),
    "data.krumm_coordinate_row_too_short": MessageTemplate(
        "A coordinate row is too short: %1",
        "line",
    ),
    "data.krumm_row_too_short": MessageTemplate(
        "A row of the %1 section has %3 value(s), where %2 are needed: %4",
        "section",
        "expected",
        "received",
        "line",
    ),
    "data.krumm_setup_heights_incomplete": MessageTemplate(
        "A row of the %1 section gives one setup height without the other (%3); give "
        "instrument and target heights together, or neither: %2",
        "section",
        "line",
        "received",
    ),
    "data.krumm_baseline_antenna_heights": MessageTemplate(
        "A baseline states antenna heights (%2). Reducing it to the marks needs each mark's "
        "vertical, which this file does not give: %1",
        "line",
        "received",
    ),
    "data.krumm_levelling_length_not_positive": MessageTemplate(
        "'%1' is not a positive line length in metres; the length weights the levelled line.",
        "received",
    ),
    "data.krumm_section_unknown": MessageTemplate(
        "'%2' has a section %1 that GeoComp does not know.",
        "section",
        "path",
    ),
    "data.krumm_section_unsupported": MessageTemplate(
        "The section %1 of '%2' holds %3. GeoComp reads none of the file rather than read it "
        "without that section: without one of its observations it would be a different "
        "example.",
        "section",
        "path",
        "reason",
    ),
    "data.krumm_handler_unimplemented": MessageTemplate(
        "The section %1 is listed as read but has no reader. This is an internal error; "
        "please report it.",
        "handler",
    ),
    "data.krumm_datum_unknown": MessageTemplate(
        "'%1' is not a datum GeoComp reads; expected %2.",
        "received",
        "expected",
    ),
    "data.krumm_dynamic_datum_unsupported": MessageTemplate(
        "'%1' has a dynamic datum, which weights the held coordinates by a covariance matrix. "
        "GeoComp does not read it: reading it as fixed would claim a certainty the example "
        "does not.",
        "path",
    ),
    "data.krumm_free_datum_partial": MessageTemplate(
        "The free datum of '%1' names different components for different stations (%2); an "
        "inner constraint names the same components for every station.",
        "path",
        "received",
    ),
    "data.krumm_datum_token_unreadable": MessageTemplate(
        "'%1' in the datum section is neither a station nor an axis letter and a station, such "
        "as xA.",
        "received",
    ),
    "data.krumm_mixed_dimensionality": MessageTemplate(
        "No one dimension of adjustment, 1D, 2D or 3D, takes every observation of the network "
        "'%1'.",
        "network",
    ),
    "data.krumm_observation_station_unknown": MessageTemplate(
        "'%1' observes stations that have no approximate coordinates (%2). An angle or azimuth "
        "to such a point defines a direction, not a position; reduce it before the network is "
        "adjusted.",
        "path",
        "received",
    ),
    # -- a field book's rows (P12c-8) ---------------------------------------------
    # A row the reader could not understand is reported as a finding, worded by
    # "finding.field_book_row_refused" with one of these as its reason.
    "data.missing_station": MessageTemplate(
        "no occupied station is given.",
    ),
    "data.missing_target": MessageTemplate(
        "no station is given for '%1', so the pointing has no target.",
        "field",
    ),
    "data.missing_angle": MessageTemplate(
        "the angle '%1' is empty.",
        "field",
    ),
    "data.unparseable_number": MessageTemplate(
        "'%2', given for '%1', is not a number.",
        "field",
        "received",
    ),
    "data.unparseable_angle": MessageTemplate(
        "'%2', given for '%1', is not an angle.",
        "field",
        "received",
    ),
    "data.unparseable_set_number": MessageTemplate(
        "the set number '%1' is not a whole number.",
        "received",
    ),
    "data.sexagesimal_out_of_range": MessageTemplate(
        "'%1' reads %2, but minutes and seconds must be below 60. The columns are probably in "
        "the wrong order, or the angle is already decimal.",
        "field",
        "received",
    ),
    "data.unknown_face_value": MessageTemplate(
        "'%1' is not one of the face values the mapping knows (%2).",
        "received",
        "expected",
    ),
    "data.unknown_sighted_value": MessageTemplate(
        "'%1' is not one of the sighted values the mapping knows (%2).",
        "received",
        "expected",
    ),
    # -- findings: the field book, its mapping and pre-processing (P12c-8) -----
    "finding.field_book_row_refused": MessageTemplate(
        "Row %1: %2",
        "row",
        "reason",
    ),
    "finding.required_field_unmapped": MessageTemplate(
        "Nothing supplies '%1', and without it there is no observation to import.",
        "field",
    ),
    "finding.column_assigned_twice": MessageTemplate(
        "The column '%1' is assigned to %2. One column cannot be two fields, and importing it "
        "as both would count the measurement twice.",
        "column",
        "fields",
    ),
    "finding.column_unmapped": MessageTemplate(
        "The column '%1' is not mapped to anything and will be ignored.",
        "column",
    ),
    "finding.mapped_column_absent": MessageTemplate(
        "The mapping expects a column '%1', which this file does not have. A mapping saved for "
        "one export layout does not fit another.",
        "column",
    ),
    "finding.inconsistent_instrument_height": MessageTemplate(
        "Station %1 records %2 different instrument heights. The first was used; check the "
        "field book.",
        "station",
        "count",
    ),
    "finding.missing_instrument_height": MessageTemplate(
        "Station %1 records no instrument height. Zero was assumed, which is right only for a "
        "leap-frog setup.",
        "station",
    ),
    "finding.repeated_face": MessageTemplate(
        "Row %1: a second pointing to %2 on the same face, in set %3. The first was kept; give "
        "the repetition its own set number to use both.",
        "row",
        "target",
        "set",
    ),
    "finding.rejected_in_preprocessing": MessageTemplate(
        "The pointing to %1 was rejected during pre-processing and is not used here.",
        "target",
    ),
    # -- findings: inspecting a network (P12c-8) -----------------------------------
    "finding.observation_names_unknown_station": MessageTemplate(
        "The observation %1 names the station %2, which the network does not have.",
        "observation",
        "station",
    ),
    "finding.observation_names_unknown_cluster": MessageTemplate(
        "The observation %1 names the cluster %2, which the network does not have.",
        "observation",
        "cluster",
    ),
    "finding.cluster_names_unknown_observation": MessageTemplate(
        "The cluster %1 lists the observation %2, which the network does not have.",
        "cluster",
        "observation",
    ),
    "finding.cluster_covariance_wrong_size": MessageTemplate(
        "The cluster %1 carries a covariance of size %2 for members with %3 components in "
        "all; it needs one row per component.",
        "cluster",
        "size",
        "components",
    ),
    "finding.unsupported_observation_type": MessageTemplate(
        "The observation %1 is a %2, which GeoComp's own adjustment does not yet implement.",
        "observation",
        "type",
    ),
    "finding.wrong_dimensionality": MessageTemplate(
        "The observation %1, a %2, cannot contribute to a %3D adjustment.",
        "observation",
        "type",
        "dimension",
    ),
    "finding.network_not_connected": MessageTemplate(
        "The network falls into %1 disconnected parts. Each has its own datum, and they cannot "
        "be adjusted together.",
        "parts",
    ),
    "finding.isolated_stations": MessageTemplate(
        "%1 station(s) take part in no active observation and cannot be determined: %2.",
        "count",
        "stations",
    ),
    "finding.insufficient_observations": MessageTemplate(
        "Station %1 appears in only %2 observation component(s), but a %3D position needs at "
        "least %4.",
        "station",
        "count",
        "dimension",
        "needed",
    ),
    "finding.repeated_observations": MessageTemplate(
        "%1 observations of type %2 between %3: %4. Repeated measurements are expected; a "
        "duplicated import is not.",
        "count",
        "type",
        "stations",
        "observations",
    ),
    "finding.missing_approximate_coordinates": MessageTemplate(
        "%1 station(s) have no approximate position: %2. The linearised model needs a point "
        "to linearise about; supply them, or generate them from the observations.",
        "count",
        "stations",
    ),
    "finding.no_active_observations": MessageTemplate(
        "The network has no active observations, so there is nothing to adjust.",
    ),
    # -- findings: the pre-analysis design (P12c-8) --------------------------------
    "finding.design_without_stations": MessageTemplate(
        "The design has no stations yet; add one to begin.",
    ),
    "finding.design_without_observations": MessageTemplate(
        "The design has stations but no planned observations, so there is nothing to "
        "evaluate. Connect two stations to begin.",
    ),
    "finding.design_not_evaluable": MessageTemplate(
        "The design cannot be evaluated: %1",
        "reason",
    ),
    "finding.design_without_redundancy": MessageTemplate(
        "The design has no redundancy, so nothing in it can be checked. A blunder anywhere "
        "would be invisible and would pass into the coordinates unaltered.",
    ),
    "finding.design_misses_tolerance": MessageTemplate(
        "Station %1 is expected to reach %2 mm, against a required %3 mm.",
        "station",
        "expected",
        "required",
    ),
    "finding.planned_observation_uncheckable": MessageTemplate(
        "The planned observation %1 would be uncheckable: no blunder in it could be detected "
        "at all.",
        "observation",
    ),
    # -- what a total-station reduction or survey reports (P12c-8) -------------
    "finding.near_vertical_sight": MessageTemplate(
        "The sight to %1 is within one degree of vertical, where the horizontal circle reading "
        "carries almost no directional information and the trunnion-tilt correction is "
        "unbounded. It was not applied.",
        "target",
    ),
    "finding.edm_constant_applied_by_instrument": MessageTemplate(
        "The instrument %1 applies its additive constant internally, so GeoComp did not apply "
        "it again.",
        "instrument",
    ),
    "finding.prism_constant_applied_by_instrument": MessageTemplate(
        "The constant of the reflector %1 is applied by the instrument, so GeoComp did not "
        "apply it again.",
        "reflector",
    ),
    "finding.collimation_beyond_tolerance": MessageTemplate(
        "The face pair to %1 implies a horizontal collimation of %2 arcsec, beyond the %3 "
        "arcsec tolerance. The pair still cancels it; a value this large means the instrument "
        "needs adjustment, or the pointings were not to the same target.",
        "target",
        "collimation",
        "tolerance",
    ),
    "finding.vertical_index_beyond_tolerance": MessageTemplate(
        "The face pair to %1 implies a vertical index error of %2 arcsec, beyond the %3 arcsec "
        "tolerance.",
        "target",
        "index",
        "tolerance",
    ),
    "finding.face_distance_discrepancy": MessageTemplate(
        "The two faces to %1 disagree on the distance by %2 m, against a tolerance of %3 m. The "
        "mean of the two is not a measurement of anything; check the field book before using "
        "this pair.",
        "target",
        "difference",
        "tolerance",
    ),
    "finding.single_face_pointing": MessageTemplate(
        "The pointing to %1 was taken on one face only, so the instrumental errors were "
        "corrected from the profile rather than cancelled. Their uncertainties are included in "
        "the result.",
        "target",
    ),
    "finding.collimation_drift": MessageTemplate(
        "The collimation implied by the %1 face pairs at station %2 varies by %3 arcsec. A "
        "collimation that is constant across a setup is instrumental and harmless; one that "
        "drifts means the instrument was disturbed, and face pairing does not fix that.",
        "pairs",
        "station",
        "spread",
    ),
    "finding.vertical_index_drift": MessageTemplate(
        "The vertical index error at station %1 varies by %2 arcsec across its face pairs.",
        "station",
        "spread",
    ),
    "finding.angular_misclosure_beyond_tolerance": MessageTemplate(
        "The angular misclosure is %1 arcsec over %2 station(s), against a tolerance of %3 "
        "arcsec.",
        "misclosure",
        "stations",
        "tolerance",
    ),
    "finding.relative_precision_beyond_tolerance": MessageTemplate(
        "The traverse closes to 1:%1 over %2 m, against a required 1:%3.",
        "precision",
        "perimeter",
        "required",
    ),
    "finding.open_traverse_unchecked": MessageTemplate(
        "This traverse does not close on a known point, so no misclosure exists and nothing "
        "about it can be checked. A blunder anywhere in it would be invisible.",
    ),
    "finding.collinear_known_points": MessageTemplate(
        "The known points %1 are collinear, so they define no circle and cannot fix a "
        "resection between them.",
        "stations",
    ),
    "finding.danger_circle": MessageTemplate(
        "The occupied station lies on the danger circle through %1: every point on that circle "
        "sees the three in the same directions, so they do not determine a position. Add a "
        "fourth point off the circle, or a distance.",
        "stations",
    ),
    "finding.weak_intersection_geometry": MessageTemplate(
        "The rays to %1 are close to parallel: the error ellipse is %2 times longer than it is "
        "wide, so the point is poorly determined along one direction however precise the "
        "individual sightings are.",
        "target",
        "elongation",
    ),
    "finding.leapfrog_sights_imbalanced": MessageTemplate(
        "The two sights differ by %1 m over %2 m. Leap-frog cancels refraction in proportion to "
        "how equal the sights are, so an imbalanced pair gets much less of the method's "
        "benefit.",
        "imbalance",
        "length",
    ),
    "finding.no_atmospheric_data": MessageTemplate(
        "Station %1 records no temperature or pressure, so the first-velocity correction was "
        "not applied. On short sights this is immaterial; over a kilometre a 10 degree error is "
        "10 mm.",
        "station",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
