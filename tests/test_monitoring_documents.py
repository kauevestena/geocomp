# SPDX-License-Identifier: GPL-2.0-or-later
"""The saved results of a monitoring run (``specs/14`` section 8.2, phase P10b).

The report, the map layers and the time-series panel all read these documents,
so what is tested here is what all three can rely on: that a document carries
the whole result, survives JSON unchanged, refuses to be read as something it
is not, and places each station where the map should draw it.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.monitoring import (
    AlertKind,
    Finding,
    analyse,
    check_reference,
    compare,
    comparison_document,
    default_datum,
    evaluate_alerts,
    read_comparison_document,
    read_series_document,
    refused_document,
    series,
    series_document,
    strain,
    thresholds_from_rows,
)

from .monitoring_network import OBJECTS, REFERENCE, epoch
from .test_monitoring import POSITIONS, _geocentric, _levelling

CONFIDENCE = 0.99


@pytest.fixture(scope="module")
def epochs():
    return epoch(2025.0, seed=1), epoch(2026.0, moves={"O2": (0.008, -0.006)}, seed=2)


@pytest.fixture(scope="module")
def document(epochs):
    first, second = epochs
    analysis = analyse(compare(first, second), REFERENCE, confidence=CONFIDENCE)
    thresholds = thresholds_from_rows([["magnitude", "0.005", "", "structure"]])
    return comparison_document(
        analysis,
        first,
        second,
        strain=strain(analysis),
        thresholds=thresholds,
        alerts=evaluate_alerts(thresholds, displacements=analysis.displacements),
    )


def _round_trip(payload):
    return json.loads(json.dumps(payload))


class TestComparisonDocument:
    def test_it_survives_json_unchanged(self, document):
        assert _round_trip(document) == document
        assert read_comparison_document(_round_trip(document)) == document

    def test_it_carries_every_epoch_and_every_displacement(self, document, epochs):
        assert document["status"] == "analysed"
        assert [e["solution"] for e in document["epochs"]] == [s.id for s in epochs]
        assert [e["epoch"] for e in document["epochs"]] == [2025.0, 2026.0]
        assert {d["station"] for d in document["displacements"]} == set(REFERENCE) | set(OBJECTS)
        moved = {d["station"]: d for d in document["displacements"]}["O2"]
        assert moved["decision"] == "significant" and moved["significant"] is True
        assert moved["values"][0] == pytest.approx(0.008, abs=0.003)
        assert np.shape(moved["covariance"]) == (2, 2)
        assert moved["ellipse"]["confidence"] == CONFIDENCE

    def test_not_significant_keeps_its_value(self, document):
        still = {d["station"]: d for d in document["displacements"]}["O4"]
        assert still["decision"] == "not significant"
        assert still["magnitude"] > 0.0 and all(s > 0.0 for s in still["std_devs"])

    def test_the_approximation_is_stated(self, document):
        assert document["mode"] == "approximate"
        assert document["strategies"] == ["independence_assumed"]

    def test_block_global_test_strain_and_alerts(self, document):
        assert document["reference_check"]["passed"] is True
        assert document["reference_check"]["steps"] == []
        assert document["global_test"]["passed"] is False
        assert document["strain"]["stations"] == list(OBJECTS)
        exceeded = [a["station"] for a in document["alerts"] if a["exceeded"]]
        assert exceeded == ["O2"]
        assert document["thresholds"] == [
            {"kind": "magnitude", "limit": 0.005, "stations": None, "group": "structure"}
        ]

    def test_stations_are_drawn_where_the_first_epoch_put_them(self, document, epochs):
        first = epochs[0]
        positions = document["display"]["positions"]
        for station in first.adjusted_stations:
            east, north, _ = (q.value for q in station.position.values)
            assert positions[station.station_id] == pytest.approx([east, north])
        assert document["display"]["crs"] == first.crs
        assert document["display"]["rotations"] == {}

    def test_without_strain_the_reason_is_kept(self, epochs):
        first, second = epochs
        analysis = analyse(compare(first, second), REFERENCE, confidence=CONFIDENCE)
        payload = comparison_document(analysis, first, second, strain_note="not_requested")
        assert payload["strain"] is None and payload["strain_note"] == "not_requested"


class TestRefusedDocument:
    def test_a_moved_block_is_a_document_with_its_localisation(self, epochs):
        first = epochs[0]
        second = epoch(2026.0, moves={"R3": (0.015, 0.010)}, seed=3)
        comparison = compare(first, second)
        check = check_reference(comparison, REFERENCE, confidence=CONFIDENCE)
        payload = refused_document(
            comparison,
            check,
            first,
            second,
            reference=REFERENCE,
            datum=default_datum(comparison),
            confidence=CONFIDENCE,
        )
        assert payload["status"] == "reference_block_unstable"
        assert payload["reference_check"]["passed"] is False
        assert payload["reference_check"]["implicated"] == ["R3"]
        assert payload["reference_check"]["steps"][0]["removed"] == "R3"
        assert payload["displacements"] == [] and payload["global_test"] is None
        assert read_comparison_document(_round_trip(payload)) == payload


class TestGeocentricDisplay:
    def test_a_geocentric_comparison_is_drawn_in_its_frames_utm_grid(self):
        first = _geocentric("gnss-1", "ITRF2020", 2025.0, POSITIONS)
        second = _geocentric("gnss-2", "ITRF2020", 2026.0, POSITIONS)
        analysis = analyse(compare(first, second), ("A",), confidence=CONFIDENCE)
        payload = comparison_document(analysis, first, second)
        display = payload["display"]
        assert display["name"].startswith("ITRF2020 / UTM zone")
        east, north = display["positions"]["A"]
        assert 100_000 < east < 900_000 and 0 < north < 10_000_000
        assert set(display["rotations"]) == {"A", "B"}
        assert all(abs(r) < 0.1 for r in display["rotations"].values())


class TestHeightsOnly:
    def test_nothing_to_place_it_means_no_map(self):
        first, second = _levelling(2025.0), _levelling(2026.0, sink={"P2": -0.004}, seed=2)
        analysis = analyse(compare(first, second), ("B1", "B2", "B3"), confidence=CONFIDENCE)
        payload = comparison_document(analysis, first, second)
        assert payload["display"]["positions"] == {}
        assert payload["components"] == ["h"]


@pytest.fixture(scope="module")
def solutions():
    return [
        epoch(year, moves={"O1": (0.004 * (year - 2024.0), -0.003 * (year - 2024.0))}, seed=10 + n)
        for n, year in enumerate((2024.0, 2025.0, 2026.0))
    ]


class TestSeriesDocument:
    def test_it_carries_every_epoch_and_the_velocity(self, solutions):
        stations = series(solutions, reference=REFERENCE, confidence=CONFIDENCE)
        payload = series_document(
            stations, solutions, reference=REFERENCE, datum="translation_rotation", confidence=CONFIDENCE
        )
        assert _round_trip(payload) == payload
        assert read_series_document(_round_trip(payload)) == payload
        assert [e["epoch"] for e in payload["epochs"]] == [2024.0, 2025.0, 2026.0]
        o1 = {s["station"]: s for s in payload["stations"]}["O1"]
        assert len(o1["points"]) == 3
        assert o1["velocity"][0] == pytest.approx(0.004, abs=0.001)
        assert o1["speed"] == pytest.approx(0.005, abs=0.0015)
        assert payload["mode"] == "approximate"
        assert payload["strategies"] == ["independence_assumed"]

    def test_a_settlement_series_is_judged_on_its_vertical_rate(self):
        solutions = [_levelling(2024.0 + n, sink={"P2": -0.003 * n}, seed=20 + n) for n in range(3)]
        stations = {s.station_id: s for s in series(solutions, reference=("B1", "B2", "B3"))}
        assert stations["P2"].horizontal_speed is None
        assert stations["P2"].speed == pytest.approx(0.003, abs=0.001)
        alerts = evaluate_alerts(
            thresholds_from_rows([["velocity", "0.002", "P2", ""]]), series=stations.values()
        )
        assert [a.exceeded for a in alerts] == [True]


class TestReading:
    def test_a_series_is_not_read_as_a_comparison(self, document):
        with pytest.raises(ValidationError) as caught:
            read_series_document(document)
        assert caught.value.code.endswith("monitoring_document_kind")

    def test_another_version_is_refused(self, document):
        with pytest.raises(ValidationError) as caught:
            read_comparison_document({**document, "version": 99})
        assert caught.value.code.endswith("monitoring_document_version")

    def test_an_incomplete_document_names_what_is_missing(self, document):
        payload = {key: value for key, value in document.items() if key != "displacements"}
        with pytest.raises(ValidationError) as caught:
            read_comparison_document(payload)
        assert caught.value.context["missing"] == ["displacements"]

    def test_not_a_document_at_all(self):
        with pytest.raises(ValidationError):
            read_comparison_document(["not", "a", "document"])


class TestThresholds:
    def test_a_file_of_criteria(self):
        rows = [
            ["kind", "limit", "stations", "group"],
            ["# settlement of the crest"],
            [],
            ["vertical", "0.005", "O1; O2 O3", "crest"],
            ["significance", "", "O5"],
            ["Velocity", "0.002"],
        ]
        vertical, significance, velocity = thresholds_from_rows(rows)
        assert vertical.kind is AlertKind.VERTICAL and vertical.limit == 0.005
        assert vertical.stations == frozenset({"O1", "O2", "O3"}) and vertical.group == "crest"
        assert significance.kind is AlertKind.SIGNIFICANCE and significance.stations == frozenset({"O5"})
        assert velocity.kind is AlertKind.VELOCITY and velocity.stations is None

    @pytest.mark.parametrize(
        ("row", "received"),
        [(["tilt", "0.1"], "tilt"), (["magnitude", "ten"], "ten"), (["horizontal", ""], "(empty)")],
    )
    def test_a_bad_row_is_named(self, row, received):
        with pytest.raises(ValidationError) as caught:
            thresholds_from_rows([["kind", "limit"], row])
        assert caught.value.code.endswith("monitoring_threshold_row")
        assert caught.value.context["row"] == 2 and caught.value.context["received"] == received

    def test_a_limit_that_is_not_positive_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            thresholds_from_rows([["magnitude", "-0.01"]])
        assert caught.value.code.endswith("monitoring_alert_limit")


class TestFindings:
    def test_a_finding_is_a_code_with_its_values(self):
        finding = Finding("stations_in_one_epoch", {"stations": ["X1", "X2"]})
        assert finding.to_dict() == {"code": "stations_in_one_epoch", "context": {"stations": ["X1", "X2"]}}
        assert str(finding) == "stations in one epoch only, not compared: X1, X2"

    def test_a_station_one_epoch_lacks_is_a_finding_in_the_document(self, epochs):
        first, second = epochs
        from dataclasses import replace

        fewer = replace(
            second, adjusted_stations=tuple(s for s in second.adjusted_stations if s.station_id != "O5")
        )
        analysis = analyse(compare(first, fewer), REFERENCE, confidence=CONFIDENCE)
        payload = comparison_document(analysis, first, fewer)
        assert {"code": "stations_in_one_epoch", "context": {"stations": ["O5"]}} in payload["findings"]
