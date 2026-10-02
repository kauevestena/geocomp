# SPDX-License-Identifier: GPL-2.0-or-later
"""What the About dialog and the system report say of the engines (specs/21 criterion 8)."""

from __future__ import annotations

from pathlib import Path

from geocomp.core.errors import ComputationError
from geocomp.engines.base import EngineVersion
from geocomp.engines.status import engine_status


def test_both_engines_with_their_own_licences():
    by_name = {engine.name: engine for engine in engine_status()}
    assert by_name["DynAdjust"].licence == "Apache License 2.0"
    assert by_name["RTKLIB (rnx2rtkp)"].licence == "BSD-2-Clause"
    assert all(engine.attribution and engine.url.startswith("https://") for engine in by_name.values())


def test_an_installed_engine_reports_its_version(monkeypatch):
    found = EngineVersion(name="DynAdjust", version="1.4.0", path=Path("/opt/dynadjust/dnaadjust"))
    monkeypatch.setattr(
        "geocomp.engines.dynadjust.engine.DynAdjustEngine.detect", lambda self: found
    )
    (dynadjust,) = [e for e in engine_status() if e.name == "DynAdjust"]
    assert dynadjust.version is found


def test_an_engine_that_will_not_answer_is_not_found_rather_than_fatal(monkeypatch):
    """A broken install must not stop the dialog or the report that would help
    diagnose it."""

    def broken(self):
        raise ComputationError("engine_version_unreadable")

    monkeypatch.setattr("geocomp.engines.rtklib.engine.RtklibEngine.version", broken)
    (rtklib,) = [e for e in engine_status() if e.name.startswith("RTKLIB")]
    assert rtklib.version is None
