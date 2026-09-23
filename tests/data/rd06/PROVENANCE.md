<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# RD-06 — GODN base, GODE judged, GODS the counter-case

Three separate NASA Goddard monuments: GODN (DOMES 40451M127), GODE (40451M123)
65.163 m away, and GODS (40451M128) 76.018 m away. Full 30-second sessions on
1 and 2 January 2025, 2880 epochs each. The first day was selected before
solving; the second is a discrepancy diagnostic. No day or epoch was selected to
obtain a passing result.

**Why two rovers.** A published coordinate describes the antenna that was on the
monument while the data behind it was collected. GODE's antenna was installed on
2013-01-30 and has never been removed, so its coordinate and these observations
describe the same instrument, and it is the baseline the accuracy criterion is
judged on. GODS's antenna changed on 2020-09-03 — **after** the 2020.0 epoch of
its published coordinate — and it is kept, never judged, as the counter-case.
Solving both off one base on one day under one configuration is what turns the
attribution in `specs/22` §5.1 into an experiment rather than an argument, and
`check_rd06.py` refuses to judge a station that fails this rule.

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

| Station | X (m) | Y (m) | Z (m) | Current antenna | Installed |
|---|---:|---:|---:|---|---|
| GODN | 1130760.752 | -4831298.683 | 3994155.197 | `TPSCR.G3 SCIS` | 2012-01-14 |
| GODE | 1130773.531 | -4831253.617 | 3994200.495 | `AOAD/M_T JPLA` | 2013-01-30 |
| GODS | 1130752.184 | -4831349.109 | 3994098.960 | `JAVRINGANT_DM SCIS` | **2020-09-03** |

All three carry identical published velocities, so the five-year propagation to
the observation epoch contributes exactly nothing to either baseline. The
antenna column is read from the vendored site logs and checked against this file
on every commit; the bold date is the one that postdates the coordinate epoch.

Each sheet also publishes the same monument at its **L1 phase centre**. An L1
offset is vertical by construction, so the horizontal part of the difference
between a sheet's own two positions is the publisher's own inconsistency:
**0.21 mm at GODN, 1.27 mm at GODE, 1.99 mm at GODS**. It is a lower bound — an
error common to both of a station's coordinates cancels in the difference — and
it is the only bound available, because the sheets print no uncertainty at all.

All three have velocity (-0.0152, +0.0002, +0.0022) m/year. Apply elapsed Julian
years of 365.25 days from 2020-01-01 to the observation day's midpoint (GPST
calendar labels). Equal velocities make both expected baselines invariant:
**(+12.779, +45.066, +45.298) m** GODN to GODE, and
**(-8.568, -50.426, -56.237) m** GODN to GODS. Only the base's official position
enters the estimator. The rover's is used exclusively for comparison.

The calibrated cases explicitly identify each station's antenna from the site
log: `TPSCR.G3        SCIS` at GODN, `AOAD/M_T        JPLA` at GODE and
`JAVRINGANT_DM   SCIS` at GODS. **The rover's antenna is `ant1` and the base's
is `ant2`**, which is the order `rnx2rtkp` reads the two observation files in;
swapping them applies each calibration at the other end, which is a few
millimetres and looks like an ordinary result. Offsets are zero because truth is
ARP, although the RINEX mark-to-ARP height is 0.0083 m. ANTEX is loaded through
`file-rcvantfile` / `file-satantfile`; passing ANTEX as a positional product
does not load it. `pos1-tidecorr=1` enables solid tides; it is a numeric bitmask,
not `on`. RTKLIB uses the NOAZI calibration, not the full azimuth-dependent
surface. These conventions are frozen, not tuned to minimise the residual.

## What the original experiment established

**These are the counter-case's numbers.** The original experiment ran GODN–GODS
only, before the antenna change was found; the case names below predate the
GODE/GODS naming and are kept so the frozen bytes, `observed-results.json` and
`reference.json` stay in step. They are retained as evidence, not as a target:
the discrepancy they show is the one `specs/22` §5.1 attributes to GODS's
post-epoch antenna change.

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

`specs/20` §6 supplies printed-source precision but **still** no dedicated GNSS
external accuracy threshold, and that is now a decision rather than a gap: one
was derived from the measured repeatability (0.38 / 0.54 / 1.47 mm per
component) and deliberately not adopted, because it lands on the 1 mm the
borrowed rule already gives. The conservative operational interpretation remains
**1 mm per ECEF component**, the sheets' printed precision. This does not adopt
a new acceptance policy. The judged comparison still fails, but the discrepancy
is no longer unattributed — `specs/22` §5 names one contaminated hour and one
station's post-epoch antenna change. A long-term published coordinate model need
not equal one day's GNSS estimate; small formal covariance is not independent
accuracy, and a wrong integer fix does not enlarge it at all. No tolerance is
relaxed, no reference coordinate is fitted, and no covariance is invented.

## Development and CI

[EXAMPLES.md](EXAMPLES.md) indexes the processing cases, the two diagnostics
(the elevation-mask sweep and the sub-session repeatability) and the smaller
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
Processing runs every case twice, preserving commands, config files, engine
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
