# GNSS development examples

Use these cases while changing session discovery, configuration, solution parsing
or the baseline bridge. They share **one base, two rovers and two observation
days** at one site; they are configuration experiments, not independent sites.

**GODE is judged and GODS is not.** GODE's antenna was installed in 2013 and
never removed, so its published coordinate and these observations describe the
same instrument. GODS changed antenna on 2020-09-03, after the 2020.0 epoch of
its coordinate, and is kept as the counter-case: running both off one base on
one day is what makes `specs/22` §5.1's attribution an experiment rather than an
argument.

| Example | Inputs / variation | Expected development outcome |
|---|---|---|
| `default_gode_001` | GODN → GODE, 2025-001, broadcast navigation, **no antenna calibration** | Complete fixed solution. It is the calibrated case minus the calibration — same zeroed antenna deltas and solid tides — so the difference between the two rows is the calibration and nothing else |
| `calibrated_gode_001` | Same observations, explicit antenna calibration and solid tides | **The comparison the criterion is judged on**; presently unmet |
| `calibrated_gode_002` | Second complete day, same monuments and calibration | Repeat the experiment on another day |
| `reverse_gode_001` | GODE → GODN | Exercise reversed station roles and baseline sign |
| `precise_gode_001` | Day 001 with the IGS20 final orbit and embedded clocks | Exercise precise-product input and comparison with broadcast processing |
| `calibrated_gods_001` | GODN → GODS, 2025-001 | **Counter-case, never judged.** Must keep showing its north discrepancy |
| `calibrated_gods_002` | GODN → GODS, 2025-002 | The counter-case on the second day |

Run them all, twice each, through the current working tree:

```sh
python3 -m pip install numpy -r tests/data/rd06/requirements.txt
python3 scripts/check_rd06.py --fetch-inputs --verify-inputs
# Put the pinned rnx2rtkp executable on PATH first.
python3 scripts/check_rd06.py --output build/rd06
```

Exit 1 currently means the judged coordinate comparison failed. Inspect
`build/rd06/metrics.json`, then each case's `rnx2rtkp.conf`, `command.json`,
`first.pos`, engine output and `metrics.json`. Do not replace the official
coordinates with these measured outputs. See [PROVENANCE.md](PROVENANCE.md)
for frame, epoch, ARP and calibration conventions.

## The elevation-mask sweep

```sh
python3 scripts/check_rd06.py --sweep --output build/rd06-sweep
# Without the NGS ANTEX (its host may be unreachable):
python3 scripts/check_rd06.py --sweep-uncalibrated --output build/rd06-sweep
```

Solves **both days at 10°, 15°, 20°, 25°, 30° and 35°** and prints each result's
east/north/up error. It exists because those two groups answer different
questions: an error that depends on the mask lives in the low-elevation
observations, and one that does not lives somewhere else. Below 25° the two days
disagree by 11 mm in east; at 25° and above they agree to 0.14 mm in north. That
split is what `specs/22` section 5 attributes the discrepancy with, and it is the
first thing to re-run after any change to weighting, the antenna model or the
baseline bridge.

Engine CI runs the **calibrated** sweep on every engine run and retains
`sweep.json`; the development environment usually cannot, because the NGS ANTEX
host is unreachable from it. At masks of 25° and above both configurations agree
on a residual near 6.9 mm dominated by north, which is the number to compare any
change against.

It sweeps **GODN–GODS**, the counter-case it was written to explain, not the
baseline the criterion is judged on. `--rover GODE` sweeps the other.

## The sub-session repeatability

```sh
python3 scripts/check_rd06.py --repeatability --output build/rd06-repeatability
# Without the NGS ANTEX (its host may be unreachable):
python3 scripts/check_rd06.py --repeatability-uncalibrated --output build/rd06-repeatability
```

Solves both days **whole, in halves, in quarters and hour by hour** — 62
solutions — and reports how far the answer moves. Sub-daily because GPS geometry
repeats every sidereal day: two consecutive days see nearly the same sky, so
their agreement bounds the day-to-day *change* in a geometry-driven error rather
than the error, and splitting the day breaks the repetition.

This is the measurement the tolerance question rests on, and it is how the
contaminated hour of 2025-001 was found. Two things to read in its output:

- **`robust_sigma_enu_mm` against `sigma_enu_mm`.** When they differ by two
  orders of magnitude, a solution in that group is grossly wrong rather than
  noisy, and `outliers` names it.
- **`last_ratio`.** Every gross error in this dataset has a low ambiguity
  validation ratio and an ordinary-looking formal covariance — a 22 mm error
  reports a 1.08 mm 3D sigma. The ratio is the indicator that moves.

Run it after any change to ambiguity resolution, weighting or the baseline
bridge. It reports rather than judges, so a failure is a bug in the diagnostic.

## Smaller examples for fast development

The repository also contains these complementary, independently runnable cases:

| Development problem | Example / test | Run from repository root |
|---|---|---|
| RINEX headers and session overlap | RTKLIB's 2005 Japanese pair, plus transcribed RINEX 3 header | `python3 -m pytest -q tests/test_rinex.py tests/test_gnss_discovery.py` |
| Five solution representations | `tests/data/rtklib/pos/`: LLH, DMS, calendar time, ECEF and ENU | `python3 -m pytest -q tests/test_pos_reader.py` |
| Configuration and real engine execution | The 2005 pair with the production adapter | `python3 -m pytest -q tests/test_rtklib_engine.py` |
| Rotation and covariance | ECEF/ENU outputs of the same real solution | `python3 -m pytest -q tests/test_gnss_baselines.py -k Rotation` |
| Antenna height reduction | Different antenna heights, double reduction, slant-height refusal | `python3 -m pytest -q tests/test_gnss_baselines.py -k AntennaHeight` |
| Baseline dependence | Four-station graph, disconnected pairs, covariance ranking | `python3 -m pytest -q tests/test_gnss_baselines.py -k IndependentSubset` |
| Adjustment interchange | One G measurement, multiple-baseline X cluster, incompatible-frame refusal | `python3 -m pytest -q tests/test_gnss_to_dynadjust.py` |
| Independent coordinate truth | Frozen NGS sheets and the recorded negative accuracy example | `python3 -m pytest -q tests/test_rd06.py -k 'not complete_fixed and not published_coordinate_accuracy'` |

The synthetic height and graph examples test known mathematical behavior. The
Japanese pair tests the pipeline and output format. RD-06 supplies authoritative
coordinate comparisons. Keep those different claims explicit when adding cases.

Further station pairs, longer baselines, other receivers, RINEX 3 observation
bodies and other reference frames would broaden field coverage. They are not
represented by the configuration cases above and are not claimed validated. One
result bears on that directly: every same-antenna-type CORS pair longer than 4 km
errs by 13 to 47 mm under this configuration (`specs/22` §5.2), so a longer
baseline is a different experiment, not a more realistic version of this one.
