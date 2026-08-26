# SPDX-License-Identifier: GPL-2.0-or-later
"""The plugin manifest and the code must agree on the version.

``specs/21`` section 3: the build refuses to proceed on a mismatch. A ZIP whose
manifest claims one version while the code reports another makes every bug
report ambiguous.
"""

from __future__ import annotations

import configparser

from geocomp.core.version import VERSION_INFO, __version__
from tests.conftest import PLUGIN_DIR


def _metadata():
    parser = configparser.ConfigParser()
    parser.read(PLUGIN_DIR / "metadata.txt", encoding="utf-8")
    return parser["general"]


def test_metadata_version_matches_the_code():
    assert _metadata()["version"] == __version__


def test_version_info_and_string_agree():
    assert __version__ == ".".join(str(part) for part in VERSION_INFO)


def test_metadata_declares_the_required_fields():
    """plugins.qgis.org rejects a manifest missing any of these."""
    metadata = _metadata()
    for field in ("name", "qgisMinimumVersion", "description", "version", "author", "email"):
        assert metadata.get(field), f"metadata.txt is missing {field}"


def test_licence_is_declared_as_gpl():
    """NFR-009 and ADR-0001."""
    assert _metadata()["license"] == "GPL-2.0-or-later"


def test_minimum_qgis_is_the_targeted_series():
    """ADR-0007: GeoComp targets QGIS 4.x; 3.x is deliberately not supported."""
    minimum = _metadata()["qgisMinimumVersion"]
    assert minimum.startswith("4."), minimum


def test_processing_provider_is_declared():
    """Without this flag QGIS does not surface the provider correctly (FR-030)."""
    assert _metadata()["hasProcessingProvider"] == "yes"
