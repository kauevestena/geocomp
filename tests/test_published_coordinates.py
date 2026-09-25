# SPDX-License-Identifier: GPL-2.0-or-later
"""What a *clean* pair does against a published coordinate.

RD-06's accuracy criterion had never been met, and until the maintainer
supplied an ANTEX on 24 September 2026 the reason could not be separated from
the reference case's own two defects. It now can: fourteen independent pairs,
every one exactly calibrated, miss the same 1 mm tolerance. These tests read
the recorded measurement offline and fail if the conclusion it supports stops
being the conclusion the numbers show.

The measurement itself is `scripts/check_published_coordinates.py`, which needs
an engine and an ANTEX; see `specs/22` section 5.4.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "tests/data/published_coordinates"
ANTENNA = "TRM41249USCG    SCIT"


@pytest.fixture(scope="module")
def observed() -> dict:
    return json.loads((DATA / "observed.json").read_text())


class TestEveryPairWasActuallyJudgeable:
    """A number from a mislabelled run is worse than no number, so the first
    thing to establish is that these fourteen comparisons could be made at
    all -- which GODE's could not."""

    def test_every_pair_resolved_its_own_antenna_and_radome(self, observed):
        for row in observed["results"]:
            assert sorted(row["antennas"].values()) == [ANTENNA, ANTENNA], row["pair"]

    def test_the_pairs_are_short_enough_for_this_engine(self, observed):
        """Beyond about 4 km the ionosphere dominates and the ionosphere-free
        combination resolves no ambiguities; `specs/22` section 5.2."""
        for row in observed["results"]:
            assert 10.0 < row["length_m"] < 100.0, row["pair"]

    def test_all_fourteen_are_present(self, observed):
        assert observed["pairs"] == len(observed["results"]) == 14


class TestTheCriterionIsUnreachableOnCleanPairs:
    """The finding itself. Not one clean pair reaches 1 mm per component."""

    def test_no_pair_meets_the_rd06_tolerance(self, observed):
        assert observed["pairs_passing_1mm_per_component"] == 0
        assert all(not row["passes_1mm_per_component"] for row in observed["results"])

    def test_the_typical_miss_is_several_millimetres(self, observed):
        assert 3.0 < observed["median_max_abs_xyz_mm"] < 10.0

    def test_the_best_pair_still_misses(self, observed):
        """Even the closest pair is over the limit, so this is not a matter of
        finding a better station."""
        best = min(row["max_abs_xyz_mm"] for row in observed["results"])
        assert best > 1.0


class TestTheMissBelongsToTheReferenceNotTheEstimator:
    """Three independent discriminators, each of which the estimator would
    fail if the error were its own."""

    def test_a_pair_repeats_itself_far_better_than_pairs_agree(self, observed):
        """The load-bearing comparison. Day to day the same pair repeats to a
        few tenths of a millimetre; between pairs the answers differ by
        millimetres. Random solution error cannot do that."""
        within = observed["median_day_to_day_sd_enu_mm"]
        between = observed["between_pair_sd_of_mean_error_enu_mm"]
        for axis in range(3):
            assert within[axis] < 0.6, axis
            assert between[axis] > 4.0 * within[axis], axis

    def test_each_pair_holds_its_own_offset_across_three_days(self, observed):
        for row in observed["results"]:
            assert max(row["day_to_day_sd_enu_mm"]) < 2.0, row["pair"]

    def test_the_offset_does_not_move_with_the_elevation_mask(self, observed):
        """Low-elevation multipath is strongly mask-dependent; a wrong
        coordinate is not. AIS5-AIS6 is 21 mm north at a 10 degree mask and
        21 mm north at 30."""
        sweep = observed["mask_invariance_mm"]
        assert sweep["AIS5-AIS6"]["spread_over_10_to_30deg"] < 1.0
        assert sweep["AIS5-AIS6"]["north_at_10deg"] > 20.0
        assert sweep["AIS5-AIS6"]["north_at_30deg"] > 20.0
        for pair in sweep.values():
            assert pair["spread_over_10_to_30deg"] < 2.0


class TestTheSourcesArePinned:
    def test_every_source_is_hashed_and_from_the_open_mirror(self):
        entries = json.loads((DATA / "source_manifest.json").read_text())
        assert len(entries) == 117
        for entry in entries:
            assert entry["url"].startswith("https://noaa-cors-pds.s3.amazonaws.com/")
            assert len(entry["sha256"]) == 64
            assert entry["bytes"] > 0

    def test_no_station_without_published_truth_was_processed(self):
        """KEN6 has observations but publishes no ITRF2020 sheet, so KEN5/KEN6
        is absent rather than judged against a coordinate that does not exist."""
        entries = json.loads((DATA / "source_manifest.json").read_text())
        assert not any("ken6" in entry["file"] for entry in entries)
