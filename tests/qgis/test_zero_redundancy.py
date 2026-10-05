# SPDX-License-Identifier: GPL-2.0-or-later
"""An adjustment with no redundancy (``specs/06`` section 4.1; P12c-23).

An open levelling line -- a benchmark and three marks levelled one after the
other, never closed -- has as many observations as unknowns. It determines the
heights and checks nothing. Until P12c-23 the a-posteriori variance factor,
``v'Pv / 0``, was used to scale the covariances; it is undefined, every
covariance came out NaN, and the adjustment failed inside numpy with
"Eigenvalues did not converge" instead of producing the heights.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.qgis


@pytest.fixture
def spur(tmp_path) -> Path:
    from geocomp.core.models import ObservationType
    from geocomp.core.units import Unit
    from tests.test_gravimetry_is_levelling import _network

    network = _network(ObservationType.HEIGHT_DIFFERENCE, Unit.METRE, "spur")
    for identifier in list(network.observations):
        if identifier not in ("L0", "L1", "L2"):  # A-B, B-C, C-D: open, never closed
            del network.observations[identifier]
    path = tmp_path / "spur.json"
    path.write_text(json.dumps(network.to_dict()), encoding="utf-8")
    return path


def _adjust(spur: Path, tmp_path: Path) -> dict:
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    from geocomp.algorithms.analysis.common import FRAME_ORDER
    from geocomp.core.adjustment.parameters import Frame

    algorithm = QgsApplication.processingRegistry().algorithmById(
        "geocomp:analysis_network_adjust"
    ).create({})
    results, ok = algorithm.run(
        {
            "NETWORK": str(spur),
            "FRAME": FRAME_ORDER.index(Frame.HEIGHT_1D),
            "DATUM": 0,
            "EPOCH": 2020.0,
            "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
            "OUTPUT_HTML": str(tmp_path / "report.html"),
        },
        QgsProcessingContext(),
        QgsProcessingFeedback(),
        catchExceptions=False,
    )
    assert ok
    return results


class TestAnOpenLevellingLine:
    def test_it_adjusts(self, geocomp_provider, spur, tmp_path):
        results = _adjust(spur, tmp_path)
        assert results["DEGREES_OF_FREEDOM"] == 0

    def test_its_heights_carry_the_observations_precision_propagated(
        self, geocomp_provider, spur, tmp_path
    ):
        """Each line is 2 mm; a mark n lines from the benchmark is 2 mm * sqrt(n)."""
        from geocomp.core.models import Solution

        _adjust(spur, tmp_path)
        solution = Solution.from_dict(
            json.loads((tmp_path / "solution.json").read_text(encoding="utf-8"))
        )
        sigma = {s.station_id: s.position.values[2].std_dev for s in solution.adjusted_stations}
        assert sigma["B"] == pytest.approx(0.002)
        assert sigma["C"] == pytest.approx(0.002 * 2**0.5)
        assert sigma["D"] == pytest.approx(0.002 * 3**0.5)

    def test_its_solution_states_no_a_posteriori_factor(self, geocomp_provider, spur, tmp_path):
        """Undefined, so absent -- not NaN, which a JSON reader need not accept."""
        _adjust(spur, tmp_path)
        text = (tmp_path / "solution.json").read_text(encoding="utf-8")
        assert "NaN" not in text
        statistics = json.loads(text)["statistics"]
        assert statistics.get("variance_factor_aposteriori") is None

    def test_the_report_says_nothing_was_checked(self, geocomp_provider, spur, tmp_path):
        _adjust(spur, tmp_path)
        report = re.sub(r"<[^>]+>", " ", (tmp_path / "report.html").read_text(encoding="utf-8"))
        assert "passed" not in report.split("Global test", 1)[-1].split("Data snooping", 1)[0]
        assert "not tested" in report
        assert "no redundancy" in report.lower()
