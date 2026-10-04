# SPDX-License-Identifier: GPL-2.0-or-later
"""Diagnostics reach the QGIS log under a GeoComp tab, at a chosen verbosity (FR-009).

Until P12c-13 nothing tested either half. The log is developer-facing and not
translated (``geocomp/services/logging.py``); what is asserted here is where it
goes and that ``interface.log_level`` decides what reaches it.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis


@pytest.fixture
def received(qgis_app):
    """Every message the QGIS log receives while the test runs, as (tag, text)."""
    from qgis.core import QgsApplication

    seen: list[tuple[str, str]] = []

    def record(message, tag, _level):
        seen.append((tag, message))

    log = QgsApplication.messageLog()
    log.messageReceived.connect(record)
    yield seen
    log.messageReceived.disconnect(record)


def test_messages_go_under_the_geocomp_tab(received):
    from geocomp.services.logging import GeoCompLog, LogLevel

    GeoCompLog(LogLevel.INFO).info("a run started")
    assert ("GeoComp", "a run started") in received


@pytest.mark.parametrize(
    ("setting", "shown", "hidden"),
    [
        ("debug", {"detail", "progress", "problem"}, set()),
        ("info", {"progress", "problem"}, {"detail"}),
        ("warning", {"problem"}, {"detail", "progress"}),
    ],
)
def test_the_verbosity_setting_decides_what_is_written(received, setting, shown, hidden):
    from geocomp.services.logging import GeoCompLog, LogLevel

    log = GeoCompLog()
    log.set_threshold(LogLevel.from_setting(setting))
    log.debug("detail")
    log.info("progress")
    log.warning("problem")
    texts = {text.removeprefix("[debug] ") for tag, text in received if tag == "GeoComp"}
    assert shown <= texts
    assert not hidden & texts


def test_the_plugin_reads_the_setting(received):
    """``SettingsService.apply_log_level`` is what the plugin calls at start."""
    from geocomp.services.logging import LogLevel, log
    from geocomp.services.settings_service import settings

    previous = log.threshold
    try:
        settings.set_global("interface.log_level", "warning")
        settings.apply_log_level()
        assert log.threshold is LogLevel.WARNING
    finally:
        settings.reset_global("interface.log_level")
        log.set_threshold(previous)
