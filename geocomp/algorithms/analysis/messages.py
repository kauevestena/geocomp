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
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
