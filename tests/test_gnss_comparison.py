# SPDX-License-Identifier: GPL-2.0-or-later
"""Comparing configurations, and why significance is the answer (FR-359).

``specs/11-module-gnss.md`` section 6. The check that matters is not that the
differences are computed -- subtraction is not at risk -- but that a difference
is judged against the covariances rather than against intuition. The two cases
below are the same 3 mm difference, significant with one pair of covariances and
not with the other, which is the whole claim of the module.
"""

from __future__ import annotations

import numpy as np
import pytest

from geocomp.core.errors import DataError
from geocomp.core.models import BaselineFrame
from geocomp.core.techniques.gnss.baselines import Baseline, components_from_covariance
from geocomp.core.techniques.gnss.comparison import compare_baselines
from geocomp.core.uncertainty import Covariance, Strategy, UncertaintyMode
from geocomp.core.units import Unit
from tests.conftest import requires_rtklib

VECTOR = (2022.7707, -468.6291, 2610.2891)


def baseline(identifier, offset=(0.0, 0.0, 0.0), sigma=0.0005):
    covariance = Covariance(
        matrix=np.eye(3) * sigma**2,
        labels=("x", "y", "z"),
        units=(Unit.METRE,) * 3,
    )
    values = tuple(v + d for v, d in zip(VECTOR, offset, strict=True))
    return Baseline(
        id=identifier,
        base_station="3040",
        rover_station="0759",
        components=components_from_covariance(values, covariance),
        covariance=covariance,
        base_horizon=(0.613, 2.437),
        rover_horizon=(0.613, 2.437),
        frame=BaselineFrame.ECEF,
    )


class TestTheSameDifferenceCanBeSignificantOrNot:
    """3 mm against 0.5 mm sigmas, and 3 mm against 5 mm sigmas."""

    def test_a_difference_large_against_its_covariance_is_significant(self):
        comparison = compare_baselines(
            {"tight-a": baseline("a", sigma=0.0005),
             "tight-b": baseline("b", offset=(0.003, 0, 0), sigma=0.0005)}
        )
        row = comparison.rows[0]
        assert row.magnitude == pytest.approx(0.003)
        assert row.is_significant
        assert comparison.any_significant

    def test_the_same_difference_small_against_its_covariance_is_not(self):
        comparison = compare_baselines(
            {"loose-a": baseline("a", sigma=0.005),
             "loose-b": baseline("b", offset=(0.003, 0, 0), sigma=0.005)}
        )
        row = comparison.rows[0]
        assert row.magnitude == pytest.approx(0.003)
        assert not row.is_significant
        assert not comparison.any_significant

    def test_identical_solutions_are_never_significant(self):
        comparison = compare_baselines({"a": baseline("a"), "b": baseline("b")})
        assert comparison.rows[0].statistic == pytest.approx(0.0)
        assert not comparison.rows[0].is_significant


class TestTheStatisticAndItsAssumption:
    def test_the_statistic_is_the_quadratic_form_it_claims(self):
        sigma = 0.001
        comparison = compare_baselines(
            {"a": baseline("a", sigma=sigma),
             "b": baseline("b", offset=(0.002, 0.0, 0.0), sigma=sigma)}
        )
        # d^T (Sigma_a + Sigma_b)^-1 d with both diagonal: 0.002^2 / (2 sigma^2).
        assert comparison.rows[0].statistic == pytest.approx(0.002**2 / (2 * sigma**2))

    def test_the_independence_assumption_is_recorded_not_hidden(self):
        """FR-202, FR-203: the simplification is named on the result.

        The two runs share their observations, so this is conservative --
        it overstates the difference's uncertainty. Saying so is what lets a
        report distinguish 'not significant' from 'not tested properly'.
        """
        comparison = compare_baselines({"a": baseline("a"), "b": baseline("b")})
        covariance = comparison.rows[0].covariance
        assert covariance.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.INDEPENDENCE_ASSUMED in covariance.strategies

    def test_a_higher_confidence_makes_a_marginal_difference_insignificant(self):
        # chi2(0.95, 3) = 7.815 and chi2(0.999, 3) = 16.27; a 4.5 mm difference
        # against 1 mm sigmas gives 10.125, which sits between them.
        pair = {"a": baseline("a", sigma=0.001),
                "b": baseline("b", offset=(0.0045, 0.0, 0.0), sigma=0.001)}
        assert compare_baselines(pair, confidence=0.95).rows[0].is_significant
        assert not compare_baselines(pair, confidence=0.999).rows[0].is_significant

    def test_the_length_difference_is_reported_beside_the_components(self):
        comparison = compare_baselines(
            {"a": baseline("a"), "b": baseline("b", offset=(0.01, 0.0, 0.0))}
        )
        assert comparison.rows[0].length_difference != 0.0


class TestWhatItRefuses:
    def test_one_configuration_is_not_a_comparison(self):
        with pytest.raises(DataError, match="comparison_needs_two_configurations"):
            compare_baselines({"only": baseline("a")})

    def test_different_station_pairs_are_refused(self):
        other = baseline("b")
        object.__setattr__(other, "rover_station", "9999")
        with pytest.raises(DataError, match="comparison_mixed_station_pairs"):
            compare_baselines({"a": baseline("a"), "b": other})

    def test_mixed_frames_are_refused(self):
        rotated = baseline("b")
        object.__setattr__(rotated, "frame", BaselineFrame.LOCAL)
        with pytest.raises(DataError, match="comparison_mixed_frames"):
            compare_baselines({"a": baseline("a"), "b": rotated})

    def test_an_unknown_reference_names_the_configurations(self):
        with pytest.raises(DataError, match="comparison_reference_not_found") as caught:
            compare_baselines({"a": baseline("a"), "b": baseline("b")}, reference="c")
        assert "a" in caught.value.context["expected"]


class TestThePresentation:
    def test_the_table_has_a_header_and_one_row_per_configuration(self):
        comparison = compare_baselines(
            {"ref": baseline("a"), "one": baseline("b"), "two": baseline("c")}
        )
        table = comparison.table()
        assert table[0][0] == "configuration"
        assert len(table) == 3  # header plus two compared configurations
        assert {row[0] for row in table[1:]} == {"one", "two"}

    def test_the_reference_defaults_to_the_first_given(self):
        comparison = compare_baselines({"first": baseline("a"), "second": baseline("b")})
        assert comparison.reference == "first"
        assert [row.name for row in comparison.rows] == ["second"]

    def test_the_dictionary_carries_the_decision_and_its_threshold(self):
        payload = compare_baselines({"a": baseline("a"), "b": baseline("b")}).to_dict()
        assert payload["confidence"] == pytest.approx(0.95)
        assert payload["critical_value"] > 0
        assert payload["any_significant"] is False


@requires_rtklib
class TestTwoMasksOverRealData:
    """Tier 4: RTKLIB's sample baseline processed live at two masks, then compared.

    What the stand-in engine of ``tests/qgis/test_configuration_comparison.py``
    cannot show: two real runs that differ, compared. The sample is clean and
    short, so no particular verdict is asserted -- only that the masks reach the
    engine, the comparison is formed from what it determined, and its numbers
    are the solutions'.

    Written for P12c-43, it found the reader's defect: at 30 degrees one epoch's
    printed covariance is marginally indefinite, and until then the whole run was
    refused (``tests/test_pos_reader.py::TestAnEpochPrintedIndefinite``).
    """

    @pytest.fixture(scope="class")
    def compared(self, tmp_path_factory):
        from pathlib import Path

        from geocomp.engines.rtklib import RtklibEngine, RtklibJob, profile
        from geocomp.engines.rtklib.baseline import baseline_from_solution
        from geocomp.io.gnss_discovery import scan_folder

        data = Path(__file__).resolve().parent / "data" / "rtklib"
        sessions = {session.station_id: session for session in scan_folder(data).sessions}
        engine = RtklibEngine()
        baselines = {}
        for mask in (10.0, 30.0):
            result = engine.run(
                RtklibJob(
                    rover=sessions["0759"],
                    base=sessions["3040"],
                    config=profile("relative-static").with_options(
                        output_format="xyz", elevation_mask=mask
                    ),
                ),
                work_dir=tmp_path_factory.mktemp(f"mask-{mask:g}"),
            )
            baselines[f"mask {mask:g}"] = baseline_from_solution(
                result.solution, base_station="3040", rover_station="0759"
            )
        return baselines, compare_baselines(baselines)

    def test_the_masks_determine_two_different_baselines(self, compared):
        baselines, _comparison = compared
        low, high = (np.array([q.value for q in b.components]) for b in baselines.values())
        assert np.linalg.norm(low - high) > 0.0

    def test_the_comparison_is_of_what_they_determined(self, compared):
        baselines, comparison = compared
        (row,) = comparison.rows
        low, high = (np.array([q.value for q in b.components]) for b in baselines.values())
        assert comparison.reference == "mask 10"
        np.testing.assert_allclose(row.difference, high - low, atol=1e-12)
        assert np.isfinite(row.statistic) and row.statistic >= 0.0
