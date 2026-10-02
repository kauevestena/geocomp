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
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
