# SPDX-License-Identifier: GPL-2.0-or-later
"""An adjustment's epoch is stated, or the network's, or marked as assumed (FR-105; P12c).

P12a left three network adjustments falling back to an epoch of their own --
2000.0, 2026.0 for levelling -- when nothing stated one. Their solutions carried
it as though someone had, and a comparison of two such solutions would take
the difference of two conventions for a displacement over zero years.

A solution must carry an epoch, so the fallback stays for a network that states
none. It is marked as assumed in the provenance and in the report, and no
comparison accepts it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import requires_qgis
from tests.networks import trilateration

pytestmark = [pytest.mark.qgis, requires_qgis]


def _adjust(tmp_path: Path, *, network_epoch: float | None = None, stated: float = 0.0):
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    from geocomp.core.models import Solution
    from geocomp.core.models.epoch import Epoch

    network = trilateration().network
    if network_epoch is not None:
        network.epoch = Epoch.from_decimal_year(network_epoch)
    document = tmp_path / "network.json"
    document.write_text(json.dumps(network.to_dict()), encoding="utf-8")
    warnings: list[str] = []

    class Recording(QgsProcessingFeedback):
        def pushWarning(self, text):  # noqa: N802 -- the Qt interface
            warnings.append(text)

    algorithm = (
        QgsApplication.processingRegistry().algorithmById("geocomp:analysis_network_adjust").create({})
    )
    results, ok = algorithm.run(
        {
            "NETWORK": str(document),
            "FRAME": 0,
            "DATUM": 0,
            "EPOCH": stated,
            "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
        },
        QgsProcessingContext(),
        Recording(),
        catchExceptions=False,
    )
    assert ok
    solution = Solution.from_dict(json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8")))
    report = QgsApplication.processingRegistry().algorithmById("geocomp:project_report").create({})
    written, ok = report.run(
        {"SOLUTION": results["OUTPUT_SOLUTION"], "OUTPUT_HTML": str(tmp_path / "report.html")},
        QgsProcessingContext(),
        QgsProcessingFeedback(),
        catchExceptions=False,
    )
    assert ok
    html = Path(written["OUTPUT_HTML"]).read_text(encoding="utf-8")
    return solution, [w for w in warnings if "epoch" in w], html


def test_a_stated_epoch_is_used_and_recorded_as_stated(geocomp_provider, tmp_path):
    solution, warnings, report = _adjust(tmp_path, stated=2025.5)
    assert solution.epoch.decimal_year == 2025.5
    assert solution.provenance.parameters["epoch_origin"] == "stated"
    assert not solution.epoch_assumed and not warnings
    assert "assumed" not in report


def test_unstated_the_networks_own_is_taken(geocomp_provider, tmp_path):
    solution, warnings, _report = _adjust(tmp_path, network_epoch=2024.25)
    assert solution.epoch.decimal_year == pytest.approx(2024.25)
    assert solution.provenance.parameters["epoch_origin"] == "network"
    assert not solution.epoch_assumed and not warnings


def test_with_nothing_stated_the_old_default_is_kept_and_said_to_be_assumed(geocomp_provider, tmp_path):
    solution, warnings, report = _adjust(tmp_path)
    assert solution.epoch.decimal_year == 2000.0
    assert solution.epoch_assumed
    assert any("assumed" in warning for warning in warnings)
    assert "assumed: none was stated" in report
