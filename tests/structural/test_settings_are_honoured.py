# SPDX-License-Identifier: GPL-2.0-or-later
"""A declared setting must be read by something, or be listed as not yet read.

The Global Settings window is generated from ``core/settings_def.py``: declare a
``SettingDef`` and a control appears, resolving correctly through run, project
and global scope. Nothing generates the *use* of the value. A setting can
therefore be declared, labelled, translated, shown, stored, resolved and
recorded in provenance while no computation ever reads it -- and from the
outside it is indistinguishable from one that works.

The pre-P7 review found **36 of 47 declared settings in that state**. This is
the same shape as the defect phase P4 recorded one level up, when the dialog
rendered raw dotted keys for all seventeen settings P3 had declared: the dialog
is generated from the declarations, the labels were not, and nobody looked. The
labels are guarded now by ``test_settings_labels.py``. This file guards the
behaviour.

It cannot prove a setting is *honoured correctly* -- only that some module names
it. That is worth having anyway: it is the difference between a value nobody
reads and a value somebody reads, and every one of the 36 failed at the first
hurdle.
"""

from __future__ import annotations

from tests.conftest import PLUGIN_DIR

#: Where a setting is declared and where it is displayed. Naming a key in either
#: is not using it.
DECLARATION_SITES = ("core/settings_def.py", "gui/settings_dialog.py")

#: Settings that are declared and read by nothing, each with the phase that owes
#: the wiring. **Do not add to this list to make a new setting pass.** A setting
#: added here without a phase behind it is a control the user can change that
#: silently does nothing, which is worse than an absent control: it invites a
#: choice and then discards it.
#:
#: The wiring is assigned to **P12** ([`specs/ROADMAP.md`](../../specs/ROADMAP.md)),
#: whose specification list already includes `specs/15`, and is recorded in
#: `specs/15-ui-menu-and-settings.md` section 2.3.
NOT_YET_HONOURED = {
    # Display formatting. `core/units.py` has `format_dms` and `convert` ready
    # for these and no caller; nothing in the reports, the exports or the layers
    # formats an angle or a distance for display at all -- they emit SI with the
    # unit named, which is right for a machine-readable export and is not what
    # these four settings promise.
    "interface.angle_decimals": "P12",
    "interface.angle_format": "P12",
    "interface.coordinate_decimals": "P12",
    "interface.distance_unit": "P12",
    # Levelling. All but the first have a core function taking them as an
    # argument (`techniques/levelling/schemes.py`, `line.py` and
    # `normal_orthometric_correction`); the algorithms pass hard-coded
    # Processing parameter defaults instead of resolving the setting.
    # `adjust_failing_lines` is the exception and the worse case: no switch of
    # that name exists anywhere in the core, so nothing would honour it even if
    # the value were passed.
    "level.adjust_failing_lines": "P12",
    "level.apply_orthometric_correction": "P12",
    "level.max_accumulated_imbalance": "P12",
    "level.max_sight_imbalance": "P12",
    "level.max_sight_length": "P12",
    "level.reciprocal_variance_inflation": "P12",
    "level.tolerance_coefficient": "P12",
    # Total station. Same shape: `techniques/total_station/atmosphere.py` and
    # `survey.py` take them as arguments and the algorithms hard-code them.
    "total_station.atmospheric_model": "P12",
    "total_station.default_humidity_percent": "P12",
    "total_station.default_pressure_hpa": "P12",
    "total_station.default_pressure_sigma_hpa": "P12",
    "total_station.default_temperature_celsius": "P12",
    "total_station.default_temperature_sigma": "P12",
    "total_station.refraction_coefficient": "P12",
    "total_station.refraction_coefficient_sigma": "P12",
    "total_station.traverse_adjustment": "P12",
    "total_station.traverse_angular_tolerance_per_station": "P12",
    "total_station.traverse_relative_precision": "P12",
    # Stochastic defaults (FR-064). `instruments/profiles.py` carries the
    # `StochasticDefaults` machinery these would populate.
    "stochastic.confidence_level": "P12",
    "stochastic.default_sigma_direction": "P12",
    "stochastic.default_sigma_height_difference": "P12",
    "stochastic.default_sigma_slope_distance": "P12",
    "stochastic.default_sigma_zenith_angle": "P12",
    "stochastic.outlier_beta": "P12",
    # Reference systems (P5). `io/geoid.py` and `core/geodesy/` implement all of
    # this; the algorithms take a CRS and a geoid file as parameters instead.
    "reference_systems.default_epoch": "P12",
    "reference_systems.geoid_model": "P12",
    "reference_systems.geoid_sigma": "P12",
    "reference_systems.preferred_crs": "P12",
    "reference_systems.preferred_transformations": "P12",
    "reference_systems.transformation_choice": "P12",
    "reference_systems.transformation_grid_directory": "P12",
    # Base maps. `basemaps.catalogue` and `basemaps.default_service` are read;
    # this one, which decides whether to offer a base map at all, is not.
    "basemaps.offer_on_result_layers": "P12",
}


def _readers() -> dict[str, list[str]]:
    """For each declared key, the modules naming it outside its declaration."""
    from geocomp.core.settings_def import SETTINGS

    sources = {
        path.relative_to(PLUGIN_DIR).as_posix(): path.read_text(encoding="utf-8")
        for path in PLUGIN_DIR.rglob("*.py")
    }
    for site in DECLARATION_SITES:
        sources.pop(site, None)
    return {
        definition.key: sorted(name for name, text in sources.items() if definition.key in text)
        for definition in SETTINGS
    }


def test_there_are_settings_to_check():
    """Guards the scan: an empty walk would make both checks below vacuous."""
    readers = _readers()
    assert len(readers) > 40
    assert any(readers.values()), "no setting is read by anything -- the scan is broken"


def test_every_declared_setting_is_read_or_declared_unread():
    unaccounted = sorted(
        key for key, users in _readers().items() if not users and key not in NOT_YET_HONOURED
    )
    assert not unaccounted, (
        "these settings are declared and read by nothing. A control the user can "
        "change that silently does nothing is worse than no control. Wire it, or "
        "add it to NOT_YET_HONOURED with the phase that will: " + str(unaccounted)
    )


def test_the_not_yet_honoured_list_has_no_stale_entries():
    """So that wiring one and forgetting the list cannot leave a false record."""
    readers = _readers()
    now_read = sorted(key for key in NOT_YET_HONOURED if readers.get(key))
    assert not now_read, (
        "these are listed as not yet honoured but something now reads them; "
        "remove them from NOT_YET_HONOURED: " + str(now_read)
    )
    undeclared = sorted(set(NOT_YET_HONOURED) - set(readers))
    assert not undeclared, (
        "NOT_YET_HONOURED names settings that are no longer declared: " + str(undeclared)
    )
