# SPDX-License-Identifier: GPL-2.0-or-later
"""The monitoring algorithms, run through Processing (``specs/14``, phase P10b).

The analysis is tested without QGIS in ``tests/test_monitoring.py`` and the
documents in ``tests/test_monitoring_documents.py``. What only a QGIS runtime
can show: that the three algorithms register, take solution documents as the
adjustments write them, read the monitoring roles from a network document,
refuse a moved reference block after recording its localisation, and write the
documents, the report and the styled layers they declare -- criteria 1, 5, 8
and 9 of ``specs/14`` section 9 as a user meets them.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from geocomp.core.models import (
    CoordinateSystem,
    DatumDefinition,
    HeightType,
    MonitoringRole,
    Network,
    Position,
    Station,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from tests.monitoring_network import CRS, LAYOUT, OBJECTS, ORIGIN, REFERENCE, epoch
from tests.qgis.conftest import post_process, requires_modern_field_api, shipped_renderer

pytestmark = pytest.mark.qgis

COMPARE = "geocomp:monitoring_compare_epochs"
SERIES = "geocomp:monitoring_time_series"
REPORT = "geocomp:monitoring_report"


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    return geocomp_provider


def _run(algorithm_id: str, parameters: dict, context=None):
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    context = context or QgsProcessingContext()
    results, ok = algorithm.create({}).run(
        parameters, context, QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok, f"{algorithm_id} reported failure"
    return results, context


def _dump(path: Path, solution) -> str:
    path.write_text(json.dumps(solution.to_dict()), encoding="utf-8")
    return str(path)


def _roles_network(path: Path) -> str:
    """The monitored structure's network document, pillars marked REFERENCE."""
    network = Network(id="dam", crs=CRS)
    for name, (x, y) in LAYOUT.items():
        network.add_station(
            Station(
                id=name,
                approx_position=Position(
                    values=(
                        Quantity.exact(ORIGIN[0] + x, Unit.METRE),
                        Quantity.exact(ORIGIN[1] + y, Unit.METRE),
                        Quantity.exact(0.0, Unit.METRE),
                    ),
                    system=CoordinateSystem.PROJECTED,
                    crs=CRS,
                    height_type=HeightType.NONE,
                ),
                monitoring_role=MonitoringRole.REFERENCE if name in REFERENCE else MonitoringRole.OBJECT,
            )
        )
    path.write_text(json.dumps(network.to_dict()), encoding="utf-8")
    return str(path)


@pytest.fixture(scope="module")
def files(tmp_path_factory):
    folder = tmp_path_factory.mktemp("monitoring")
    stable = epoch(2025.0, seed=1)
    moved = epoch(2026.0, moves={"O2": (0.008, -0.006)}, seed=2)
    pillar = epoch(2026.0, moves={"R3": (0.015, 0.010)}, seed=3)
    thresholds = folder / "thresholds.csv"
    thresholds.write_text("kind,limit,stations,group\nmagnitude,0.006,,structure\n", encoding="utf-8")
    return {
        "folder": folder,
        "stable": _dump(folder / "2025.json", stable),
        "moved": _dump(folder / "2026.json", moved),
        "pillar": _dump(folder / "2026-pillar.json", pillar),
        "held": _dump(folder / "2026-held.json", replace(moved, datum_definition=DatumDefinition.FIXED)),
        "network": _roles_network(folder / "network.json"),
        "thresholds": str(thresholds),
        "series": [
            _dump(
                folder / f"series-{year:.0f}.json",
                epoch(year, moves={"O1": (0.004 * (year - 2024.0), -0.003 * (year - 2024.0))}, seed=10 + n),
            )
            for n, year in enumerate((2024.0, 2025.0, 2026.0))
        ],
    }


def _compare_parameters(files, **extra):
    folder = files["folder"]
    return {
        "FIRST": files["stable"],
        "SECOND": files["moved"],
        "NETWORK": files["network"],
        "CONFIDENCE": 0.99,
        "THRESHOLDS": files["thresholds"],
        "OUTPUT_ANALYSIS": str(folder / "analysis.json"),
        "OUTPUT_HTML": str(folder / "analysis.html"),
        "OUTPUT_DISPLACEMENT_LAYER": None,
        "OUTPUT_DISPLACEMENT_ELLIPSE_LAYER": None,
        **extra,
    }


class TestCompareEpochs:
    @pytest.fixture(scope="class")
    def outcome(self, files):
        return _run(COMPARE, _compare_parameters(files))

    def test_the_roles_come_from_the_network_and_the_motion_is_found(self, outcome):
        from geocomp.core.monitoring import read_comparison_document

        results, _context = outcome
        document = read_comparison_document(json.loads(Path(results["OUTPUT_ANALYSIS"]).read_text()))
        assert document["reference"] == list(REFERENCE)
        assert sorted(document["objects"]) == sorted(OBJECTS)
        assert [d["station"] for d in document["displacements"] if d["significant"]] == ["O2"]
        assert results["REFERENCE_STABLE"] is True
        assert results["SIGNIFICANT_COUNT"] == 1
        assert results["ALERT_COUNT"] >= 1

    def test_the_report_carries_the_decisions_and_the_map(self, outcome):
        results, _context = outcome
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        for section in ("Reference block", "Displacements", "Displacement map", "Alerts", "Deformation"):
            assert section in html
        assert "<svg" in html and "exaggerated" in html
        assert "independent" in html  # the approximation and its bias, never omitted

    def test_a_moved_pillar_is_named_and_the_analysis_refuses(self, files):
        from qgis.core import QgsProcessingException

        folder = files["folder"]
        with pytest.raises(QgsProcessingException) as caught:
            _run(
                COMPARE,
                {
                    "FIRST": files["stable"],
                    "SECOND": files["pillar"],
                    "REFERENCE": ",".join(REFERENCE),
                    "CONFIDENCE": 0.99,
                    "OUTPUT_ANALYSIS": str(folder / "refused.json"),
                    "OUTPUT_HTML": str(folder / "refused.html"),
                },
            )
        assert "R3" in str(caught.value)
        refused = json.loads((folder / "refused.json").read_text())
        assert refused["status"] == "reference_block_unstable"
        assert refused["reference_check"]["implicated"] == ["R3"]
        html = (folder / "refused.html").read_text(encoding="utf-8")
        assert "Analysis refused" in html and "R3" in html

    def test_free_against_held_is_refused_by_name(self, files):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException) as caught:
            _run(COMPARE, {"FIRST": files["stable"], "SECOND": files["held"], "REFERENCE": "R1,R2,R3,R4"})
        assert "dam-2025.0" in str(caught.value) and "datum" in str(caught.value)

    def test_no_reference_block_is_asked_for_not_guessed(self, files):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException) as caught:
            _run(COMPARE, {"FIRST": files["stable"], "SECOND": files["moved"]})
        assert "reference stations" in str(caught.value).lower()


def _series_parameters(files, **extra):
    folder = files["folder"]
    return {
        "SOLUTIONS": list(reversed(files["series"])),
        "REFERENCE": ",".join(REFERENCE),
        "CONFIDENCE": 0.99,
        "OUTPUT_SERIES": str(folder / "series.json"),
        "OUTPUT_CSV": str(folder / "series.csv"),
        "OUTPUT_HTML": str(folder / "series.html"),
        "OUTPUT_VELOCITY_LAYER": None,
        **extra,
    }


class TestTimeSeries:
    @pytest.fixture(scope="class")
    def outcome(self, files):
        return _run(SERIES, _series_parameters(files))

    def test_the_series_the_table_and_the_counts(self, outcome):
        from geocomp.core.monitoring import read_series_document

        results, _context = outcome
        document = read_series_document(json.loads(Path(results["OUTPUT_SERIES"]).read_text()))
        assert [e["epoch"] for e in document["epochs"]] == [2024.0, 2025.0, 2026.0]
        assert results["EPOCH_COUNT"] == 3 and results["STATION_COUNT"] == len(LAYOUT)
        rows = Path(results["OUTPUT_CSV"]).read_text().splitlines()
        assert rows[0] == "station,solution,epoch,component,offset,std_dev"
        assert len(rows) == 1 + len(LAYOUT) * 3 * 2

    def test_the_series_report_plots_every_station(self, outcome):
        results, _context = outcome
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Time series" in html and "Velocities" in html
        assert html.count("<svg") == len(LAYOUT) * 2

    def test_a_block_that_moves_at_one_epoch_stops_the_series(self, files):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException) as caught:
            _run(
                SERIES,
                {
                    "SOLUTIONS": [files["stable"], files["pillar"]],
                    "REFERENCE": ",".join(REFERENCE),
                    "CONFIDENCE": 0.99,
                },
            )
        assert "R3" in str(caught.value) and "dam-2026.0" in str(caught.value)


class TestReport:
    def test_rendered_from_the_saved_documents_alone(self, files):
        folder = files["folder"]
        _run(
            COMPARE,
            {
                "FIRST": files["stable"],
                "SECOND": files["moved"],
                "REFERENCE": ",".join(REFERENCE),
                "OUTPUT_ANALYSIS": str(folder / "a.json"),
                "OUTPUT_HTML": "",
            },
        )
        _run(
            SERIES,
            {
                "SOLUTIONS": files["series"],
                "REFERENCE": ",".join(REFERENCE),
                "OUTPUT_SERIES": str(folder / "s.json"),
            },
        )
        first, _ = _run(
            REPORT,
            {
                "ANALYSIS": str(folder / "a.json"),
                "SERIES": str(folder / "s.json"),
                "OUTPUT_HTML": str(folder / "r1.html"),
            },
        )
        second, _ = _run(
            REPORT,
            {
                "ANALYSIS": str(folder / "a.json"),
                "SERIES": str(folder / "s.json"),
                "OUTPUT_HTML": str(folder / "r2.html"),
            },
        )
        one = Path(first["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert one == Path(second["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Displacements" in one and "Time series" in one

    def test_a_template_cannot_drop_the_premise(self, files, tmp_path):
        from geocomp.core.monitoring import read_comparison_document

        folder = files["folder"]
        template = tmp_path / "brief.html"
        template.write_text("<html><body>{{title}}{{displacements}}</body></html>", encoding="utf-8")
        _run(
            COMPARE,
            {
                "FIRST": files["stable"],
                "SECOND": files["moved"],
                "REFERENCE": ",".join(REFERENCE),
                "OUTPUT_ANALYSIS": str(folder / "b.json"),
            },
        )
        read_comparison_document(json.loads((folder / "b.json").read_text()))
        results, _ = _run(
            REPORT,
            {
                "ANALYSIS": str(folder / "b.json"),
                "TEMPLATE": str(template),
                "OUTPUT_HTML": str(tmp_path / "brief-out.html"),
            },
        )
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Reference block" in html and "Uncertainty" in html and "Compatibility" in html
        assert "uncertainty_notice" not in results["OMITTED"]
        assert "alerts" in results["OMITTED"]

    def test_neither_document_is_refused(self):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException):
            _run(REPORT, {"OUTPUT_HTML": ""})

    def test_a_series_is_not_read_as_an_analysis(self, files):
        from qgis.core import QgsProcessingException

        folder = files["folder"]
        _run(
            SERIES,
            {
                "SOLUTIONS": files["series"],
                "REFERENCE": ",".join(REFERENCE),
                "OUTPUT_SERIES": str(folder / "t.json"),
            },
        )
        with pytest.raises(QgsProcessingException) as caught:
            _run(REPORT, {"ANALYSIS": str(folder / "t.json"), "OUTPUT_HTML": ""})
        assert "geocomp.monitoring.series" in str(caught.value)


@requires_modern_field_api
class TestLayers:
    """Styled, named and categorised -- where QGIS can build a typed field."""

    def test_displacements_and_their_ellipses(self, files):
        from qgis.core import QgsProcessing, QgsProcessingUtils

        folder = files["folder"]
        results, context = _run(
            COMPARE,
            _compare_parameters(
                files,
                OUTPUT_ANALYSIS=str(folder / "layers.json"),
                OUTPUT_HTML="",
                OUTPUT_DISPLACEMENT_LAYER=QgsProcessing.TEMPORARY_OUTPUT,
                OUTPUT_DISPLACEMENT_ELLIPSE_LAYER=QgsProcessing.TEMPORARY_OUTPUT,
            ),
        )
        arrows = QgsProcessingUtils.mapLayerFromString(results["OUTPUT_DISPLACEMENT_LAYER"], context)
        ellipses = QgsProcessingUtils.mapLayerFromString(
            results["OUTPUT_DISPLACEMENT_ELLIPSE_LAYER"], context
        )
        assert arrows.featureCount() == len(REFERENCE) + len(OBJECTS)
        assert ellipses.featureCount() == len(REFERENCE) + len(OBJECTS)
        assert "exaggerated" in arrows.name() and "confidence" in ellipses.name()
        categories = {f["station"]: f["category"] for f in arrows.getFeatures()}
        assert categories["O2"] == "alert"
        assert set(categories.values()) <= {"alert", "significant", "not significant"}
        o2 = next(f for f in arrows.getFeatures() if f["station"] == "O2")
        assert o2["decision"] == "significant" and "magnitude" in o2["alerts"]

    def test_the_velocity_layer_is_tied_to_its_series(self, files):
        from qgis.core import QgsProcessing, QgsProcessingUtils

        from geocomp.algorithms.monitoring.time_series import SERIES_PROPERTY

        folder = files["folder"]
        results, context = _run(
            SERIES,
            _series_parameters(
                files,
                OUTPUT_SERIES=str(folder / "tied.json"),
                OUTPUT_CSV="",
                OUTPUT_HTML="",
                OUTPUT_VELOCITY_LAYER=QgsProcessing.TEMPORARY_OUTPUT,
            ),
        )
        layer = QgsProcessingUtils.mapLayerFromString(results["OUTPUT_VELOCITY_LAYER"], context)
        assert layer.featureCount() == len(LAYOUT)
        assert Path(layer.customProperty(SERIES_PROPERTY)) == Path(results["OUTPUT_SERIES"]).resolve()
        o1 = next(f for f in layer.getFeatures() if f["station"] == "O1")
        assert o1["v_e"] == pytest.approx(0.004, abs=0.001)
        assert o1["epochs"] == 3

    def test_each_draws_with_its_shipped_style(self, files):
        """FR-900 and FR-905: displacement vectors, their ellipses and the
        velocities arrive styled. Until P12c-13 nothing ran their post-processor,
        so a style that never reached them would have passed."""
        from qgis.core import QgsProcessing, QgsProcessingUtils

        folder = files["folder"]
        compared = _run(
            COMPARE,
            _compare_parameters(
                files,
                OUTPUT_ANALYSIS=str(folder / "styled.json"),
                OUTPUT_HTML="",
                OUTPUT_DISPLACEMENT_LAYER=QgsProcessing.TEMPORARY_OUTPUT,
                OUTPUT_DISPLACEMENT_ELLIPSE_LAYER=QgsProcessing.TEMPORARY_OUTPUT,
            ),
        )
        series = _run(
            SERIES,
            _series_parameters(
                files,
                OUTPUT_SERIES=str(folder / "styled-series.json"),
                OUTPUT_CSV="",
                OUTPUT_HTML="",
                OUTPUT_VELOCITY_LAYER=QgsProcessing.TEMPORARY_OUTPUT,
            ),
        )
        for (results, context), output, style in (
            (compared, "OUTPUT_DISPLACEMENT_LAYER", "displacements"),
            (compared, "OUTPUT_DISPLACEMENT_ELLIPSE_LAYER", "displacement_ellipses"),
            (series, "OUTPUT_VELOCITY_LAYER", "velocities"),
        ):
            layer = QgsProcessingUtils.mapLayerFromString(results[output], context)
            post_process(results, output, layer, context)
            assert layer.renderer().dump() == shipped_renderer(style), output
