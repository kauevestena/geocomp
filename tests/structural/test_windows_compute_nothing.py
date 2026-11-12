# SPDX-License-Identifier: GPL-2.0-or-later
"""ADR-0010 and FR-011: a menu window computes nothing.

A window writes what was typed as the inputs an algorithm reads, and runs the
algorithm. If a window ever computed a misclosure or a coordinate itself, the
menu and the toolbox would be two implementations again -- the very thing
ADR-0005 was written against -- and the first a user would learn of it is two
different answers.

So three things are held here, without QGIS:

* nothing under ``gui/windows/``, ``gui/workbench/`` or ``jobs/`` imports the
  parts of the core that compute: the adjustment, the techniques, the
  statistics, the monitoring, or an engine;
* every algorithm id written in those modules is a registered one;
* a window's module names only algorithms its ``WindowSpec`` declares -- the
  chain runner refuses any other at run time, and this says so before.
"""

from __future__ import annotations

import ast
import re

import pytest

from geocomp.registry import ALGORITHMS, PROVIDER_ID, WINDOWS
from tests.conftest import PLUGIN_DIR, python_sources

#: The packages that make up the menu's windows.
WINDOW_PACKAGES = ("gui/windows", "gui/workbench", "jobs")

#: The core's computing parts. Models, units, errors, findings and the
#: instrument profiles a reader needs are not computing, and may be imported.
COMPUTING = (
    "geocomp.core.adjustment",
    "geocomp.core.techniques",
    "geocomp.core.statistics",
    "geocomp.core.monitoring",
    "geocomp.core.preanalysis",
    "geocomp.core.geodesy",
    "geocomp.core.geoid",
    "geocomp.core.differentiation",
    "geocomp.core.visualization",
    "geocomp.engines",
)

_ALGORITHM_ID = re.compile(rf"^{PROVIDER_ID}:[a-z0-9_]+$")


def _sources():
    for package in WINDOW_PACKAGES:
        yield from python_sources(PLUGIN_DIR / package)


def _imports(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
    return found


def _algorithm_ids(tree: ast.AST) -> set[str]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and _ALGORITHM_ID.match(node.value)
    }


def test_the_packages_exist():
    """Guards the scan: one that found nothing would pass everything."""
    assert len(list(_sources())) >= 10


def test_no_window_imports_a_computation():
    offenders = []
    for path in _sources():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for name in sorted(_imports(tree)):
            if any(name == root or name.startswith(root + ".") for root in COMPUTING):
                offenders.append(f"{path.relative_to(PLUGIN_DIR.parent)}: {name}")
    assert not offenders, (
        "A menu window computes nothing (ADR-0010): it runs the registered algorithms. "
        "These modules import a computation:\n" + "\n".join(offenders)
    )


def test_every_algorithm_id_they_name_is_registered():
    registered = {spec.id for spec in ALGORITHMS}
    stray = []
    for path in _sources():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        stray.extend(
            f"{path.relative_to(PLUGIN_DIR.parent)}: {algorithm_id}"
            for algorithm_id in sorted(_algorithm_ids(tree) - registered)
        )
    assert not stray, "\n".join(stray)


@pytest.mark.parametrize("spec", WINDOWS, ids=lambda spec: spec.name)
def test_a_window_names_only_the_algorithms_it_declares(spec):
    """The ids a window's own module writes, and the chain it builds, are its own."""
    path = PLUGIN_DIR.parent / (spec.module.replace(".", "/") + ".py")
    named = _algorithm_ids(ast.parse(path.read_text(encoding="utf-8")))
    assert named <= set(spec.algorithm_ids)


def test_the_chains_run_what_their_windows_declare():
    """The chains are declared in ``geocomp.jobs``; each is the chain of one window."""
    from geocomp.jobs import total_station as ts

    book = ts.TotalStationBook(ts.new_job())
    book.table.paste(0, "station", "A\t1.5\tB\tPD\t0 00 00\t90 00 00\t10")
    book.points.paste(0, "name", "A\t0\t0\t0\nB\t10\t0\t0")
    book.sightings.paste(0, "station", "A\t45 00 00\nB\t315 00 00")
    book.job.parameters(ts.WINDOW_RESECTION)["STATION"] = "A"
    chains = {
        ts.WINDOW_FIELD_BOOK: ts.import_chain(book),
        ts.WINDOW_PREPROCESS: ts.preprocess_chain(book),
        ts.WINDOW_TRAVERSE: ts.traverse_chain(book),
        ts.WINDOW_RADIATION: ts.radiation_chain(book),
        ts.WINDOW_RESECTION: ts.resection_chain(book),
        ts.WINDOW_INTERSECTION: ts.intersection_chain(book),
        ts.WINDOW_NETWORK: ts.network_chain(book),
        ts.WINDOW_TRIG_LEVELLING: ts.trig_levelling_chain(book),
    }
    from geocomp.jobs import levelling as lv

    level = lv.LevellingBook(lv.new_job())
    level.table.paste(0, "line", "L\tS1\tBM1\tBS\t1.5\nL\tS1\tT1\tFS\t1.2")
    level.benchmarks.paste(0, "name", "BM1\t100")
    chains.update(
        {
            lv.WINDOW_FIELD_BOOK: lv.import_chain(level),
            lv.WINDOW_EQUAL: lv.equal_chain(level),
            lv.WINDOW_EQUIDISTANT: lv.equidistant_chain(level),
            lv.WINDOW_EXTREME: lv.extreme_chain(level),
            lv.WINDOW_CLOSURES: lv.closures_chain(level),
            lv.WINDOW_NETWORK: lv.network_chain(level),
        }
    )
    declared = {spec.name: spec.algorithm_ids for spec in WINDOWS}
    assert set(chains) == set(declared), "a window without a chain here is not checked"
    for window, chain in chains.items():
        assert chain.algorithms == declared[window], window
