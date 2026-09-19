<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# RD-06 — GODN–GODS, independent coordinates and an unmet accuracy criterion

Two separate NASA Goddard monuments, about 76 m apart: GODN (DOMES 40451M127)
and GODS (40451M128). Full 30-second sessions on 1 and 2 January 2025, 2880
epochs each. The first day was selected before solving; the second is a
discrepancy diagnostic. No day or epoch was selected to obtain a passing result.

## Sources and reuse

`sources/` vendors the coordinate sheets, station logs and policy-page snapshots
obtained on 17 September 2026. Large processing files are downloaded explicitly
into this ignored cache with `--fetch-inputs`; their original hashes are pinned.
The original evidence bundle also preserves all downloaded files. `source_manifest.json` records the official URL, acquisition date, sizes
and SHA-256 hashes of every source. NOAA's official distribution is described
at <https://geodesy.noaa.gov/CORS/data.shtml>; the archive is
`https://noaa-cors-pds.s3.amazonaws.com`.

The full NGS IGS20 composite calibration `ngs20.atx` is losslessly gzipped
(mtime 0). The uncompressed calibration hash is verified; local gzip bytes may vary by Python version. No antenna blocks,
satellites or observation epochs were removed. Hatanaka decompression is
lossless; RINEX header warnings from NOAA's upstream GFZRNX conversion remain.
`.gitattributes` prevents newline conversion of the frozen originals.

[NOTICE.md](NOTICE.md) records attribution and reuse terms; upstream terms are
also preserved in `sources/`. NOAA/NGS, NASA Goddard, IGS and antenna calibration
contributors retain their authorship. This is test data, excluded from the
plugin ZIP by `scripts/build.py`. No endorsement is implied.

## Independent expected results

`reference.json` transcribes the first **ITRF2020 ARP, epoch 2020.0** block of
each official NGS coordinate sheet, including velocities. The checker verifies
the transcription against those sheets. It excludes NAD83, L1 phase centres,
monument coordinates and approximate RINEX positions.

| Station | X (m) | Y (m) | Z (m) |
|---|---:|---:|---:|
| GODN | 1130760.752 | -4831298.683 | 3994155.197 |
| GODS | 1130752.184 | -4831349.109 | 3994098.960 |

Both have velocity (-0.0152, +0.0002, +0.0022) m/year. Apply elapsed Julian
years of 365.25 days from 2020-01-01 to the observation day's midpoint (GPST
calendar labels). Equal velocities make the expected baseline invariant:
**(-8.568, -50.426, -56.237) m**, GODN to GODS. Only the base's official position
enters the estimator. The rover's is used exclusively for comparison.

The calibrated cases explicitly identify `TPSCR.G3        SCIS` at GODN and
`JAVRINGANT_DM   SCIS` at GODS. Offsets are zero because truth is ARP, although
the RINEX mark-to-ARP height is 0.0083 m. ANTEX is loaded through
`file-rcvantfile` / `file-satantfile`; passing ANTEX as a positional product
does not load it. `pos1-tidecorr=1` enables solid tides; it is a numeric bitmask,
not `on`. RTKLIB uses the NOAZI calibration, not the full azimuth-dependent
surface. These conventions are frozen, not tuned to minimise the residual.

## What the original experiment established

GeoComp `bb2e2d595dab717d65bbc2c7ab1408d5f6b9ae74`, RTKLIB-EX
`06e8644287ff07efc4c53bbf3e7f9dafb0355605`, NumPy 2.3.5, hatanaka 2.8.1.
`observed-results.json` records the measured results; it is **not ground truth**.
`calibrated_001.pos.gz` losslessly compresses the unmodified primary output, including its original
machine paths in the header; its hash is in `reference.json`.

| Case | ΔX (mm) | ΔY (mm) | ΔZ (mm) | 3D (mm) |
|---|---:|---:|---:|---:|
| Default day 001 | +6.952 | -2.301 | -2.408 | 7.708 |
| **Calibrated day 001 (primary)** | **+6.452** | **-2.401** | **-3.008** | **7.512** |
| Calibrated day 002 | +1.594 | -5.801 | -4.114 | 7.288 |
| Reciprocal day 001 | -6.448 | +2.399 | +2.992 | 7.503 |
| IGS20 final orbit day 001 | +6.352 | -2.401 | -3.108 | 7.468 |

Each run used static GPS L1+L2, forward processing, a 15° mask, broadcast
ionosphere, Saastamoinen troposphere and continuous ambiguity resolution at
threshold 3. The precise case adds the frozen SP3 (including its clocks).
The answer is the **last epoch**, as `baseline_from_solution` specifies.
All days finished fixed and each case reproduced its complete `.pos` bytes
on a same-path repeat. Moving the evidence bundle preserved all solution
records. None of this establishes published-coordinate accuracy.

`specs/20` §6 supplies printed-source precision but no dedicated GNSS external
accuracy threshold. The conservative operational interpretation is **1 mm per
ECEF component**, the sheets' printed precision. This does not adopt a new
acceptance policy. The primary comparison fails; the discrepancy's cause is
unresolved. A long-term published coordinate model need not equal one day's
GNSS estimate; small formal covariance is not independent accuracy. No tolerance
is relaxed, no reference coordinate is fitted, and no covariance is invented.

## Development and CI

[EXAMPLES.md](EXAMPLES.md) indexes the five processing cases and the smaller
GNSS examples for parser, covariance, antenna-height and adjustment development.

The shared checker runs the **current working tree**, not the old commit above.
The original results are retained as history and a negative parser/comparison
example, never as the live test's expected coordinates.

```sh
python3 scripts/check_rd06.py --verify-inputs
python3 -m pip install -r tests/data/rd06/requirements.txt
python3 scripts/check_rd06.py --fetch-inputs --verify-inputs
# rnx2rtkp from the pinned commit must be on PATH:
python3 -m pytest -q tests/test_rd06.py
python3 scripts/check_rd06.py --output build/rd06
```

The first command needs only the standard library. Offline tests check source
integrity, coordinate transcription and the recorded negative example. Live
tests skip with a reason if the engine or Hatanaka decompressor is absent.
Processing runs all five cases twice, preserving commands, config files, engine
logs, solutions and metrics. Full-day coverage, final ambiguity fixing and byte
repeatability must succeed before the accuracy comparison is considered.

Only the live primary accuracy assertion is marked `xfail(strict=True,
raises=AccuracyMismatchError)` for ordinary development. An unexpected pass demands
review/removal of that marker. Input, engine and reproducibility errors cannot
be mistaken for the known discrepancy. The standalone checker returns **1**
for the accuracy mismatch and does not suppress other errors.

The engine workflow installs the decompressor, builds the pinned engine, sets
`GEOCOMP_RD06_REQUIRED=1` (missing prerequisites become errors), and runs
`pytest -q tests/test_rd06.py --runxfail`. **That CI check remains red while the
criterion is unmet.** There is no `continue-on-error`. It uploads the evidence
even on failure; `GEOCOMP_RD06_OUTPUT` selects its retained output directory.
The reference workflow verifies the vendored snapshots without network access.
Engine CI explicitly downloads missing processing inputs and checks their original
hashes before running. Changed upstream bytes cause failure, never substitution.
The manifest also retains optional historical sources (the aggregate coordinate
list and IGS terms PDF); these are not required to process the examples.
