# SPDX-License-Identifier: GPL-2.0-or-later
"""An approximate result names its approximations wherever it goes (FR-203; specs/05 criterion 5).

*Every APPROXIMATE result names its strategies in its export, in its report and
in its provenance.* The report did; P12c's audit found the provenance recorded
the mode alone, and the export's statistics sheet the same. A provenance record
travels without its solution -- attached to a bug report, read by a client --
and "approximate" does not say what was approximated.
"""

from __future__ import annotations

import dataclasses

import pytest

import tests.networks as nets
from geocomp.core.adjustment import Frame
from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust, to_solution
from geocomp.core.models import DatumDefinition, HeightType, Project, Provenance, Solution
from geocomp.core.models.epoch import Epoch
from geocomp.core.uncertainty import Strategy, UncertaintyMode
from geocomp.io.store import open_store
from geocomp.io.tabular import sheet_rows


def _solved(network, provenance) -> Solution:
    run = adjust(
        network, AdjustmentOptions(frame=Frame.HEIGHT_1D, datum=DatumDefinition.CONSTRAINED)
    )
    return to_solution(
        run,
        network,
        solution_id="approx",
        crs="EPSG:31982",
        epoch=Epoch.from_decimal_year(2026.0),
        datum=DatumDefinition.CONSTRAINED,
        height_type=HeightType.ORTHOMETRIC,
        provenance=provenance,
    )


@pytest.fixture(scope="module")
def network():
    """RD-03's levelling loop, its sigmas taken from a manufacturer's figure."""
    network = nets.levelling_loop().network
    for identifier, observation in list(network.observations.items()):
        network.observations[identifier] = dataclasses.replace(
            observation,
            values=tuple(v.with_strategy(Strategy.NOMINAL_PRECISION) for v in observation.values),
        )
    return network


@pytest.fixture(scope="module")
def approximate(network) -> Solution:
    # Built before the adjustment, as an algorithm builds it: it cannot know
    # the result's mode or strategies yet.
    return _solved(network, Provenance.now(algorithm_id="geocomp:analysis_network_adjust"))


class TestTheProvenance:
    def test_names_the_strategy(self, approximate):
        assert approximate.uncertainty_mode is UncertaintyMode.APPROXIMATE
        assert approximate.provenance.strategies == frozenset({Strategy.NOMINAL_PRECISION})

    def test_says_what_the_solution_says(self, approximate):
        assert approximate.provenance.strategies == approximate.strategies

    def test_survives_its_document(self, approximate):
        back = Provenance.from_dict(approximate.provenance.to_dict())
        assert back.strategies == approximate.provenance.strategies

    def test_a_rigorous_result_names_none(self):
        rigorous = _solved(nets.levelling_loop().network, Provenance.now(algorithm_id="x"))
        assert rigorous.provenance.strategies == frozenset()
        assert "strategies" not in rigorous.provenance.to_dict()

    def test_a_provenance_that_disagrees_is_put_right(self, approximate):
        """Whoever builds the solution, the provenance cannot contradict it."""
        stale = dataclasses.replace(approximate.provenance, strategies=frozenset())
        rebuilt = dataclasses.replace(approximate, provenance=stale)
        assert rebuilt.provenance.strategies == approximate.strategies


class TestTheStore:
    def test_a_stored_solution_keeps_its_strategies_in_its_provenance(
        self, tmp_path, network, approximate
    ):
        project = Project(id="p", name="P", default_crs="EPSG:31982")
        project.add_network(network)
        with open_store(tmp_path / "p.gpkg", create=True) as store:
            store.write(project)
            store.write_solution(approximate)
        with open_store(tmp_path / "p.gpkg") as store:
            (back,) = [s for s in store.read_solutions() if s.id == approximate.id]
        assert back.provenance.strategies == frozenset({Strategy.NOMINAL_PRECISION})

    def test_the_column_holds_them_not_only_the_covariance(self, tmp_path, network, approximate):
        """A solution derives them as it is read, which would hide a column
        nothing wrote; so the row itself is read here."""
        import json
        import sqlite3

        project = Project(id="p", name="P", default_crs="EPSG:31982")
        project.add_network(network)
        path = tmp_path / "p.gpkg"
        with open_store(path, create=True) as store:
            store.write(project)
            store.write_solution(approximate)
        connection = sqlite3.connect(path)
        (stored,) = connection.execute('SELECT "strategies" FROM "gc_provenance"').fetchone()
        connection.close()
        assert json.loads(stored) == ["NOMINAL_PRECISION"]


class TestTheExport:
    def test_the_statistics_sheet_names_the_strategies(self, approximate):
        _headers, rows = sheet_rows("statistics", solution=approximate)
        values = dict(rows)
        assert values["uncertainty_mode"] == "APPROXIMATE"
        assert values["strategies"] == "NOMINAL_PRECISION"
