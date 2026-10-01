# SPDX-License-Identifier: GPL-2.0-or-later
"""What a monitoring result draws (``specs/19`` sections 1 and 3, phase P10b).

Checked against the geometry's own definition rather than against QGIS: the
arrow starts where the first epoch put the station and ends at the exaggerated
displacement, the confidence ellipse is centred on the tip, a geocentric
station's arrow is turned by its grid convergence, and the category a style
draws is the decision -- or the alert, which outranks it.
"""

from __future__ import annotations

import math
from xml.etree import ElementTree

import pytest

from geocomp.core.monitoring import (
    analyse,
    compare,
    comparison_document,
    evaluate_alerts,
    series,
    series_document,
    thresholds_from_rows,
)
from geocomp.core.visualization.monitoring import (
    ALERT,
    displacement_exaggeration,
    drawn_displacements,
    drawn_velocities,
    velocity_exaggeration,
)
from geocomp.core.visualization.svg import MapText, PlotText, displacement_map, series_plot

from .monitoring_network import REFERENCE, epoch

CONFIDENCE = 0.99


@pytest.fixture(scope="module")
def document():
    first, second = epoch(2025.0, seed=1), epoch(2026.0, moves={"O2": (0.008, -0.006)}, seed=2)
    analysis = analyse(compare(first, second), REFERENCE, confidence=CONFIDENCE)
    thresholds = thresholds_from_rows([["horizontal", "0.002", "O4", "crest"]])
    return comparison_document(
        analysis,
        first,
        second,
        thresholds=thresholds,
        alerts=evaluate_alerts(thresholds, displacements=analysis.displacements),
    )


def _by_station(drawn):
    return {d.station: d for d in drawn}


class TestDisplacements:
    def test_an_arrow_from_the_first_epoch_to_the_exaggerated_displacement(self, document):
        drawn = _by_station(drawn_displacements(document, exaggeration=500.0))
        o2 = drawn["O2"]
        east, north = document["display"]["positions"]["O2"]
        d_e, d_n = o2.record["values"]
        assert o2.tail == pytest.approx((east, north))
        assert o2.tip == pytest.approx((east + 500.0 * d_e, north + 500.0 * d_n))
        assert o2.exaggeration == 500.0

    def test_the_confidence_ellipse_is_centred_on_the_tip(self, document):
        o2 = _by_station(drawn_displacements(document, exaggeration=500.0))["O2"]
        ring = o2.ellipse.ring[:-1]
        centre = (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))
        assert centre == pytest.approx(o2.tip, abs=1e-6)
        assert o2.ellipse.confidence == CONFIDENCE
        assert o2.ellipse.semi_major == pytest.approx(o2.record["ellipse"]["semi_major"])
        assert o2.ellipse.exaggeration == 500.0

    def test_zero_lies_outside_a_significant_ellipse_and_inside_a_still_one(self, document):
        drawn = _by_station(drawn_displacements(document, exaggeration=500.0))

        def contains(d, point):
            e = d.record["ellipse"]
            dx, dy = point[0] - d.tip[0], point[1] - d.tip[1]
            a = e["orientation"]
            along = (dx * math.sin(a) + dy * math.cos(a)) / (500.0 * e["semi_major"])
            across = (dx * math.cos(a) - dy * math.sin(a)) / (500.0 * e["semi_minor"])
            return along**2 + across**2 <= 1.0

        assert not contains(drawn["O2"], drawn["O2"].tail)
        assert contains(drawn["O3"], drawn["O3"].tail)

    def test_the_category_is_the_decision_unless_an_alert_outranks_it(self, document):
        drawn = _by_station(drawn_displacements(document, exaggeration=100.0))
        assert drawn["O2"].category == "significant"
        assert drawn["O5"].category == "not significant"
        o4 = drawn["O4"]
        assert o4.record["decision"] == "not significant"
        if o4.record["horizontal_magnitude"] > 0.002:
            assert o4.category == ALERT and o4.alerts == ("horizontal",)
        else:
            assert o4.category == "not significant" and o4.alerts == ()

    def test_a_first_factor_fits_the_largest_arrow_to_the_network(self, document):
        factor = displacement_exaggeration(document)
        largest = max(d["horizontal_magnitude"] for d in document["displacements"])
        assert 0.02 * 1200.0 < factor * largest <= 0.15 * 900.0

    def test_a_station_with_no_place_is_not_drawn(self, document):
        placeless = {
            **document,
            "display": {**document["display"], "positions": {"O2": document["display"]["positions"]["O2"]}},
        }
        assert [d.station for d in drawn_displacements(placeless, exaggeration=10.0)] == ["O2"]
        assert displacement_exaggeration(placeless) == 1.0


class TestGridConvergence:
    def test_a_geocentric_arrow_turns_by_the_bearing_of_north(self, document):
        turned = {
            **document,
            "display": {
                **document["display"],
                "rotations": {station: math.radians(1.5) for station in document["display"]["positions"]},
            },
        }
        plain = _by_station(drawn_displacements(document, exaggeration=1000.0))["O2"]
        rotated = _by_station(drawn_displacements(turned, exaggeration=1000.0))["O2"]
        length = math.dist(plain.tail, plain.tip)
        assert math.dist(rotated.tail, rotated.tip) == pytest.approx(length)

        def azimuth(d):
            return math.atan2(d.tip[0] - d.tail[0], d.tip[1] - d.tail[1])

        assert azimuth(rotated) - azimuth(plain) == pytest.approx(math.radians(1.5))
        assert rotated.ellipse.orientation == pytest.approx(
            (plain.ellipse.orientation + math.radians(1.5)) % math.pi
        )


@pytest.fixture(scope="module")
def series_payload():
    solutions = [
        epoch(year, moves={"O1": (0.004 * (year - 2024.0), -0.003 * (year - 2024.0))}, seed=10 + n)
        for n, year in enumerate((2024.0, 2025.0, 2026.0))
    ]
    thresholds = thresholds_from_rows([["velocity", "0.003", "", ""]])
    stations = series(solutions, reference=REFERENCE, confidence=CONFIDENCE)
    return series_document(
        stations,
        solutions,
        reference=REFERENCE,
        datum="translation_rotation",
        confidence=CONFIDENCE,
        thresholds=thresholds,
        alerts=evaluate_alerts(thresholds, series=stations),
    )


class TestVelocities:
    def test_a_years_motion_exaggerated(self, series_payload):
        o1 = _by_station(drawn_velocities(series_payload, exaggeration=1000.0))["O1"]
        v_e, v_n = o1.record["velocity"]
        east, north = series_payload["display"]["positions"]["O1"]
        assert o1.tip == pytest.approx((east + 1000.0 * v_e, north + 1000.0 * v_n))
        assert o1.category == ALERT and o1.alerts == ("velocity",)

    def test_a_first_factor_for_velocities(self, series_payload):
        assert velocity_exaggeration(series_payload) > 1.0


# -- the report's pictures -----------------------------------------------------------


SVG = "{http://www.w3.org/2000/svg}"
MAP_TEXT = MapText(
    caption="arrows and ellipses exaggerated 500x",
    legend={"alert": "Alert", "significant": "Significant", "not significant": "Not significant"},
    reference="reference",
    obj="object",
)
PLOT_TEXT = PlotText(
    title="O1 — east", x_label="epoch", y_label="offset (mm)", band="band", fit="fit", threshold="limit"
)


class TestReportMap:
    def test_well_formed_deterministic_and_stating_its_factor(self, document):
        first = displacement_map(document, exaggeration=500.0, text=MAP_TEXT)
        assert first == displacement_map(document, exaggeration=500.0, text=MAP_TEXT)
        root = ElementTree.fromstring(first)
        assert root.tag == f"{SVG}svg"
        texts = " ".join(element.text or "" for element in root.iter(f"{SVG}text"))
        assert "exaggerated 500x" in texts
        assert len(list(root.iter(f"{SVG}line"))) >= len(document["displacements"])

    def test_nothing_placed_draws_nothing(self, document):
        placeless = {**document, "display": {**document["display"], "positions": {}}}
        assert displacement_map(placeless, exaggeration=500.0, text=MAP_TEXT) == ""


class TestReportPlot:
    def test_a_series_plot_with_its_band_fit_and_limits(self, series_payload):
        o1 = {s["station"]: s for s in series_payload["stations"]}["O1"]
        svg = series_plot(o1, "e", band_factor=2.0, thresholds=(0.005,), text=PLOT_TEXT)
        root = ElementTree.fromstring(svg)
        dashed = [line for line in root.iter(f"{SVG}line") if line.get("stroke-dasharray") == "6 4"]
        assert len(dashed) == 2  # the limit, above and below zero
        circles = list(root.iter(f"{SVG}circle"))
        assert len(circles) == len(o1["points"])
        assert svg == series_plot(o1, "e", band_factor=2.0, thresholds=(0.005,), text=PLOT_TEXT)
