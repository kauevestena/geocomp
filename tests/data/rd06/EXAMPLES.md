# GNSS development examples

Use these cases while changing session discovery, configuration, solution parsing
or the baseline bridge. The five RD-06 cases share **one station pair and two
observation days**; they are configuration experiments, not five independent sites.

| Example | Inputs / variation | Expected development outcome |
|---|---|---|
| `default_001` | GODN → GODS, 2025-001, broadcast navigation | Complete fixed solution; exposes the uncalibrated configuration's result |
| `calibrated_001` | Same observations, explicit antenna calibration and solid tides | Primary independent-coordinate comparison; presently fails at 7.512 mm in 3D |
| `calibrated_002` | Second complete day, same monuments and calibration | Repeat the experiment on another day; presently fails the coordinate comparison |
| `reverse_001` | GODS → GODN | Exercise reversed station roles and baseline sign |
| `precise_001` | Day 001 with the IGS20 final orbit and embedded clocks | Exercise precise-product input and comparison with broadcast processing |

Run all five, twice each, through the current working tree:

```sh
python3 -m pip install numpy -r tests/data/rd06/requirements.txt
python3 scripts/check_rd06.py --fetch-inputs --verify-inputs
# Put the pinned rnx2rtkp executable on PATH first.
python3 scripts/check_rd06.py --output build/rd06
```

Exit 1 currently means the primary coordinate comparison failed. Inspect
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
represented by the five configuration cases above and are not claimed validated.
