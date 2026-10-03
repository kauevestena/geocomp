# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for what the engine manager and engine discovery refuse (P12c-6).

Each says what happened and what to do about it (NFR-006). Until P12c-6 none of
these codes had a template: nothing in the plugin installed an engine, and a
DynAdjust directory that did not exist reached the user as
"could not complete the operation (validation.engine_path_not_found)".

Importing this module registers the templates; :mod:`geocomp.algorithms.engines`
imports it.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

TEMPLATES: dict[str, MessageTemplate] = {
    # -- an engine that is not there (FR-306) -----------------------------
    # RTKLIB's absence reached the GNSS algorithms' users as "could not complete
    # the operation (computation.engine_not_available)" until P12c-6.
    "computation.engine_not_available": MessageTemplate(
        "%1 is needed for %2 and was not found. It needs %3. Everything in GeoComp that "
        "does not need it works without it.",
        "engine",
        "operation",
        "expected",
    ),
    "validation.engine_path_not_found": MessageTemplate(
        "The path given for %1 does not exist: '%2'. GeoComp does not fall back to another "
        "copy of the program when one is named. Correct the path in Global Settings, under "
        "Paths and engines, or clear it to use GeoComp's installation or the system path.",
        "program",
        "received",
    ),
    "validation.engine_release_not_pinned": MessageTemplate(
        "GeoComp has no verified release of %1 for this computer (%2); it has one for: %3. "
        "Install the engine yourself and give its path in Global Settings, under Paths and "
        "engines.",
        "engine",
        "platform",
        "available",
    ),
    "data.engine_download_failed": MessageTemplate(
        "The engine could not be downloaded from %1 (HTTP status %2: %3). Check the network "
        "and QGIS's proxy settings, then run the installation again.",
        "url",
        "status",
        "reason",
    ),
    "data.engine_download_produced_nothing": MessageTemplate(
        "The download of %1 from %2 produced no file. Run the installation again.",
        "engine",
        "url",
    ),
    "data.engine_archive_digest_mismatch": MessageTemplate(
        "The downloaded archive is not the one GeoComp was tested with: its SHA-256 is %1, "
        "and GeoComp expects %2. It was deleted and nothing was installed. Run the "
        "installation again; if it happens again, report it rather than working around it.",
        "received",
        "expected",
    ),
    "data.engine_archive_member_escapes": MessageTemplate(
        "The downloaded archive contains '%1', which would be written outside the "
        "installation folder. Nothing was extracted. Report this: the archive is not the "
        "one GeoComp expects.",
        "member",
    ),
    "data.engine_archive_contains_symlink": MessageTemplate(
        "The downloaded archive contains a link, '%1', where only programs were expected. "
        "Nothing was extracted. Report this: the archive is not the one GeoComp expects.",
        "member",
    ),
    "data.engine_archive_missing_programs": MessageTemplate(
        "The downloaded archive does not contain %1. The engine's release has probably "
        "changed shape, and GeoComp needs updating; meanwhile install it yourself and give "
        "its path in Global Settings.",
        "expected",
    ),
    "data.engine_archive_programs_scattered": MessageTemplate(
        "The downloaded archive puts the engine's programs in several folders (%1); GeoComp "
        "runs them from one. Install the engine yourself and give its path in Global "
        "Settings.",
        "received",
    ),
    "data.engine_installation_not_recorded": MessageTemplate(
        "%1 was installed in %2 but its record could not be written. Run the installation "
        "again.",
        "engine",
        "root",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
