# SPDX-License-Identifier: GPL-2.0-or-later
"""The two P6 algorithms inside a real QGIS (FR-033).

Everything about the DynAdjust adapter is tested without QGIS, and the
cross-validation itself runs in tier 1. What cannot be tested there is what only
exists inside QGIS: that these two register, that Processing accepts their
parameter declarations, and that ``processAlgorithm`` runs to completion.

**The comparison algorithm runs here for real**, on two solution documents the
test writes -- it needs no engine, because comparing is reading. The adjust
algorithm is only exercised as far as a machine without DynAdjust can take it,
which is the more interesting half of its behaviour anyway: that it fails with a
message telling the user how to get the engine, rather than with a traceback
(ADR-0003).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from geocomp.core.models.epoch import Epoch
from geocomp.core.models.position import CoordinateSystem, HeightType, Position
from geocomp.core.models.solution import (
    AdjustedStation,
    AdjustmentStatistics,
    Solution,
    SolutionKind,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

pytestmark = pytest.mark.qgis

ENGINE_IDS = (
    "geocomp:analysis_dynadjust_adjust",
    "geocomp:analysis_dynadjust_compare",
)
EPOCH = Epoch.from_datetime(datetime(2020, 1, 1, tzinfo=UTC), label="01.01.2020")


def _algorithm(algorithm_id: str):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    return algorithm


def _run(algorithm_id: str, parameters: dict):
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    algorithm = _algorithm(algorithm_id).create({})
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    results, ok = algorithm.run(parameters, context, feedback, catchExceptions=False)
    assert ok, f"{algorithm_id} reported failure"
    return results


def _solution(identifier: str, *, height: float = 3.0) -> Solution:
    position = Position(
        values=(
            Quantity.exact(1.0, Unit.METRE),
            Quantity.exact(2.0, Unit.METRE),
            Quantity.exact(height, Unit.METRE),
        ),
        system=CoordinateSystem.CARTESIAN,
        crs="GDA2020",
        epoch=EPOCH,
        height_type=HeightType.ELLIPSOIDAL,
    )
    return Solution(
        id=identifier,
        network_id="n",
        kind=SolutionKind.ADJUSTMENT,
        crs="GDA2020",
        epoch=EPOCH,
        adjusted_stations=(AdjustedStation(station_id="A", position=position),),
        statistics=AdjustmentStatistics(
            n_observations=6,
            n_parameters=3,
            degrees_of_freedom=3,
            variance_factor_aposteriori=1.0,
        ),
    )


@pytest.fixture
def solutions(tmp_path: Path) -> tuple[str, str]:
    paths = []
    for name, height in (("a.json", 3.0), ("b.json", 3.0)):
        path = tmp_path / name
        path.write_text(json.dumps(_solution(path.stem, height=height).to_dict()))
        paths.append(str(path))
    return paths[0], paths[1]


class TestRegistration:
    @pytest.mark.parametrize("algorithm_id", ENGINE_IDS)
    def test_it_registers_in_the_analysis_group(self, geocomp_provider, algorithm_id):
        assert _algorithm(algorithm_id).groupId() == "analysis"

    @pytest.mark.parametrize("algorithm_id", ENGINE_IDS)
    def test_it_documents_itself(self, geocomp_provider, algorithm_id):
        algorithm = _algorithm(algorithm_id)
        assert algorithm.displayName()
        assert algorithm.displayName() != algorithm.name()
        assert len(algorithm.shortHelpString()) > 200
        assert algorithm.shortDescription()

    @pytest.mark.parametrize("algorithm_id", ENGINE_IDS)
    def test_every_parameter_is_described(self, geocomp_provider, algorithm_id):
        for parameter in _algorithm(algorithm_id).parameterDefinitions():
            assert parameter.description(), f"{algorithm_id}: {parameter.name()}"
            assert parameter.description() != parameter.name()

    def test_the_adjust_algorithm_keeps_the_engine_options_out_of_the_way(
        self, geocomp_provider
    ):
        """FR-034: Basic mode shows what a survey needs, not what an engine
        wrapper needs. A timeout and an install directory are the latter."""
        from qgis.core import QgsProcessingParameterDefinition

        advanced = {
            parameter.name()
            for parameter in _algorithm(ENGINE_IDS[0]).parameterDefinitions()
            if parameter.flags() & QgsProcessingParameterDefinition.FlagAdvanced
        }
        assert {"TIMEOUT", "ENGINE_DIRECTORY", "KEEP_WORKING_FILES"} <= advanced


class TestCompare:
    def test_two_matching_solutions_agree(self, geocomp_provider, solutions, tmp_path):
        reference, other = solutions
        results = _run(
            "geocomp:analysis_dynadjust_compare",
            {
                "REFERENCE": reference,
                "OTHER": other,
                "OUTPUT_REPORT": str(tmp_path / "report.txt"),
                "OUTPUT_JSON": str(tmp_path / "differences.json"),
            },
        )
        assert results["AGREES"] is True
        assert results["DISAGREEMENT_COUNT"] == 0
        assert results["LARGEST_COORDINATE_DIFFERENCE"] == pytest.approx(0.0)

        report = Path(results["OUTPUT_REPORT"]).read_text(encoding="utf-8")
        assert "degrees of freedom" in report
        payload = json.loads(Path(results["OUTPUT_JSON"]).read_text(encoding="utf-8"))
        assert payload["agrees"] is True
        assert payload["coordinate_differences"]["A"] == pytest.approx(0.0)

    def test_a_moved_station_is_reported(self, geocomp_provider, tmp_path):
        reference = tmp_path / "ref.json"
        other = tmp_path / "other.json"
        reference.write_text(json.dumps(_solution("ref").to_dict()))
        other.write_text(json.dumps(_solution("other", height=3.05).to_dict()))
        results = _run(
            "geocomp:analysis_dynadjust_compare",
            {
                "REFERENCE": str(reference),
                "OTHER": str(other),
                "OUTPUT_REPORT": str(tmp_path / "report.txt"),
            },
        )
        assert results["AGREES"] is False
        assert results["DISAGREEMENT_COUNT"] == 1
        assert results["LARGEST_COORDINATE_DIFFERENCE"] == pytest.approx(0.05)

    def test_a_file_that_is_not_a_solution_says_so(self, geocomp_provider, tmp_path):
        """FR-035: name the input that was wrong, and how it was wrong."""
        from qgis.core import QgsProcessingException

        broken = tmp_path / "broken.json"
        broken.write_text("{not json")
        good = tmp_path / "good.json"
        good.write_text(json.dumps(_solution("good").to_dict()))
        with pytest.raises(QgsProcessingException) as excinfo:
            _run(
                "geocomp:analysis_dynadjust_compare",
                {"REFERENCE": str(broken), "OTHER": str(good)},
            )
        assert "JSON" in str(excinfo.value)


class TestAdjustWithoutTheEngine:
    def test_it_says_how_to_get_dynadjust_rather_than_failing_obscurely(
        self, geocomp_provider, tmp_path, monkeypatch
    ):
        """ADR-0003: an engine is an optional dependency, and its absence is a
        message a user can act on -- not an import error, and not a silent
        empty result."""
        from qgis.core import QgsProcessingException

        from tests.networks import trilateration

        monkeypatch.setenv("PATH", str(tmp_path / "no-engines-here"))
        network = tmp_path / "network.json"
        network.write_text(json.dumps(trilateration().network.to_dict()))
        with pytest.raises(QgsProcessingException) as excinfo:
            _run(
                "geocomp:analysis_dynadjust_adjust",
                {"NETWORK": str(network), "OUTPUT_SOLUTION": str(tmp_path / "s.json")},
            )
        message = str(excinfo.value)
        assert "DynAdjust was not found" in message
        assert "DynAdjust directory" in message
