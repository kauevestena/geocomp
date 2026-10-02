# SPDX-License-Identifier: GPL-2.0-or-later
"""A changed setting changes what a run computes (FR-068; phase P12a).

``specs/15-ui-menu-and-settings.md`` section 2.3: before P12a, 36 declared
settings were read by nothing, and a user who changed the default meteorology or
the confidence level changed no result. ``tests/structural`` can only show that
something *names* a setting; this shows that the name leads somewhere -- that a
value set for the run becomes the default of the parameter it governs, which is
the value a run that does not override it computes with.

The table is the record of the wiring: specs/15 section 2.3 cites it rather
than copying it.
"""

from __future__ import annotations

import math

import pytest

pytestmark = pytest.mark.qgis

CONFIDENCE_USERS = (
    "geocomp:analysis_network_adjust",
    "geocomp:analysis_network_preanalysis",
    "geocomp:analysis_dynadjust_adjust",
    "geocomp:totalstation_intersection",
    "geocomp:totalstation_network",
    "geocomp:levelling_network",
    "geocomp:gravimetry_network",
    "geocomp:integration_multiple",
    "geocomp:monitoring_compare_epochs",
    "geocomp:monitoring_time_series",
)
ALPHA_USERS = (
    "geocomp:analysis_network_adjust",
    "geocomp:analysis_network_preanalysis",
    "geocomp:levelling_network",
    "geocomp:gravimetry_network",
)
BETA_USERS = (
    "geocomp:analysis_network_adjust",
    "geocomp:analysis_network_preanalysis",
    "geocomp:levelling_network",
    "geocomp:gravimetry_network",
)
EPOCH_USERS = (
    "geocomp:analysis_network_adjust",
    "geocomp:analysis_dynadjust_adjust",
    "geocomp:totalstation_network",
    "geocomp:levelling_network",
)

PREPROCESS = "geocomp:totalstation_preprocess"
TRAVERSE = "geocomp:totalstation_traverse"
FIELDBOOK = "geocomp:totalstation_import_fieldbook"

#: (setting, value set for the run, algorithm, parameter, the default that must follow)
WIRING: list[tuple[str, object, str, str, object]] = [
    ("total_station.default_temperature_celsius", 31.5, PREPROCESS, "TEMPERATURE", 31.5),
    ("total_station.default_pressure_hpa", 900.0, PREPROCESS, "PRESSURE", 900.0),
    ("total_station.default_humidity_percent", 80.0, PREPROCESS, "HUMIDITY", 80.0),
    ("total_station.default_temperature_sigma", 2.5, PREPROCESS, "TEMPERATURE_SIGMA", 2.5),
    ("total_station.default_pressure_sigma_hpa", 3.0, PREPROCESS, "PRESSURE_SIGMA", 3.0),
    ("total_station.refraction_coefficient", 0.2, "geocomp:totalstation_trig_levelling", "REFRACTION", 0.2),
    (
        "total_station.refraction_coefficient_sigma",
        0.07,
        "geocomp:totalstation_trig_levelling",
        "REFRACTION_SIGMA",
        0.07,
    ),
    ("total_station.collimation_tolerance", 2.0e-4, PREPROCESS, "COLLIMATION_TOLERANCE", 2.0e-4),
    ("total_station.face_distance_tolerance", 0.01, PREPROCESS, "DISTANCE_TOLERANCE", 0.01),
    ("total_station.traverse_adjustment", "transit", TRAVERSE, "METHOD", 1),
    ("total_station.traverse_adjustment", "none", TRAVERSE, "METHOD", 2),
    (
        "total_station.traverse_angular_tolerance_per_station",
        math.radians(20.0 / 3600.0),
        TRAVERSE,
        "ANGULAR_TOLERANCE",
        20.0 / 3600.0,
    ),
    ("total_station.traverse_relative_precision", 20000, TRAVERSE, "RELATIVE_LIMIT", 20000),
    ("stochastic.default_sigma_direction", 1.0e-5, FIELDBOOK, "SIGMA_DIRECTION", 1.0e-5),
    ("stochastic.default_sigma_zenith_angle", 2.0e-5, FIELDBOOK, "SIGMA_ZENITH", 2.0e-5),
    ("stochastic.default_sigma_slope_distance", 0.002, FIELDBOOK, "SIGMA_DISTANCE", 0.002),
    *[("stochastic.confidence_level", 0.99, algorithm, "CONFIDENCE", 0.99) for algorithm in CONFIDENCE_USERS],
    *[("stochastic.outlier_alpha", 0.01, algorithm, "ALPHA", 0.01) for algorithm in ALPHA_USERS],
    *[("stochastic.outlier_beta", 0.1, algorithm, "BETA", 0.1) for algorithm in BETA_USERS],
    ("level.tolerance_coefficient", 0.004, "geocomp:levelling_closures", "TOLERANCE_COEFFICIENT", 0.004),
    ("level.tolerance_coefficient", 0.004, "geocomp:levelling_network", "TOLERANCE_COEFFICIENT", 0.004),
    ("level.weighting", "setups", "geocomp:levelling_closures", "WEIGHTING", 1),
    ("level.weighting", "setups", "geocomp:levelling_network", "WEIGHTING", 1),
    ("level.max_sight_length", 60.0, "geocomp:levelling_equal_sights", "MAX_SIGHT_LENGTH", 60.0),
    ("level.max_sight_length", 60.0, "geocomp:levelling_extreme_sights", "MAX_SIGHT_LENGTH", 60.0),
    ("level.max_sight_imbalance", 2.0, "geocomp:levelling_equal_sights", "MAX_SIGHT_IMBALANCE", 2.0),
    ("level.max_sight_imbalance", 2.0, "geocomp:levelling_extreme_sights", "MAX_SIGHT_IMBALANCE", 2.0),
    (
        "level.max_accumulated_imbalance",
        5.0,
        "geocomp:levelling_equal_sights",
        "MAX_ACCUMULATED_IMBALANCE",
        5.0,
    ),
    ("level.reciprocal_variance_inflation", 3.0, "geocomp:levelling_equidistant_sights", "INFLATION", 3.0),
    ("level.adjust_failing_lines", True, "geocomp:levelling_network", "ADJUST_FAILING", True),
    ("level.apply_orthometric_correction", True, "geocomp:levelling_network", "ORTHOMETRIC", True),
    *[("reference_systems.default_epoch", 2020.5, algorithm, "EPOCH", 2020.5) for algorithm in EPOCH_USERS],
    ("reference_systems.default_epoch", 2020.5, "geocomp:integration_multiple", "EPOCH", "2020.5"),
    ("reference_systems.preferred_crs", "EPSG:31983", "geocomp:totalstation_network", "CRS", "EPSG:31983"),
    ("reference_systems.geoid_sigma", 0.08, "geocomp:integration_multiple", "GEOID_SIGMA", 0.08),
    ("basemaps.reuse_existing_layer", False, "geocomp:project_basemap", "REUSE", False),
]


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    return geocomp_provider


def _default(algorithm_id: str, parameter: str):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    # Held while the definition is read: the instance owns it, and Python would
    # otherwise collect the instance as soon as the call returned.
    instance = algorithm.create({})
    definition = instance.parameterDefinition(parameter)
    assert definition is not None, f"{algorithm_id} has no parameter {parameter}"
    return definition.defaultValue()


@pytest.mark.parametrize(
    ("key", "value", "algorithm_id", "parameter", "expected"),
    WIRING,
    ids=[f"{key}->{algorithm.split(':')[1]}.{parameter}" for key, _, algorithm, parameter, _ in WIRING],
)
def test_the_setting_becomes_the_parameters_default(key, value, algorithm_id, parameter, expected):
    from geocomp.services.settings_service import settings

    with settings.run_overrides({key: value}):
        changed = _default(algorithm_id, parameter)
    unchanged = _default(algorithm_id, parameter)

    if isinstance(expected, float):
        assert float(changed) == pytest.approx(expected, rel=1e-12)
    else:
        assert changed == expected
    assert changed != unchanged, "the setting's own default already gave this value; pick another"


def test_every_wired_setting_is_in_the_table():
    """A setting wired to a parameter default and missing here is wiring nobody checks."""
    from geocomp.core.settings_def import SETTINGS

    tabled = {key for key, *_ in WIRING}
    elsewhere = {
        # Not a parameter default; each has its own test.
        "total_station.atmospheric_model",  # test_the_generic_profile_uses_the_configured_model
        "reference_systems.geoid_model",  # test_the_geoid_model_becomes_the_file_default
        "basemaps.offer_on_result_layers",  # tests/qgis/test_basemap_offer.py
        "basemaps.default_service",  # tests/qgis/test_basemaps.py, and the offer
        "basemaps.catalogue",
    }
    wired_in_p12a = {
        definition.key
        for definition in SETTINGS
        if definition.section in ("total_station", "level", "stochastic", "reference_systems", "basemaps")
    }
    untabled = sorted(wired_in_p12a - tabled - elsewhere)
    assert not untabled, f"wired but not checked here: {untabled}"


def test_the_generic_profile_uses_the_configured_model():
    from geocomp.algorithms.totalstation.common import default_library
    from geocomp.services.settings_service import settings

    with settings.run_overrides({"total_station.atmospheric_model": "leica"}):
        library = default_library()
    profile = next(iter(library.instruments.values()))
    assert profile.atmospheric_model.value == "leica"


def test_the_geoid_model_becomes_the_file_default(tmp_path):
    from geocomp.services.settings_service import settings

    grid = tmp_path / "model.gtx"
    grid.write_bytes(b"")
    with settings.run_overrides({"reference_systems.geoid_model": str(grid)}):
        assert _default("geocomp:integration_multiple", "GEOID") == str(grid)
    assert not _default("geocomp:integration_multiple", "GEOID")


def test_an_unstated_epoch_leaves_each_algorithm_its_own():
    """Zero is 'none stated': an unconfigured installation computes what it did."""
    from geocomp.services.settings_service import settings

    with settings.run_overrides({"reference_systems.default_epoch": 0.0}):
        assert _default("geocomp:levelling_network", "EPOCH") == 2026.0
        assert _default("geocomp:analysis_network_adjust", "EPOCH") == 2000.0
        assert _default("geocomp:analysis_dynadjust_adjust", "EPOCH") == 0.0
        assert not _default("geocomp:integration_multiple", "EPOCH")
