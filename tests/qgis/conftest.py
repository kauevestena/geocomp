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
