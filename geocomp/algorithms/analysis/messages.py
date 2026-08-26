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
        "Observation '%1' is of type %2, which the in-house adjustment does not implement. "
        "%3",
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
    "computation.adjustment_did_not_run": MessageTemplate(
        "The adjustment of '%1' produced no iterations at all. This is an internal error; "
        "please report it with the network that caused it.",
        "network",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
