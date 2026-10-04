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
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
