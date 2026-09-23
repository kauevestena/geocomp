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
    AccuracyMismatchError,
    accuracy_case,
    antenna_history,
    load_reference,
    measure_solution,
    official_position,
    phase_centre_offsets,
    require_accuracy,
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
        vector = np.subtract(official_position(reference, rover, day),
                             official_position(reference, "GODN", day))
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


def test_recorded_solution_remains_a_negative_accuracy_example(reference, tmp_path):
    path = tmp_path / "recorded.pos"
    path.write_bytes(gzip.decompress((DATA / reference["recorded_solution"]["path"]).read_bytes()))
    solution = read_pos(path)
    # The frozen bytes are a GODN-GODS run, which is no longer CASES[1]. The
    # case that produced them is recorded beside them rather than indexed for.
    case = tuple(reference["recorded_solution"]["case"])
    metrics = measure_solution(solution, reference, case)
    recorded = next(row for row in json.loads(
        (DATA / "observed-results.json").read_text())["cases"] if row["case"] == case[0])
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
    if any(entry["required_for_processing"] and not (DATA / entry["packaged_path"]).is_file()
           for entry in entries):
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
@pytest.mark.xfail(
    strict=True, raises=AccuracyMismatchError,
    reason=(
        "RD-06 accuracy unmet; specs/22 section 5.2. Rebuilt on GODN-GODE, whose antenna "
        "predates its coordinate epoch. Calibrated, the horizontal agrees to +0.68 mm east "
        "and +0.09 mm north -- inside the limit -- and the criterion fails on a constant "
        "-6.47 mm vertical. CI enforces the original assertion with --runxfail."
    ),
)
def test_published_coordinate_accuracy(live_results, reference):
    require_accuracy(accuracy_case(live_results["cases"], reference), reference)


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
    gode = rows["calibrated_gode_001"]["difference_enu_m"][1] * 1000
    gods = rows["calibrated_gods_001"]["difference_enu_m"][1] * 1000
    assert gods < -3.0, f"the counter-case no longer shows its north discrepancy: {gods:.3f} mm"
    assert abs(gode) < abs(gods), (
        f"GODE {gode:.3f} mm is not better than GODS {gods:.3f} mm in north"
    )
