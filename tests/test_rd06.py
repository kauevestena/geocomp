# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent NGS coordinates: frozen provenance, current code, unresolved accuracy.

Only the accuracy assertion is xfailed locally. Its fixture's data/engine failures
cannot be xfailed. Engine CI uses --runxfail, making this unmet criterion red.

**Two rovers off one base.** GODE is the baseline the criterion is judged on:
its antenna was installed in 2013 and never removed, so the published
coordinate and the observations describe the same instrument. GODS is the
counter-case, kept and never judged: its antenna changed on 2020-09-03, after
the 2020.0 epoch of its published position. Running both under one
configuration on one day is what makes the attribution an experiment rather
than an argument -- see ``specs/22`` section 5.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import os
import shutil
from pathlib import Path

import numpy as np
import pytest

from geocomp.engines.rtklib import read_pos
from scripts.check_rd06 import (
    CASES,
    DATA,
    EXACT,
    RADOME_SUBSTITUTED,
    UNCALIBRATED,
    AccuracyMismatchError,
    UnjudgeableCaseError,
    accuracy_case,
    antenna_history,
    antennas_spanning,
    load_reference,
    measure_solution,
    official_position,
    phase_centre_offsets,
    require_accuracy,
    require_closure,
    require_exact_calibration,
    require_processing,
    require_reference_configuration,
    run_all,
)


@pytest.fixture(scope="module")
def reference():
    return load_reference()


@pytest.mark.parametrize("rover", ["GODE", "GODS"])
def test_sources_and_transcription_match_the_official_bytes(reference, rover):
    # Independent truth is an epoch-propagated ITRF2020 ARP baseline, not the
    # RINEX approximate positions, NAD83, L1 phase centres or RTKLIB output.
    for day in (1, 2):
        vector = np.subtract(
            official_position(reference, rover, day), official_position(reference, "GODN", day)
        )
        np.testing.assert_allclose(
            vector, reference[f"expected_baseline_GODN_to_{rover}_m"], atol=1e-9, rtol=0
        )


class TestTheReferenceDescribesTheseObservations:
    """Offline, on every commit: is the published coordinate even *about* this
    antenna? Nothing in the coordinate sheet says. The site log does."""

    def test_the_judged_station_kept_one_antenna_across_the_epoch(self, reference):
        findings = require_reference_configuration(reference)
        assert findings["GODE"]["predates_coordinate_epoch"]
        assert findings["GODN"]["predates_coordinate_epoch"]
        assert findings["GODE"]["installed"] == "2013-01-30"

    def test_the_counter_case_is_the_one_that_fails_the_rule(self, reference):
        findings = require_reference_configuration(reference)
        assert findings["GODS"]["exempt"]
        assert not findings["GODS"]["predates_coordinate_epoch"]
        assert findings["GODS"]["installed"] == "2020-09-03"

    def test_a_station_whose_antenna_postdates_the_epoch_is_refused(self, reference):
        """The guard is only worth having if removing the exemption fails."""
        import copy

        without = copy.deepcopy(reference)
        without["stations"]["GODS"].pop("antenna_epoch_exempt")
        with pytest.raises(ValueError, match="instrument these observations are not of"):
            require_reference_configuration(without)

    def test_an_exemption_that_no_longer_describes_anything_is_refused(self, reference):
        """An exemption must stay earned, or it becomes a place to hide a
        future station that fails for a real reason."""
        import copy

        stale = copy.deepcopy(reference)
        stale["stations"]["GODE"]["antenna_epoch_exempt"] = "not true of GODE"
        with pytest.raises(ValueError, match="no longer describes anything"):
            require_reference_configuration(stale)

    def test_the_site_log_and_the_reference_agree_on_the_antenna(self, reference):
        for station, entry in reference["stations"].items():
            current = [a for a in antenna_history(reference, station) if a["removed"] is None]
            assert len(current) == 1, station
            assert current[0]["type"] == entry["antenna_type"]
            assert current[0]["installed"] == entry["antenna_installed"]


class TestTheDayTheComparisonIsReadAgainst:
    """The observation day is part of the question, not a detail.

    A published coordinate describes the antenna carried while the data behind
    it was collected. The first station screen fixed the observation day at 2025
    day 001 and concluded that GGAO's 65 m baseline was the shortest clean one
    in the network. That was a property of the day: on a day beside the 2020.0
    epoch the same screen finds seventeen same-antenna pairs within 5 km,
    fifteen of them under 46 m. ``specs/22`` section 5.2 carries the correction;
    these fix the behaviour it rests on, offline, from the vendored logs.
    """

    @staticmethod
    def log(station: str) -> str:
        return (DATA / "sources" / f"{station}.log.txt").read_text(errors="replace")

    def test_the_judged_stations_carry_one_antenna_across_the_span(self):
        assert antennas_spanning(self.log("godn"), "2020-01-01", "2025-01-01") == {"TPSCR.G3        SCIS"}
        assert antennas_spanning(self.log("gode"), "2020-01-01", "2025-01-01") == {"AOAD/M_T        JPLA"}

    def test_nothing_spans_the_counter_case_against_the_day_it_is_processed_on(self):
        """GODS's defect stated as a set size: no antenna it carried at the
        2020.0 epoch was still there in 2025, and the one that is arrived
        after. This is the same refusal ``require_reference_configuration``
        makes, reached from the log text alone."""
        assert antennas_spanning(self.log("gods"), "2020-01-01", "2025-01-01") == set()

    def test_the_counter_case_is_judgeable_against_a_day_beside_the_epoch(self):
        """The correction, as a test. GODS is only unjudgeable *because of the
        day chosen*: its pre-epoch antenna was on the monument until
        2020-09-02, so a day before that reads against the instrument the
        published coordinate is actually of."""
        assert antennas_spanning(self.log("gods"), "2020-01-01", "2020-06-01") == {"TPSCR.G3        SCIS"}

    def test_removal_is_exclusive_of_the_day_observed(self):
        """GODS's antenna came off on 2020-09-02 and its replacement went on
        the 3rd, so the 3rd spans nothing -- the boundary, not an estimate."""
        assert antennas_spanning(self.log("gods"), "2020-01-01", "2020-09-02") == {"TPSCR.G3        SCIS"}
        assert antennas_spanning(self.log("gods"), "2020-01-01", "2020-09-03") == set()

    def test_a_block_with_no_installation_date_is_skipped_not_guessed_at(self):
        """An empty date field used to let the pattern run on and pair this
        antenna with the *next* block's dates, which reports a real antenna
        against times it was not installed for. Skipping errs towards refusing
        a station, which is the safe direction for a screen."""
        log = (
            "4.1  Antenna Type             : TPSCR.G3        SCIS\n"
            "     Date Installed           : \n"
            "     Date Removed             : (CCYY-MM-DDThh:mmZ)\n"
            "\n"
            "4.2  Antenna Type             : AOAD/M_T        NONE\n"
            "     Date Installed           : 2015-01-01T00:00Z\n"
            "     Date Removed             : (CCYY-MM-DDThh:mmZ)\n"
        )
        assert antennas_spanning(log, "2020-01-01", "2025-01-01") == {"AOAD/M_T        NONE"}


class TestTheSheetContradictsItself:
    """An L1 phase-centre offset is vertical by construction: two verticals
    76 m apart diverge by 1.2e-5 radians, so 85 mm of offset projects to under
    a micrometre sideways. Any horizontal difference between a sheet's own ARP
    and L1PC positions is therefore the publisher's inconsistency, measured
    from the publisher's own numbers with nothing assumed."""

    def test_the_offset_is_vertical_for_the_station_that_never_changed(self, reference):
        offsets = phase_centre_offsets(reference)
        assert offsets["GODN"]["horizontal_inconsistency_mm"] < 0.5
        assert 80.0 < offsets["GODN"]["arp_to_l1pc_enu_mm"][2] < 90.0

    def test_the_counter_case_station_is_the_inconsistent_one(self, reference):
        """GODS disagrees with itself by about 2 mm in east -- the same station
        whose antenna changed, and the same order as the residual it shows."""
        offsets = phase_centre_offsets(reference)
        # Measured on the frozen bytes: GODS 1.99 mm, GODN 0.21 mm, a ratio of
        # 9.4. The bound is loose because the claim is the order of magnitude,
        # not the third digit.
        assert offsets["GODS"]["horizontal_inconsistency_mm"] > 1.5
        assert offsets["GODS"]["horizontal_inconsistency_mm"] > (
            5 * offsets["GODN"]["horizontal_inconsistency_mm"]
        )

    def test_it_is_a_lower_bound_and_the_sheets_publish_no_uncertainty(self, reference):
        """Nothing here bounds the reference's uncertainty from above: an error
        common to both of a station's coordinates cancels in this difference."""
        for entry in reference["stations"].values():
            text = (DATA / entry["coordinate_sheet"]).read_text(encoding="utf-8")
            assert "sigma" not in text.lower()
            assert "std dev" not in text.lower()


class TestACaseCarryingAnotherDomesCalibration:
    """``searchpcv`` retries without the radome, so a station whose dome is not
    in the ANTEX is calibrated with a different one and nothing says so."""

    def test_a_substituted_radome_cannot_be_judged(self):
        with pytest.raises(UnjudgeableCaseError, match="antenna \\*and radome\\*"):
            require_exact_calibration(
                {
                    "case": "calibrated_gode_001",
                    "antenna_calibration": RADOME_SUBSTITUTED,
                    "resolved_antennas": {"1": "AOAD/M_T        NONE"},
                }
            )

    def test_an_exact_match_is_judgeable(self):
        require_exact_calibration(
            {
                "case": "calibrated_gods_001",
                "antenna_calibration": EXACT,
                "resolved_antennas": {},
            }
        )

    def test_no_calibration_at_all_is_a_processing_error_instead(self):
        """A different refusal, because it is a different thing: one is a real
        calibration of the wrong dome, the other is no calibration."""
        with pytest.raises(RuntimeError, match="applied no calibration"):
            require_processing(
                {
                    "cases": [
                        {
                            "case": "calibrated_gode_001",
                            "full_day_and_fixed": True,
                            "repeat_pos_bit_identical": True,
                            "antenna_calibration": UNCALIBRATED,
                            "resolved_antennas": {"1": ""},
                        }
                    ]
                }
            )


def test_recorded_solution_remains_a_negative_accuracy_example(reference, tmp_path):
    path = tmp_path / "recorded.pos"
    path.write_bytes(gzip.decompress((DATA / reference["recorded_solution"]["path"]).read_bytes()))
    solution = read_pos(path)
    # The frozen bytes are a GODN-GODS run, which is no longer CASES[1]. The
    # case that produced them is recorded beside them rather than indexed for.
    case = tuple(reference["recorded_solution"]["case"])
    metrics = measure_solution(solution, reference, case)
    recorded = next(
        row
        for row in json.loads((DATA / "observed-results.json").read_text())["cases"]
        if row["case"] == case[0]
    )
    np.testing.assert_allclose(metrics["difference_xyz_m"], recorded["difference_xyz_m"], atol=1e-9, rtol=0)
    assert metrics["full_day_and_fixed"]
    # Formal precision and fixed ambiguities cannot substitute for accuracy.
    assert max(metrics["formal_sigma_xyz_m"]) < reference["tolerance_m"]
    with pytest.raises(AccuracyMismatchError, match="criterion UNMET"):
        require_accuracy(metrics, reference)


@pytest.fixture(scope="module")
def live_results(reference, tmp_path_factory):
    executable = shutil.which("rnx2rtkp")
    missing = []
    if executable is None:
        missing.append("rnx2rtkp on PATH")
    if importlib.util.find_spec("hatanaka") is None:
        missing.append("hatanaka (pip install -r tests/data/rd06/requirements.txt)")
    entries = json.loads((DATA / "source_manifest.json").read_text())
    if any(
        entry["required_for_processing"] and not (DATA / entry["packaged_path"]).is_file()
        for entry in entries
    ):
        missing.append("reference inputs (python3 scripts/check_rd06.py --fetch-inputs --verify-inputs)")
    if missing:
        message = "RD-06 requires " + " and ".join(missing)
        if os.environ.get("GEOCOMP_RD06_REQUIRED") == "1":
            pytest.fail(message)
        pytest.skip(message)
    output = os.environ.get("GEOCOMP_RD06_OUTPUT")
    directory = Path(output) if output else tmp_path_factory.mktemp("rd06")
    # This fixture must finish successfully before the narrowly xfailed
    # assertion runs: malformed input, incomplete epochs and lost repeatability
    # are real errors, not the known published-coordinate discrepancy.
    return run_all(directory, Path(executable), reference)


@pytest.mark.engines
@pytest.mark.parametrize("case", [case[0] for case in CASES])
def test_complete_fixed_runs_are_reproducible(live_results, case):
    metrics = next(row for row in live_results["cases"] if row["case"] == case)
    require_processing({"cases": [metrics]})
    # The production baseline bridge must return rover minus the published
    # base. The engine prints that base at 0.1 mm, bounding this conversion.
    vector = np.subtract(metrics["computed_rover_arp_xyz_m"], metrics["official_base_arp_xyz_m"])
    np.testing.assert_allclose(metrics["computed_baseline_xyz_m"], vector, atol=0.00005, rtol=0)


@pytest.mark.engines
def test_gode_still_carries_another_domes_calibration(live_results, reference):
    """A recorded fact, no longer a failure -- because nothing rests on it now.

    ``ngs20.atx`` has no entry for GODE's ``AOAD/M_T JPLA``; neither has
    ``igs20.atx``, and NGS publishes no JPLA radome at all. ``searchpcv``
    therefore matches ``AOAD/M_T NONE``, the same antenna under a different
    dome. That used to fail the build, because the criterion was GODE's
    absolute agreement with a published coordinate and putting a number on a
    mislabelled run is worse than reporting that the comparison cannot be made.

    The criterion is now loop closure, where a dome substitution at GODE enters
    two legs with opposite signs and cancels, so the substitution no longer
    corrupts anything that is judged. The check stays as an assertion rather
    than a comment so that the day an ANTEX starts carrying JPLA, this says so.
    """
    metrics = accuracy_case(live_results["cases"], reference)
    assert metrics["antenna_calibration"] == RADOME_SUBSTITUTED, (
        f"GODE's calibration state changed to {metrics['antenna_calibration']!r}; "
        "specs/22 section 5.2 and 5.4 need revisiting"
    )
    with pytest.raises(UnjudgeableCaseError):
        require_exact_calibration(metrics)


@pytest.mark.engines
def test_the_counter_case_was_calibrated_exactly(live_results):
    """The attribution in ``specs/22`` §5.1 rests on the GODS numbers, so they
    have to be the calibrated numbers they are reported as."""
    rows = {row["case"]: row for row in live_results["cases"]}
    assert rows["calibrated_gods_001"]["antenna_calibration"] == EXACT
    assert rows["calibrated_gods_002"]["antenna_calibration"] == EXACT


@pytest.mark.engines
def test_the_published_coordinate_comparison_is_reported_not_judged(live_results, reference):
    """The criterion RD-06 used to have, kept as a measurement.

    It is no longer a pass/fail test, at the maintainer's decision of
    24 September 2026. Fourteen independent same-antenna pairs, every one
    exactly calibrated, miss their published coordinates by a median worst
    component of 5.1 mm and none reaches 1 mm, while the same estimator repeats
    to well under a millimetre -- so the comparison was measuring the
    reference's uncertainty rather than this software's. ``specs/22`` §5.4 has
    the measurement, ``specs/20`` §6 the decision.

    What is asserted here is that the discrepancy is still the size §5 says it
    is. If it ever collapses to nothing, or grows by an order of magnitude,
    something changed that the specs do not describe.
    """
    metrics = accuracy_case(live_results["cases"], reference)
    worst = max(abs(component) for component in metrics["difference_xyz_m"]) * 1000
    assert 1.0 < worst < 50.0, (
        f"the published-coordinate discrepancy is {worst:.3f} mm, outside the range "
        "specs/22 section 5 describes"
    )


@pytest.mark.engines
class TestTheTriangleCloses:
    """RD-06's criterion since 24 September 2026.

    A closed circuit of measured vectors must return where it began, so the
    sum is zero but for the errors in the legs. That needs **no published
    coordinate at all**: it asks whether the measurements agree with each
    other rather than with somebody else's position, which is what this
    project controls. ``specs/20`` section 6 states it and says why the
    published comparison stopped being a criterion.
    """

    def test_the_circuit_closes_within_the_criterion(self, live_results, reference):
        require_closure(live_results, reference)

    def test_both_days_were_closed(self, live_results):
        assert sorted(live_results["closure"]) == ["2025-001", "2025-002"]

    def test_the_third_leg_was_measured_and_not_differenced(self, live_results):
        """Differencing two legs to get the third closes identically and checks
        nothing, so a misclosure of exactly zero would mean the test had
        stopped testing. Every leg here is processed independently."""
        for day, entry in live_results["closure"].items():
            assert entry["cases"] == [
                f"calibrated_gode_{day[-3:]}",
                f"calibrated_gods_{day[-3:]}",
                f"calibrated_gode_gods_{day[-3:]}",
            ]
            # Traversal order round GODN->GODE->GODS->GODN, not the order the
            # cases were supplied in: the last leg is GODN-GODS walked backwards.
            assert entry["legs"] == ["GODN-GODE", "GODE-GODS", "GODN-GODS"]
            assert entry["magnitude_mm"] > 0.0, f"{day} closed exactly, which no measurement does"

    def test_the_closure_says_its_uncertainty_is_approximate(self, live_results):
        """Legs from one session share satellites and atmosphere, so summing
        their covariances as independent understates the truth."""
        for entry in live_results["closure"].values():
            assert entry["covariance_is_approximate"]

    def test_a_contaminated_day_still_closes_which_is_the_blind_spot(self, live_results):
        """The limitation, asserted rather than described.

        2025-001 carries the bad ambiguity fix ``specs/22`` section 5.1
        attributes, and it closes anyway -- because an error common to a
        station enters the loop twice with opposite signs. Closure cannot see
        it. That is exactly why the criterion also requires repeatability, and
        the day this assertion fails is the day that argument needs rewriting.
        """
        assert live_results["closure"]["2025-001"]["magnitude_mm"] < 2.0

    def test_the_two_baselines_from_the_shared_station_move_together(self, live_results):
        """The same blind spot seen from the other side: between the two days
        the baselines from GODN shift by millimetres while GODE-GODS barely
        moves, which is the signature of the common station rather than of
        random error -- and is invisible to the closure above."""
        between = live_results["repeatability_between_days"]
        from_godn = [between["GODN-GODE"]["magnitude_mm"], between["GODN-GODS"]["magnitude_mm"]]
        assert min(from_godn) > 2.0 * between["GODE-GODS"]["magnitude_mm"]


@pytest.mark.engines
def test_the_counter_case_carries_the_discrepancy_and_the_judged_one_does_not(live_results):
    """The attribution, as an experiment rather than an argument.

    One base, two rovers, one day, one configuration. Only GODS's antenna
    changed after the epoch of the coordinate it is compared against, and only
    GODS should be several millimetres out in north. If this ever fails, the
    attribution in ``specs/22`` section 5 is wrong and must be rewritten --
    which is why it is a test and not a paragraph.
    """
    rows = {row["case"]: row for row in live_results["cases"]}
    # North, where the counter-case's antenna change shows and a vertical
    # calibration substitution does not.
    gode = rows["calibrated_gode_001"]["difference_enu_m"][1] * 1000
    gods = rows["calibrated_gods_001"]["difference_enu_m"][1] * 1000
    assert gods < -3.0, f"the counter-case no longer shows its north discrepancy: {gods:.3f} mm"
    assert abs(gode) < abs(gods), f"GODE {gode:.3f} mm is not better than GODS {gods:.3f} mm in north"
