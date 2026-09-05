# SPDX-License-Identifier: GPL-2.0-or-later
"""One QGIS application for the whole tier-3 session.

``QgsApplication`` is a process-wide singleton: initialising it per test would
fail the second time, and tearing it down between tests leaves the Processing
registry in a state nothing else expects. So it is session-scoped, and the
provider is registered on it once.
"""

from __future__ import annotations

import pytest

from tests.conftest import has_qgis

pytestmark = pytest.mark.qgis


@pytest.fixture(scope="session")
def qgis_app():
    if not has_qgis():
        pytest.skip("requires a QGIS runtime")

    from qgis.core import QgsApplication

    app = QgsApplication([], False)
    app.initQgis()
    yield app
    app.exitQgis()


@pytest.fixture(scope="session")
def geocomp_provider(qgis_app):
    """Register the GeoComp provider, exactly as ``plugin.initGui`` does."""
    from qgis.core import QgsApplication

    from geocomp.provider import GeoCompProvider

    provider = GeoCompProvider()
    QgsApplication.processingRegistry().addProvider(provider)
    yield provider
    QgsApplication.processingRegistry().removeProvider(provider)


def qgis_version() -> int:
    """QGIS's integer version, e.g. ``33404``, or 0 where QGIS is absent."""
    if not has_qgis():
        return 0
    from qgis.core import Qgis

    return int(Qgis.QGIS_VERSION_INT)


#: ``QgsField(name, QMetaType.Type)`` arrived in QGIS 3.38; before it, fields
#: were typed with ``QVariant.Type``.
#:
#: GeoComp declares ``qgisMinimumVersion=4.0.0`` (ADR-0007) and uses the
#: QMetaType form, which is correct for the target and for CI's
#: ``qgis/qgis:latest``. A developer whose distribution ships an older QGIS can
#: still run the rest of the tier-3 suite, and gets a skip that says why rather
#: than a wall of errors that hides real failures among environmental ones.
#:
#: Deliberately keyed on the version rather than on a try/except around the
#: call: a genuine regression in field construction must fail, not skip.
requires_modern_field_api = pytest.mark.skipif(
    0 < qgis_version() < 33800,
    reason=(
        "QgsField(name, QMetaType.Type) needs QGIS >= 3.38; this QGIS is older than "
        "the plugin's declared minimum of 4.0"
    ),
)
