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
        "Expected %1.",
        "expected",
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
        "The network '%1' is not internally consistent: %2. Run Inspect network to see "
        "every problem at once.",
        "network",
        "problems",
    ),
    # -- what the network is missing --------------------------------------
    "computation.no_active_observations": MessageTemplate(
        "The network '%1' has no active observations, so there is nothing to adjust. "
        "Observations marked as rejected do not take part; re-activate the ones you want "
        "to use.",
        "network",
    ),
    "computation.no_observations": MessageTemplate(
        "No observations were supplied. %1",
        "expected",
    ),
    "computation.no_planned_observations": MessageTemplate(
        "The planned network '%1' contains no observations, so there is no design to "
        "evaluate. Add the observations you intend to make, with their assumed precisions.",
        "network",
    ),
    "validation.no_estimable_parameters": MessageTemplate(
        "Every station in this network is held fixed, so there is nothing to estimate. %1",
        "expected",
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
        "No stations were given to define the datum on. %1",
        "expected",
    ),
    "data.observation_without_uncertainty": MessageTemplate(
        "Observation '%1' carries no uncertainty, so it cannot be weighted. %2",
        "observation",
        "expected",
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
        "The field mapping supplies no column for %1, which every import needs: %2. "
        "Give a mapping that names them, or a field book whose header does.",
        "received",
        "expected",
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
        "The field book '%1' could not be read. Choose an existing, readable CSV file.",
        "received",
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
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
