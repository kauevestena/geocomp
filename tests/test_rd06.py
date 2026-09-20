# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent NGS coordinates: frozen provenance, current code, unresolved accuracy.

Only the accuracy assertion is xfailed locally. Its fixture's data/engine failures
cannot be xfailed. Engine CI uses --runxfail, making this unmet criterion red.
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
    load_reference,
    measure_solution,
    official_position,
    require_accuracy,
    require_processing,
    run_all,
)


@pytest.fixture(scope="module")
def reference():
    return load_reference()


def test_sources_and_transcription_match_the_official_bytes(reference):
    # Independent truth is an epoch-propagated ITRF2020 ARP baseline, not the
    # RINEX approximate positions, NAD83, L1 phase centres or RTKLIB output.
    for day in (1, 2):
        vector = np.subtract(official_position(reference, "GODS", day),
                             official_position(reference, "GODN", day))
        np.testing.assert_allclose(vector, reference["expected_baseline_GODN_to_GODS_m"], atol=1e-9, rtol=0)


def test_recorded_solution_remains_a_negative_accuracy_example(reference, tmp_path):
    path = tmp_path / "recorded.pos"
    path.write_bytes(gzip.decompress((DATA / reference["recorded_solution"]["path"]).read_bytes()))
    solution = read_pos(path)
    metrics = measure_solution(solution, reference, CASES[1])
    recorded = json.loads((DATA / "observed-results.json").read_text())["cases"][1]
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
    reason="RD-06 accuracy unmet: 7.512 mm 3D; specs/22 section 5. CI enforces this with --runxfail.",
)
def test_published_coordinate_accuracy(live_results, reference):
    primary = next(row for row in live_results["cases"] if row["case"] == "calibrated_001")
    require_accuracy(primary, reference)
