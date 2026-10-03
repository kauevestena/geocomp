# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for what a monitoring analysis refuses (``specs/14``, phase P10b).

Each says what failed, why, and what to do about it (NFR-006). The refusals are
the point of the module -- every one of them stops a systematic difference from
being reported as motion -- so each names the solutions or the stations it is
about: "the epochs cannot be compared" is true and no use to anyone deciding
whether a dam moved.

Importing this module registers the templates; :mod:`geocomp.algorithms.monitoring`
imports it.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

TEMPLATES: dict[str, MessageTemplate] = {
    "validation.monitoring_solution_without_epoch": MessageTemplate(
        "The solution '%1' states no epoch, so it cannot enter a comparison (FR-105). "
        "The difference of two unknown instants is not a displacement; GeoComp does not "
        "assume one. Adjust the epoch's network again with its observation date.",
        "solution",
    ),
    "validation.monitoring_solution_epoch_assumed": MessageTemplate(
        "The solution '%1' carries the epoch %2 only because nothing stated one: the "
        "adjustment used its own default. An assumed epoch is not when the network was "
        "measured, so it cannot enter a comparison (FR-105). Adjust the epoch's network again "
        "with its observation date as the reference epoch.",
        "solution",
        "received",
    ),
    "validation.solution_without_epoch": MessageTemplate(
        "The solution '%1' states no epoch, and GeoComp does not assume one (FR-105). "
        "Adjust its network again with its observation date.",
        "solution",
    ),
    "validation.monitoring_height_types_differ": MessageTemplate(
        "The two solutions (%1) hold heights of different types: %2. Their difference "
        "would be the difference of the height systems, not motion. Adjust both epochs "
        "with heights of one type.",
        "solutions",
        "received",
    ),
    "validation.monitoring_geoid_models_differ": MessageTemplate(
        "The two solutions (%1) relate heights to the ellipsoid through different geoid "
        "models: %2. Heights from two models differ by the difference of the models, "
        "which is not motion. Use the same geoid model at every epoch.",
        "solutions",
        "received",
    ),
    "validation.monitoring_datum_incompatible": MessageTemplate(
        "The two solutions (%1) define their datum differently: %2. A free solution "
        "compares with a free one, and a held solution with one held the same way; a "
        "held one carries its constraint in its coordinates, and no transformation "
        "takes it out. Adjust both epochs with the same datum definition.",
        "solutions",
        "received",
    ),
    "validation.monitoring_coordinate_systems_differ": MessageTemplate(
        "The two solutions are in different coordinate systems (%1). Two projections "
        "differ by the projection, not by motion. Adjust both epochs in one coordinate "
        "reference system, or give both in a geocentric frame, which GeoComp transforms.",
        "received",
    ),
    "validation.monitoring_mixed_coordinate_systems": MessageTemplate(
        "The solution '%1' mixes coordinate systems (%2) among its stations. Compare "
        "solutions whose stations are all in one system.",
        "solution",
        "received",
    ),
    "validation.monitoring_frames_differ": MessageTemplate(
        "The two solutions are in frames GeoComp cannot relate (%1). Give both in ITRF2000 "
        "to ITRF2020 or SIRGAS 2000, which GeoComp transforms between with the "
        "transformation's own uncertainty.",
        "received",
    ),
    "validation.monitoring_frame_needs_velocity": MessageTemplate(
        "The frames %1 are related only at epoch %2, and the second solution is at "
        "another. Carrying a position between epochs along a velocity is exactly the "
        "motion being measured, so GeoComp will not do it here. Give both epochs in "
        "frames related at every epoch (the ITRFs), or in the same frame.",
        "received",
        "epoch",
    ),
    "validation.monitoring_components_differ": MessageTemplate(
        "The two solutions estimate different components (%1). Compare epochs adjusted "
        "in the same dimension: plan with plan, heights with heights, 3D with 3D.",
        "received",
    ),
    "validation.monitoring_no_common_stations": MessageTemplate(
        "The solutions '%1' and '%2' have no station in common, so there is nothing to "
        "compare. The same mark must carry the same name at every epoch.",
        "first",
        "second",
    ),
    "validation.monitoring_station_not_in_both": MessageTemplate(
        "These stations are not in both solutions: %1. Stations both epochs estimate: %2.",
        "stations",
        "expected",
    ),
    "validation.monitoring_station_not_compared": MessageTemplate(
        "These stations were not compared: %1. The compared stations are: %2.",
        "stations",
        "expected",
    ),
    "validation.monitoring_no_position_components": MessageTemplate(
        "The solution '%1' has no position components to compare (%2).",
        "solution",
        "received",
    ),
    "validation.monitoring_reference_block_empty": MessageTemplate(
        "No reference stations were named. A displacement is measured against stations "
        "assumed stable; name them in Reference stations, or mark them REFERENCE in the "
        "network document.",
    ),
    "validation.monitoring_reference_block_too_small": MessageTemplate(
        "The reference block (%1) is too small to define the datum '%2'. Add reference "
        "stations, or choose a datum with fewer parameters.",
        "stations",
        "datum",
    ),
    "validation.monitoring_reference_block_unstable": MessageTemplate(
        "The reference block has moved: its congruency test gives %1 against a critical "
        "value of %2, and the localisation implicates %3. The analysis does not proceed "
        "on a block that has itself moved, because that motion would be spread over "
        "every other station. The stations that remain stable are %4. Check the "
        "implicated pillars, then analyse again with them among the object points.",
        "statistic",
        "critical",
        "stations",
        "stable",
    ),
    "validation.monitoring_datum_unknown": MessageTemplate(
        "'%1' is not a datum GeoComp can refer displacements to. Choose one of: %2.",
        "received",
        "expected",
    ),
    "validation.monitoring_datum_needs_plan": MessageTemplate(
        "The datum '%1' needs a plan (east and north) and these solutions have none. "
        "Use the translation datum for heights.",
        "received",
    ),
    "validation.monitoring_cross_covariance_shape": MessageTemplate(
        "The cross-covariance given has shape %1; it must be %2.",
        "received",
        "expected",
    ),
    "validation.monitoring_series_too_short": MessageTemplate(
        "A series needs two epochs at least; %1 was given.",
        "received",
    ),
    "validation.monitoring_strain_configuration": MessageTemplate(
        "Strain cannot be computed here: %1. It needs three object points at least, "
        "spread over an area.",
        "expected",
    ),
    "validation.monitoring_alert_limit": MessageTemplate(
        "The %1 threshold's limit is %2; it must be positive.",
        "kind",
        "received",
    ),
    "validation.monitoring_threshold_row": MessageTemplate(
        "Row %1 of the alert thresholds file cannot be read: '%2'. Expected %3. Each row "
        "is kind, limit, stations, group.",
        "row",
        "received",
        "expected",
    ),
    "validation.monitoring_document_kind": MessageTemplate(
        "This file is a '%1', not a '%2'. Give the document the monitoring algorithm "
        "wrote for this input.",
        "received",
        "expected",
    ),
    "validation.monitoring_document_version": MessageTemplate(
        "This monitoring document is version %1; this GeoComp reads version %2. Run the "
        "analysis again to write it anew.",
        "received",
        "expected",
    ),
    "validation.monitoring_document_incomplete": MessageTemplate(
        "This monitoring document lacks %1, so it cannot be read. Run the analysis "
        "again to write it anew.",
        "missing",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
