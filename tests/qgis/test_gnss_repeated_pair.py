# SPDX-License-Identifier: GPL-2.0-or-later
"""A pair the folder holds twice is two baselines, each with its own record (P13-25).

A campaign observes a pair on several days, and *Build baselines* reads a
folder of their solutions. Until P13-25 every baseline was named ``BASE-ROVER``,
so a pair held twice was two baselines with one name, and everything keyed by
it kept one of them:
- the quality record, so one session's was lost;
- the session, so the network document gave a baseline the other's epoch;
- the observation id, so keeping the dependent baselines refused the whole run,
  with a remedy -- remove the repeated member -- the user could not apply;
- the independent and dependent lists, which could name the same id in each.

The solutions are the GNSS tutorial's, as the real engine solved them
(``tests/data/ggao``): GODN-GODE at midnight and at eleven, and the
triangle's other two sides at midnight.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT
from tests.qgis.walkthrough import run_logged

pytestmark = pytest.mark.qgis

ALGORITHM = "geocomp:gnss_build_baselines"
RECORDED = REPO_ROOT / "tests" / "data" / "ggao"
MIDNIGHT = "GODN-GODE 2025-01-01 00:00/00:59"
ELEVEN = "GODN-GODE 2025-01-01 11:00/11:59"
NAMES = {MIDNIGHT, ELEVEN, "GODN-GODS", "GODE-GODS"}


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture
def folder(tmp_path) -> Path:
    solutions = tmp_path / "solutions"
    solutions.mkdir()
    for hour in ("00", "11"):
        shutil.copyfile(RECORDED / f"hour-{hour}" / "godn-gode.pos", solutions / f"godn-gode-{hour}.pos")
    for pair in ("godn-gods", "gode-gods"):
        shutil.copyfile(RECORDED / "hour-00" / f"{pair}.pos", solutions / f"{pair}.pos")
    return solutions


def _build(folder: Path, **extra) -> tuple[dict, dict, str]:
    """The baselines document, the network document, and the log."""
    out = folder.parent
    results, log = run_logged(
        ALGORITHM,
        {
            "FOLDER": str(folder),
            "INDEPENDENT_ONLY": False,
            # The network document needs a frame; ITRF2020 is the first offered.
            "FRAME": 1,
            "OUTPUT_JSON": str(out / "baselines.json"),
            "OUTPUT_NETWORK": str(out / "network.json"),
            **extra,
        },
    )
    return (
        json.loads(Path(results["OUTPUT_JSON"]).read_text(encoding="utf-8")),
        json.loads(Path(results["OUTPUT_NETWORK"]).read_text(encoding="utf-8")),
        log,
    )


class TestARepeatedPair:
    def test_each_session_is_its_own_baseline(self, folder):
        document, _network, _log = _build(folder)
        assert {o["id"] for o in document["observations"]} == {f"gnss-{name}" for name in NAMES}
        assert set(document["quality"]) == NAMES
        assert set(document["independent"]) | set(document["dependent"]) == NAMES
        assert not set(document["independent"]) & set(document["dependent"])

    def test_a_pair_held_once_keeps_its_plain_name(self, folder):
        (folder / "godn-gode-11.pos").unlink()
        document, _network, log = _build(folder)
        assert set(document["quality"]) == {"GODN-GODE", "GODN-GODS", "GODE-GODS"}
        assert "more than once" not in log

    def test_the_log_says_why_they_are_named_so(self, folder):
        _document, _network, log = _build(folder)
        assert (
            "GODN-GODE is in the folder more than once, so each of its baselines is named by its "
            f"span: {MIDNIGHT}, {ELEVEN}."
        ) in log

    def test_each_is_at_its_own_sessions_epoch(self, folder):
        _document, network, _log = _build(folder)
        epochs = {o["id"]: o["epoch"]["instant"] for o in network["observations"]}
        assert epochs[f"gnss-{MIDNIGHT}"] == "2025-01-01T00:29:45+00:00"
        assert epochs[f"gnss-{ELEVEN}"] == "2025-01-01T11:29:45+00:00"

    def test_the_independent_ones_too(self, folder):
        document, network, _log = _build(folder, INDEPENDENT_ONLY=True)
        kept = {o["id"]: o["epoch"]["instant"] for o in network["observations"]}
        assert set(kept) == {f"gnss-{name}" for name in document["independent"]}
        for name in document["independent"]:
            hour = "11" if name == ELEVEN else "00"
            assert kept[f"gnss-{name}"] == f"2025-01-01T{hour}:29:45+00:00", name

    def test_a_float_one_is_named_by_its_session(self, folder):
        document, _network, log = _build(folder)
        assert set(document["float"]) <= NAMES
        for name in document["float"]:
            assert f"{name} is taken from an epoch whose ambiguities were not fixed" in log

    def test_each_keeps_its_own_heights(self, folder):
        document, _network, _log = _build(folder, STATION_HEIGHTS=["GODN", "0.0083", "GODE", "0.0614"])
        assert set(document["antenna_heights"]) == NAMES
        assert document["antenna_heights"][ELEVEN] == {"GODN": 0.0083, "GODE": 0.0614}

    def test_the_same_span_twice_is_named_by_its_file(self, folder):
        (folder / "godn-gode-11.pos").unlink()
        shutil.copyfile(folder / "godn-gode-00.pos", folder / "godn-gode-again.pos")
        document, _network, _log = _build(folder)
        assert {f"{MIDNIGHT} godn-gode-00.pos", f"{MIDNIGHT} godn-gode-again.pos"} <= set(document["quality"])
