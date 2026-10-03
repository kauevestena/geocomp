# SPDX-License-Identifier: GPL-2.0-or-later
"""The engine manager against the real pinned release, on the machine it runs on (specs/21 criterion 4).

``specs/21`` criterion 4: the engine manager downloads, verifies, installs and
detects each engine on each supported operating system, and an explicitly
configured path overrides it. P6 did this once, by hand, on Linux; Windows and
macOS were pinned and never run. Here the ``engine`` workflow runs it on all
three, against the archive upstream actually publishes:

* the pinned release for this machine is downloaded and its SHA-256 checked;
* it is extracted, recorded, and found where the record says;
* the installed ``dnaadjust`` runs here and reports the pinned version;
* a configured directory wins over it;
* and it adjusts a network, agreeing with the committed fixture -- which a
  build that started but computed differently on this platform would not.

The download is plain ``urllib`` rather than the QGIS network stack: these jobs
have no QGIS, and what differs between operating systems is everything after
the download. The QGIS fetcher is tested against a local server
(``tests/qgis/test_engine_install.py``).

Skipped unless ``GEOCOMP_ENGINE_DOWNLOAD=1``: tens of megabytes from GitHub is
not something every test run should do, and the workflow that sets it fails if
these skip.
"""

from __future__ import annotations

import math
import os
import shutil
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import pytest

from geocomp.core.models import Epoch
from geocomp.engines.dynadjust.engine import PROGRAMS, DynAdjustEngine, DynAdjustJob
from geocomp.engines.dynadjust.read_dynaml import read_dynaml
from geocomp.engines.dynadjust.read_output import AngularFormat
from geocomp.engines.dynadjust.solution import read_solution
from geocomp.engines.manager import (
    current_platform,
    install_pinned,
    installed,
    managed_directories,
    releases_for,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("GEOCOMP_ENGINE_DOWNLOAD") != "1",
    reason=(
        "downloads the pinned DynAdjust release; set GEOCOMP_ENGINE_DOWNLOAD=1 "
        "(the engine workflow's manager job does, on Linux, Windows and macOS)"
    ),
)

DATA = Path(__file__).parent / "data" / "dynadjust"


def _fetch(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url, timeout=600) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


@pytest.fixture(scope="module")
def installation(tmp_path_factory):
    root = tmp_path_factory.mktemp("profile") / "geocomp" / "engines"
    platform = current_platform()
    assert releases_for("dynadjust", platform), f"no pinned DynAdjust for {platform}"
    install_pinned("dynadjust", platform, root=root, fetch=_fetch)
    return root, installed("dynadjust", root)


def test_the_pinned_release_is_downloaded_verified_and_recorded(installation):
    root, found = installation
    release = releases_for("dynadjust", current_platform())[0]
    assert found is not None
    assert (found.version, found.platform, found.sha256) == (
        release.version,
        current_platform(),
        release.sha256,
    )
    assert not list(root.rglob("*.zip")), "the archive is removed once installed"


def test_every_program_is_where_the_record_says(installation):
    root, found = installation
    engine = DynAdjustEngine(extra_directories=managed_directories("dynadjust", root))
    for program in PROGRAMS:
        assert engine.locate(program).parent == found.directory, program


def test_the_installed_engine_runs_here_and_reports_the_pinned_version(installation):
    root, found = installation
    version = DynAdjustEngine(extra_directories=managed_directories("dynadjust", root)).detect()
    assert version is not None, "the installed dnaadjust did not run on this machine"
    assert version.path.parent == found.directory
    assert version.version == found.version
    assert version.tested


def test_a_configured_directory_overrides_it(installation, tmp_path):
    root, found = installation
    own = tmp_path / "own-installation"
    shutil.copytree(found.directory, own)
    engine = DynAdjustEngine(
        configured_directory=own, extra_directories=managed_directories("dynadjust", root)
    )
    version = engine.detect()
    assert version is not None
    assert version.path.parent == own


def test_it_adjusts_a_network_here_as_it_does_where_the_fixtures_were_made(installation, tmp_path):
    """The sample GNSS network, through GeoComp's whole DynAdjust pipeline, with
    the managed installation, against the output committed from the Linux build
    the parsers were written for."""
    root, _found = installation
    network = read_dynaml(DATA / "sample-stn.xml", DATA / "sample-msr.xml").network
    fixture = read_solution(
        DATA / "output" / "sample.adj",
        network=network,
        apu_path=DATA / "output" / "sample.apu",
        cor_path=DATA / "output" / "sample.cor",
        angular_format=AngularFormat.HP,
    )
    network.epoch = Epoch.from_datetime(datetime(2020, 1, 1, tzinfo=UTC), label="01.01.2020")
    engine = DynAdjustEngine(extra_directories=managed_directories("dynadjust", root))
    solution = engine.adjust(DynAdjustJob(network=network, name="run"), tmp_path)

    assert solution.statistics.converged
    assert solution.statistics.degrees_of_freedom == fixture.statistics.degrees_of_freedom
    expected = {s.station_id: [q.value for q in s.position.values] for s in fixture.adjusted_stations}
    got = {s.station_id: [q.value for q in s.position.values] for s in solution.adjusted_stations}
    assert set(got) == set(expected)
    worst = max(math.dist(got[name], expected[name]) for name in expected)
    assert worst < 1.0e-4, f"{worst * 1000:.3f} mm from the fixture"
