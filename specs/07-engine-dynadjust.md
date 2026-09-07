# 07 — Engine: DynAdjust

**Status:** Draft
**Requirements covered:** FR-163, FR-300…FR-306, FR-320…FR-325, NFR-008.
**Source:** O2; tex §Integração com o DynAdjust; §O Software DynAdjust.

**Upstream references.** [Repository and README](https://github.com/GeoscienceAustralia/DynAdjust) ·
[`resources/INSTALLING.md`](https://github.com/GeoscienceAustralia/DynAdjust/blob/master/resources/INSTALLING.md) ·
`resources/DynAdjust Users Guide.pdf` (also `research_project/bibliography/` in this repository) ·
Fraser, Leahy & Collier, *Automatic segmentation and parallel phased least squares…*
(`research_project/bibliography/dynadjust/adjustment_detailed.pdf`) · Harrison et al. (2024) on GDA2020.

> **Verification note.** Statements below marked **[V]** were verified against upstream sources during
> specification. Statements marked **[C]** must be confirmed against the User's Guide when the module is
> implemented (roadmap P6), and the specification updated if they differ. Implementation MUST NOT assume a
> **[C]** claim is correct.
>
> **Discharged in P6.** Every **[C]** in this document has now been checked against upstream at commit
> `5cdb897`, and each is marked **[V]** with its source. Three sources were used, in this order of
> authority: the **source code**, which is what actually runs; the **User's Guide** (`resources/DynAdjust
> Users Guide.pdf`), which documents the file formats column by column; and the **sample data**
> (`sampleData/`), which shows real files. Where a claim could be checked in more than one, all agreed.
> Nothing below is inferred from a sample file alone — a sample shows what one file happens to contain, not
> what the format permits.

---

## 1. What DynAdjust is, and what it is not

DynAdjust is Geoscience Australia's least-squares adjustment software for geodetic networks, licensed
**Apache-2.0** **[V]**. Its credentials are the GDA2020 adjustment: more than 330,000 stations and 2.4 million
observations, with median positional uncertainties of 20.2 mm horizontal and 100.8 mm vertical
(`tex §O Software DynAdjust`). It is what makes continental-scale adjustment reachable from GeoComp.

**It is a suite of programs, not one executable** **[V]**:

| Program | Role |
|---|---|
| `dnaimport` | Reads station and measurement files, validates, produces the binary working files |
| `dnareftran` | Transforms between reference frames and epochs |
| `dnageoid` | Interpolates a geoid model and applies it to stations |
| `dnasegment` | Divides a large network into blocks connected by junction stations |
| `dnaadjust` | Performs the adjustment (simultaneous, or phased over segmented blocks) |
| `dnaplot` | Produces plot output |

This matters because the archived roadmap modelled the interface as a single `dynadjust` binary
([`archive/README.md`](./archive/README.md), item 8). GeoComp drives a **pipeline** (§3).

### 1.1 What DynAdjust does not do — and why GeoComp has its own core

DynAdjust adjusts networks. It does not:

- **perform instrument-level pre-processing** — no face-left/face-right reduction, no atmospheric or EDM
  correction, no traverse computation, no resection or intersection. All of this is GeoComp's work
  ([`09-module-total-station.md`](./09-module-total-station.md));
- **adjust gravimetric networks** — there is no gravity measurement type **[V]**, so gravimetry runs entirely
  on the in-house core ([`12-module-gravimetry.md`](./12-module-gravimetry.md)). Confirmed twice over: the
  measurement tally in `dnameasurement.hpp` declares exactly twenty types and none is gravimetric, and the
  strings *gravity*, *gravimetr* and *mGal* do not appear anywhere in the source. ADR-0002's conclusion —
  that gravimetry is levelling and runs on the in-house core — is therefore forced rather than chosen;
- **perform network design / pre-analysis** on a network that has no observations
  ([`06-adjustment-core.md`](./06-adjustment-core.md) §5);
- **process GNSS observations** — it consumes baselines, it does not compute them
  ([`08-engine-rtklib.md`](./08-engine-rtklib.md)).

---

## 2. Acquisition and version handling (FR-300…FR-302)

Upstream's **v1.4.0 release carries five binary archives [V]**, listed here as they are actually named,
because an earlier description of this section named builds that do not exist:

| Asset | Platform | Self-contained |
|---|---|---|
| `dynadjust-linux-openblas-static.zip` | Linux x86-64 | yes |
| `dynadjust-linux-mkl.zip` | Linux x86-64 | no — needs the MKL runtime |
| `dynadjust-macos-static.zip` | macOS Apple Silicon | yes |
| `dynadjust-windows-openblas.zip` | Windows x64 | no — ships its own DLLs |
| `dynadjust-windows-mkl.zip` | Windows x64 | no |

Plus a Docker image. **There is no statically linked Windows build**, so ADR-0003 rule 1 is satisfied on
Linux and macOS and cannot be on Windows; `PINNED` records which is which rather than leaving it to be
inferred. This is what makes FR-301 — installation without a command line — achievable. The acquisition
strategy is [`adr/0003-engine-acquisition.md`](./adr/0003-engine-acquisition.md).

**Two things about the archives that only appear when one is installed [V]:**

- **They nest.** Every program sits under a single top-level folder (`dynadjust-linux-static/`), so the
  directory an archive is extracted into is not the directory the programs are in. `manager.install`
  returns the latter, derived from where the expected members actually landed.
- **Windows renames the programs, irregularly.** `dnaadjust` ships as `adjust.exe` and `dnaimport` as
  `import.exe`, but `dnadiff` keeps its prefix as `dnadiff.exe`; the `dna*.dll` files beside them are
  libraries. `engines.dynadjust.engine.WINDOWS_PROGRAM_NAMES` is the table, and it is a table rather than
  a rule because no rule covers all eight.

Requirements specific to this engine:

- GeoComp MUST prefer the **static** Linux and macOS builds when downloading, to avoid a system-library
  dependency chain the user cannot be asked to resolve **[V]**.
- GeoComp MUST record the exact version of each program invoked, and MUST warn when it falls outside the
  tested range (FR-302). The output parsers in §5 are version-sensitive.
- GeoComp MUST verify the checksum of any downloaded archive before extracting it.

---

## 3. The pipeline (FR-321)

```text
GeoComp Network  ──►  write input files (§4)
                          │
                          ▼
                     dnaimport         validate; build binary working files
                          │
                          ▼
                     dnareftran        (when the target frame/epoch differs)
                          │
                          ▼
                     dnageoid          (when orthometric heights are involved — FR-804)
                          │
                          ▼
                     dnasegment        (when the network exceeds the simultaneous threshold)
                          │
                          ▼
                     dnaadjust         simultaneous or phased
                          │
                          ▼
                  parse outputs (§5)  ──►  Solution  ──►  QGIS layers, reports, storage
```

**Stage selection.** Basic mode decides: `dnareftran` runs when the input frame or epoch differs from the
target; `dnageoid` runs when orthometric heights participate; `dnasegment` runs when the station count
exceeds a configurable threshold. Advanced mode exposes each stage individually (FR-325) and allows the user
to stop after input generation, inspect or edit the files, and resume — this is the `prepare` / `run` /
`parse` split in the engine interface ([`03-architecture.md`](./03-architecture.md) §3.3).

**Segmentation.** For very large networks `dnasegment` divides the network into blocks joined by junction
stations, and `dnaadjust` solves them by Tienstra's phased least-squares method with forward and reverse
passes, which is rigorous — the block solutions and their variances equal the simultaneous solution
**[V, per the Fraser/Leahy/Collier paper]**. GeoComp exposes segmentation as a parameter, reports the block
structure, and states in the result that a phased adjustment was used.

**Every stage** is an `EngineRun` recording command line, exit code, stdout, stderr, wall time and version
(FR-036, FR-304). A failure at any stage surfaces DynAdjust's own diagnostic to the user (FR-305), because
its import validation messages are specific and genuinely useful.

**Every stage is recorded whether it ran or not**, with the reason. A provenance record listing only what ran
cannot distinguish a transformation that was unnecessary from one that was forgotten, and those are different
answers to "is this solution in the frame I asked for".

**An unstated input frame or epoch is not a different one** [V]. `dnareftran` runs when the target differs
from the input's — which requires the input to *have* one. A network that states no frame is not in a
different frame; it is in an unrecorded one, and transforming out of that applies a shift computed from an
assumption, which is precisely what FR-105 forbids. So the job's frame is then taken as a statement of what
the data already is, and the stage stays out.

**The exit code is not the whole test** [V]. `dnaimport` returns 0 on a measurement file it could not parse:
it prints `Warning: some files were not parsed` and `there are no measurements to process`, and succeeds.
Trusting the exit code alone carries an empty network into `dnaadjust`; worse, where only *part* of a file
fails to parse, it carries an adjustment of fewer observations than intended whose variance factor looks
entirely healthy. GeoComp knows how many stations and measurement components it wrote, `dnaimport` reports
how many it read, and a difference is a refusal naming both — a count, not a match on warning text, because
the counts are what matters and they do not change wording between releases.

---

## 4. Input generation (FR-320, FR-163)

DynAdjust accepts **DNA, DynaML and SINEX** formats **[V]**.

### 4.1 Format decision

GeoComp writes **DynaML (XML)** as its primary interchange format, and reads DNA `.stn`/`.msr` for
interoperability with existing user data. Rationale in
[`adr/0004-dynadjust-interchange-format.md`](./adr/0004-dynadjust-interchange-format.md); in short: DynaML is
schema-validated, so a generation error is caught by the schema rather than by a misparse; the DNA formats
are column-oriented and unforgiving of a one-character misalignment; and XML generation is far easier to test.

#### The DNA measurement columns [V]

"Unforgiving of a one-character misalignment" turned out to be the operative sentence: the pre-P7 review
found **four defects in `read_dna.py`, all of them column arithmetic**, and all in branches the only
committed `.stn`/`.msr` pair — upstream's all-Cartesian GNSS sample — never reaches. The layout below is
taken from what `dnaimport --export-dna-files` writes and reads back, and
`tests/data/dynadjust/output/terrestrial.{stn,msr}` pins it with a live-engine check in
`scripts/check_dynadjust_fixtures.py`.

| Columns | Field |
|---|---|
| 1 | measurement code |
| 2 | `*` for an ignored measurement |
| 3–22 | first station |
| 23–42 | second station — **on a direction set's header row, the reference direction's target** |
| 43–62 | third station; on a direction set's header, the count of further directions; on each **following** row, that row's own target |
| 63–76 | linear value |
| 77–80 · 81–82 · 83–90 | degrees · minutes · seconds |
| 91–99 | standard deviation — metres for a linear value, **seconds of arc** for an angular one |
| 100–106 | instrument height |
| 107–113 | target height |

Two of the four are worth stating as rules rather than as fixed numbers, because both were *plausible*
readings that produced a network rather than an error:

- **A direction set's target moves between the header row and the rows after it** (23–42, then 43–62).
  Reading 23–42 throughout builds every direction after the first against a station named `''` — an
  observation pointing at nothing, and no complaint anywhere.
- **The three angle columns reassemble into HP notation**, which has exactly one decimal point. Formatting
  the seconds with their own point and concatenating gives `171.2033.58000`, which fails; that is the benign
  half. The malign half is §5.5's: a reader that *accepts* a malformed HP angle gets a wrong angle.

Setup heights follow §4.2's rule for DynaML unchanged: a blank or a zero on a type a vertical offset does
not move is the format's filler; a non-zero one is refused rather than dropped.

### 4.2 Mapping GeoComp observations to DynAdjust measurement types

DynAdjust identifies measurement types by single-letter codes. **There are exactly twenty**, and the list is
now settled from three agreeing sources **[V]**: the tally structure in
`dynadjust/include/measurement_types/dnameasurement.hpp`, which declares
`UINT32 A, B, C, D, E, G, H, I, J, K, L, M, P, Q, R, S, V, X, Y, Z`; the parser's own switch in
`dnaimport/dnainterop.cpp`, which names each; and Table 3.2 of the User's Guide. The letters F, N, O, T, U
and W are **not** measurement types, which is worth stating because a writer that emitted one would produce
a file `dnaimport` rejects with a message about an unknown type rather than about the observation.

| Code | DynAdjust measurement type |
|---|---|
| A | Horizontal angle (uncorrelated) |
| B | Geodetic azimuth (or bearing) |
| C | Ellipsoid chord distance |
| D | Direction set |
| E | Ellipsoid arc distance |
| G | Single GNSS baseline (Δx Δy Δz) |
| H | Orthometric height |
| I | Astronomic latitude |
| J | Astronomic longitude |
| K | Astronomic (Laplace) azimuth |
| L | Orthometric height difference |
| M | Mean sea level (MSL) arc distance |
| P | Geodetic latitude |
| Q | Geodetic longitude |
| R | Ellipsoid height |
| S | Slope (direct) distance |
| V | Zenith distance |
| X | GNSS baseline cluster (full correlations) |
| Y | GNSS point cluster (full correlations) |
| Z | Vertical angle |

The mapping below is the module's contract, and every row is now **[V]**.

| GeoComp observation type ([`04-data-model.md`](./04-data-model.md) §4) | DynAdjust type | Status |
|---|---|---|
| `GNSS_BASELINE` (single) | G | **[V]** |
| `GNSS_BASELINE` (cluster) | X | **[V]** |
| `GNSS_POINT` (cluster) | Y | **[V]** |
| `GEODETIC_LATITUDE` | P | **[V]** |
| `GEODETIC_LONGITUDE` | Q | **[V]** |
| `ELLIPSOIDAL_HEIGHT` | R | **[V]** |
| `ELLIPSOID_DISTANCE` (chord) | C | **[V]** |
| `ELLIPSOID_DISTANCE` (arc) | E | **[V]** |
| `HORIZONTAL_ANGLE` | A | **[V]** |
| `DIRECTION` (set) | D | **[V]** |
| `AZIMUTH` | B | **[V]** |
| `ASTRONOMIC_AZIMUTH` | K | **[V]** |
| `SLOPE_DISTANCE` | S | **[V]** |
| `ZENITH_ANGLE` | V | **[V]** |
| `VERTICAL_ANGLE` | Z | **[V]** |
| `HEIGHT_DIFFERENCE` | L | **[V]** |
| `ORTHOMETRIC_HEIGHT` | H | **[V]** |
| `ASTRONOMIC_LATITUDE` | I | **[V]** |
| `ASTRONOMIC_LONGITUDE` | J | **[V]** |
| `HORIZONTAL_DISTANCE` | **none** | **[V]** — see below |
| `GRAVITY`, `GRAVITY_DIFFERENCE` | **none** | **[V]** — see §1.1 |

**Two distinctions the original table blurred**, both of which would have been silent errors. `AZIMUTH` and
`ASTRONOMIC_AZIMUTH` are separate codes (B and K) — a geodetic azimuth written as K would be adjusted
against a deflection of the vertical it never had. And `ZENITH_ANGLE` and `VERTICAL_ANGLE` are likewise
separate (V and Z), differing by 90°: writing one as the other is a 90° error that produces a plausible
adjustment of the wrong network. GeoComp's own model already distinguishes both pairs, so the mapping is
one-to-one; the risk was only in this table having collapsed each pair into a single row.

**`HORIZONTAL_DISTANCE` has no DynAdjust counterpart**, and this row was missing from the table until a
trilateration network was pushed through the writer and ten of its eleven observations were skipped. It is
not an oversight in DynAdjust: a horizontal distance is a distance *in a plane* — a grid distance, or a
distance reduced to a local horizontal — and DynAdjust's distances are ellipsoidal (`C`, `E`), sea-level
(`M`) or slope (`S`). Converting one to another needs the point scale factor and a height reduction, which is
the **same missing capability** as §4.4's projected coordinates: GeoComp has no geodetic reductions. Writing a
grid distance as an ellipsoid arc would be a scale error of the order of 1 in 10⁴ — 10 cm on a kilometre,
which passes every plausibility check a surveyor would apply and fails the adjustment quietly.

The consequence is that **a plane trilateration or traverse network cannot presently be adjusted by
DynAdjust**, and §4.3 rule 6 says what happens instead of a partial answer.

**`M` (MSL arc distance) has no GeoComp counterpart** and none is invented. A distance reduced to mean sea
level is a distance reduced to a surface GeoComp does not model, and inventing an equivalence to
`ELLIPSOID_DISTANCE` would be a metre-scale error over a long line. A network read from DNA or DynaML that
contains one is reported, not silently reinterpreted (§4.4).

### 4.3 Generation rules

1. **Clusters stay clusters** (FR-104). A GNSS baseline is written with its full 3×3 covariance as a G or X
   measurement, never as three independent scalars. This is the single most important correctness rule of
   the writer.
2. **Units and formats are converted explicitly.** GeoComp holds angles in radians
   ([`04-data-model.md`](./04-data-model.md) §6); the writer converts to DynAdjust's expected representation
   and the round-trip is unit-tested.
3. **Station identifiers are checked against DynAdjust's constraints** (length, permitted characters) and,
   where a user identifier cannot be represented, a mapping is generated, recorded in provenance, and
   reversed on import so the user never sees a renamed station.
4. **Constraint specifications** ([`04-data-model.md`](./04-data-model.md) §2.4) map to DynAdjust's
   per-component station constraints; a mapping GeoComp cannot express exactly is a `ValidationError`, never
   a silent approximation.
5. **Reference frame and epoch are always written explicitly** (FR-105). A DynAdjust run whose frame GeoComp
   inferred rather than knew is refused.
6. Generated files are retained in the run's working directory and referenced from provenance, so a user can
   reproduce the run by hand or attach the files to an upstream bug report (FR-955).

---

## 5. Output parsing (FR-322, FR-323)

`dnaadjust` writes an adjustment output file, a positional-uncertainty file, coordinate files and correction
files. The extensions are **`.adj`, `.xyz`, `.apu` and `.cor`** **[V]**, appended in
`dnaadjustwrapper.cpp`; `.apu` and `.cor` are written only when the corresponding option is given, so their
absence is a configuration fact and not a failure. The User's Guide specifies each format **column by
column** — Appendix C.7 for `.xyz`, C.8 for `.adj`, C.9 for `.cor` and C.10 for `.apu` — and those tables,
not the sample files, are what the parsers are written against: a sample shows what one file happens to
contain, and a fixed-width parser written from one sample breaks on the first file with a longer station
name.

GeoComp parses:

| From | Into `Solution` |
|---|---|
| Adjusted coordinates and their uncertainties | `adjusted_stations` |
| Full variance matrix / positional uncertainty | `parameter_covariance`, per-station covariance blocks |
| Measurement residuals, standardised residuals, n-statistics | `observation_results` |
| Global statistics: σ̂₀², degrees of freedom, chi-square test result | `statistics` |
| Iteration and convergence information | `statistics` |
| Block structure, when phased | `statistics` / provenance |

6. **A network DynAdjust cannot represent whole is refused, not adjusted in part** [V]. Three GeoComp
   observation types have no DynAdjust type (§4.2), and one of them — `HORIZONTAL_DISTANCE` — is the
   *dominant* type in a plane trilateration or traverse: pushed through the writer, RD-03's trilateration
   loses ten of its eleven observations. Adjusting the remainder produces a variance factor and residuals
   that look entirely healthy for a network the user does not have, and nothing in the result says which
   observations were not in it. The pipeline therefore refuses unless `allow_partial` is set, which is a
   statement that a partial network is what was wanted. The writer itself still *reports* rather than
   refuses, because exporting part of a network is a legitimate thing to ask it for; the refusal belongs at
   the layer whose promise is "adjust this network".

### 4.4 The station coordinate type follows the position [V]

DynaML's `<Type>` is a **declaration about the three numbers beside it**, not a
setting. GeoComp writes:

| GeoComp position | `<Type>` | The three values |
|---|---|---|
| Cartesian | `XYZ` | geocentric X, Y, Z in metres |
| Geodetic | `LLH` | latitude and longitude in HP notation, height in metres |
| Projected | **refused** | — |

A projected position was refused rather than converted, because DynaML's third
type, `UTM`, needs a zone and a hemisphere, and converting to geodetic or
geocentric needed an inverse projection GeoComp did not carry.

**It carries one now.** `core/geodesy/` has the ellipsoids, the geodetic↔geocentric
conversion and Transverse Mercator in both directions (§4.5 for how it compares
with DynAdjust's). What is still missing is smaller and different in kind:
deriving the *zone and hemisphere* from a CRS string, which needs a projection
database rather than mathematics. A caller that states the projection
parameters can convert; one that has only an EPSG code still cannot, and the
writer refuses that case by name rather than guessing a zone.

This began as a single constant `XYZ`, with the recorded reasoning that
GeoComp's frames "are cartesian or projected already" — and that sentence was
the defect. A projected easting is not a geocentric X: a UTM 22S station written
as `XYZ` sits **845 km above the Earth's surface**, and DynAdjust accepts it.
A geodetic latitude in radians written into `XAxis` is wrong by the radius of the
Earth. Neither shows up in a network of absolute observations, because DynAdjust
computes its own approximate coordinates and discards the nonsense — which is why
the `gnss-network` cross-validation in §6.1 was unaffected. In a **relative**
network — a traverse, a levelling line, GNSS baselines without absolute points —
the approximate coordinates set the datum, and the answer is wrong in a way that
looks entirely healthy.

### 4.5 DynAdjust's northing carries a meridian-arc truncation [V]

Measured, not inferred. `tests/data/dynadjust/output/grid.xyz` is fifteen stations on **exact whole
arcseconds** — values HP notation holds without rounding — all constrained, so DynAdjust's output is a pure
conversion rather than an adjustment, with eastings printed to 0.01 mm. Against GeoComp's Krüger series:

| latitude | Δ easting | Δ northing |
|---|---|---|
| 0° | 0.000 mm | 0.000 mm |
| 8° | 0.001 mm | 0.004 mm |
| 20° | 0.005 mm | 0.005 mm |
| 36.5° | 0.003 mm | **0.085 mm** |
| 45° | 0.002 mm | **0.253 mm** |

**Easting agrees to the printed precision. Northing does not**, by an amount that grows with latitude and is
independent of longitude — the same at 2.5° west of the central meridian, on it, and 2.75° east. A northing
difference that does not vary with longitude is not in the projection: it is in the **meridian arc**, the
term that carries the northing from the equator to the parallel.

Which implementation is right is settled by an arbiter that uses no series at all. Integrating *M(φ)* by
Gauss–Legendre quadrature puts GeoComp within **a micrometre** of the integral at every latitude from −84°
to 84°, and DynAdjust away from it by exactly the differences tabulated above. The truncation is DynAdjust's.

Two consequences, both practical:

* **A cross-validation must not expect exact agreement in northing.** Sub-millimetre, latitude-dependent, and
  entirely explained — but a tolerance set from the easting will fail on the northing at Australian or
  Brazilian latitudes, and the failure looks like a bug in GeoComp.
* **It is not worth working around.** 0.25 mm at 45° is far below the uncertainty of any observation feeding
  a network, and matching DynAdjust's truncation deliberately would mean shipping a worse conversion to
  agree with a better-known one.

### 5.1 What the files do and do not say about their own layout [V]

No output table has a fixed layout, and none may be parsed as though it had. The columns a run prints depend
on its options -- `--stn-coord-types` chooses the coordinate columns *and their widths*, `--stn-corrections`
adds three, `--output-tstat-adj-msr` and `--output-database-ids` add more, `--output-apu-vcv-units` renames
three -- so the parsers build a column plan per file from the widths in `dnaconsts-iostream.hpp` and the
file's own preamble and column-header line. A header that matches no known plan is refused.

Three things the files state, and one they do not:

| Fact | Where it is stated |
|---|---|
| Coordinate types, station corrections, reference frame, epoch | the preamble, in every file that has a coordinate table |
| Variance-matrix units, whether the full covariance is present | the `.apu` preamble |
| The optional measurement columns (`T-stat`, `Meas. ID`, `Clust. ID`) | the column-header line itself |
| **Whether angles are HP notation or decimal degrees** | **nowhere but the recorded command line** |

The last is the one that matters, because both readings of a number are valid. `-36.331031467` in HP is
`-36.552865187` in decimal degrees, and the same field can hold either. The `.adj` records `Command line
arguments:` and so can be read unaided; **the `.xyz` and `.apu` record no command line at all**. GeoComp
therefore passes the format it used, falls back to the command line when there is one, and otherwise refuses
rather than guessing -- a guess here is a coordinate wrong by up to 0.6 degrees that looks entirely plausible.

HP validation catches part of it by accident: HP cannot hold minutes of 60 or more, so a decimal-degree value
whose fractional part is 0.60 or greater is rejected. That covers much of a real file and is not a guarantee
-- `145.55` reads as either. §5.5 has the two ways the *angular* columns go wrong in particular, one of which
that same validation catches on purpose.

### 5.2 Units inside the measurement table [V]

Confirmed against `PrintAdjMeasurementsAngular` and `PrintAdjMeasurementsLinear` at commit `5cdb897`:

| Column | Angular measurement | Linear measurement |
|---|---|---|
| `Measured`, `Adjusted` | degrees/minutes/seconds, or HP, or decimal degrees, per the format options | metres |
| `Correction`, `Meas. SD`, `Adj. SD`, `Corr. SD`, `Pre Adj Corr` | **seconds of arc**, in every format | metres |
| `N-stat`, `T-stat`, `Pelzer Rel` | dimensionless | dimensionless |

The second row is the trap: the correction and the precisions are wrapped in `Seconds(...)` whatever format
the two value columns took, so reading them the same way as the value is an error of a factor of 3600.

**Angularity is a property of the component, not the type.** `PrintAdjMeasurementsAngular` is called with the
component letters `P`, `L`, `a` and `v`, and `PrintAdjMeasurementsLinear` with `H`, `X`, `Y`, `Z`, `e`, `h`,
`n`, `s` and `u`. A `Y` cluster prints `P`, `L` and `H` under one type letter -- two angles and a height --
so a rule keyed on the type letter reads a height as an angle. Only a row with no component letter falls
back to the type.

The `.cor` file is a further case: its `Azimuth` and `V. Angle` are written by
`FormatDmsString(RadtoDms(...), 4, true, false)`, i.e. separated fields (`84 42 21`), unconditionally -- not
in whatever format the `.adj` used for the same kind of quantity.

### 5.3 Station names are not always recoverable [V]

`std::setw(STATION)` pads to 20 characters but never truncates, and `STN_NAME_WIDTH` allows 30. A name of 20
characters or more therefore runs into the next field **with no separator at all**:

```text
A STATION WITH SPACESCCC   -36.331031467  145.585707313 ...
^-------- name --------^^-^
                        the constraint, with no space before it
```

and names may contain spaces, so splitting on whitespace is no better than slicing. The field is genuinely
ambiguous. It is *not* ambiguous when the caller knows which names it wrote, which GeoComp always does
because it wrote the input files (rule 3 below), so the parsers resolve against a known set when given one
and refuse -- naming the remedy -- when not.

### 5.4 A covariance read from printed text needs conditioning [V]

Measured on DynAdjust 1.4.0. A levelling network determines no horizontal position, so each station's
cartesian covariance has an eigenvalue that is mathematically zero. The `.apu` prints variances to **ten
significant figures** — `6.547721537e+01` — which discards the rest of the double DynAdjust computed, and
the zero eigenvalue lands on whichever side of zero the rounding puts it. For the four-station loop in
`tests/test_dynadjust_pipeline.py` it lands at **−3.03 × 10⁻⁹**, and `Covariance` refuses the matrix:

```text
data.covariance_not_positive_semidefinite (smallest_eigenvalue=-3.0336929576346763e-09, labels=['A.x', 'A.y', 'A.z'])
```

The whole solution was unreadable over an artefact of printing. The matrix is sound to the precision it was
printed at; what is unsound is holding it to a tolerance meant for a matrix that was never printed.

**The tolerance is not loosened.** `Covariance.EIGENVALUE_TOLERANCE` at `1e-12` relative is correct for a
computed matrix — far above double precision's round-off, far below any real defect — and relaxing it
globally would stop it catching genuine data problems everywhere else. Instead
`core.uncertainty.covariance_from_printed` conditions explicitly, and the bound comes from the file:

* `read_output.printed_half_width` reads the precision out of the text — half the place value of the last
  digit each number actually carries — rather than assuming a format, because DynAdjust's output precision
  is settable per column from the command line and a constant here would be right only for the defaults.
* Weyl's inequality bounds an eigenvalue's error by the perturbation's spectral norm, and
  ‖E‖₂ ≤ ‖E‖_F ≤ *n*·max|E_ij|, so **n × half_width** is the furthest rounding alone can push an eigenvalue
  negative. For the block above that is 3 × 5 × 10⁻⁹ = 1.5 × 10⁻⁸, comfortably covering the 3.03 × 10⁻⁹ found.
* Within the bound the negative eigenvalues are clipped to zero — the nearest positive semi-definite matrix
  in the Frobenius norm. The repair moves the whole block by **less than one printed digit**, so the result
  is a matrix the file's own digits are equally consistent with.
* **Beyond the bound nothing is repaired.** The matrix goes to `Covariance` unchanged and is refused naming
  the eigenvalue actually found, which is what keeps the conditioning from quietly rescuing a matrix that is
  indefinite for a real reason.

It is recorded, not silent. The conditioned covariance is `APPROXIMATE` and carries
`Strategy.ROUNDING_CONDITIONED` ([`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md)
§2.3), and the `Solution` built from it is `APPROXIMATE` too — so a report cannot present a repaired matrix
as a rigorously propagated one (FR-203). A covariance that needed no repair is returned untouched and
unlabelled: reporting a conditioning that did not happen is its own dishonesty.

### 5.5 What the angular columns do wrong [V]

Two defects, both in DynAdjust 1.4.0, both reached by asking for `Latitude` and `Longitude` columns. They
were found while checking a note in this repository that claimed something else — that the `.xyz` parser
could not read a column set containing `E`, `N` and `z`. **That note was wrong**: `grid.xyz` is
`--stn-coord-types ENz` and has always read. The real limits are these.

**1. `--precision-stn-angular 7` overflows the column.** An HP latitude is `sign + DD + . + MM + SS +
precision`, so at precision 7 it is 15 characters and `LAT_EAST` is 14. `std::setw` pads but never truncates,
so Zone, Latitude and Longitude run together with no separator at all:

```text
  55  -45.00000000   144.30000000     precision 4 — separated
  55 -45.000000000  144.300000000     precision 5 — DynAdjust's default
  55-44.6000000000 144.3000000000     precision 6 — abuts, still sliceable
  55-44.60000000000144.30000000000    precision 7 — overflowed, nothing after it is its own field
```

Note precision 6: the fields **touch without anything being lost**, because two right-aligned columns abut
whenever the left one's value fills its width exactly. A missing separator is therefore not by itself an
overflow, and refusing that row would be a false alarm. So `ColumnPlan.unseparated` is a *diagnosis* — it is
consulted to explain a conversion that already failed and never to refuse a row on its own. Without it the
first complaint is `not a number` in `SD(n)`, several columns to the right of the fault and naming a field
that is perfectly well formed.

**GeoComp must never request a precision that overflows**, and this one is entirely its own to get right: it
composes the command line. It asks for no angular precision at all and takes DynAdjust's default of 5; 6 is
the last value that fits, and a test asserts it.

**2. DynAdjust's HP printer can emit 60 minutes.** This one needs no unusual flags. In `grid-hp-carry.xyz`,
written at the *default* precision, three stations sit at latitude −45° — confirmed to eight nanoseconds of
arc by inverse-projecting the eastings and northings printed in the same rows — and DynAdjust prints two of
them as `-45.000000000` and the third as **`-44.600000000`**: 44 degrees, **60** minutes. The seconds round up
to 60 and the carry into minutes, and from minutes into degrees, is not made.

HP notation cannot hold it, and GeoComp refuses it rather than reading 60 minutes as an hour
(`validation.hp_angle_minutes_out_of_range`) — the reader now names the station so the row can be found. The
trigger is a value within half of the last printed digit of a whole minute, so in real data it is rare; in a
network laid out on whole degrees it is not. **Reading it leniently is the wrong repair**: the same
validation is what stops a decimal-degree value being read as HP (§5.1), and a reader that accepts 60
minutes from one source accepts it from all of them.

### 5.6 A direction set is not a row per direction [V]

The two engines parameterise a set of directions differently, and the difference is invisible until one is
written and read back.

**GeoComp** holds *N* directions plus the setup's orientation unknown (FR-104): every direction is an
observation, and the unknown absorbs the arbitrary circle zero. **DynAdjust's `D`** holds a *reference*
direction plus the *N−1* measured from it — the reference has no value of its own, so it is never a printed
row. The two carry the same information; they do not map row for row.

```text
D 1                   3                                          1
                                          2             199 06 36.5000  199 06 41.0993 ...
^ instrument          ^ reference                        ^ the one direction that has a value
                                          ^ target       ^ and the C column holds the set *count*
```

Three consequences, each of which was a defect until RD-01 became the first network with directions to reach
the engine:

* **`printed_rows` emits *N−1* rows for a set of *N*.** Emitting one per direction reported a lost
  measurement on every network with a direction set — `check_import` compares its count against
  `dnaimport`'s, and `dnaimport` counts printed rows too.
* **The parser must carry the set across rows.** The header has no value to read and the member rows have no
  type letter, so reading rows independently drops the whole set silently.
* **The `C` column of a header is a count, not a component.** Handing that digit to the angular/linear test
  raised `dynadjust_unknown_measurement_component` — and *that raise was itself broken*: its context key
  `code` collided with `GeoCompError`'s first positional argument, so a guard written to prevent a
  factor-of-3600 misread failed with a `TypeError` instead of its own message.

**A direction set of one has no equivalent at all.** `dnaimport` refuses the file: *"Direction set declares
total of 0 but there aren't any non-ignored directions in the set."* Nothing is lost by leaving it out — one
direction with its own orientation unknown is one observation and one parameter, contributing exactly zero —
but it is **reported as skipped** rather than dropped, so the pipeline refuses unless `allow_partial` says a
partial network is what was wanted (§5 rule 6). `tests/test_dynadjust_pipeline.py` asserts the "contributes
zero" claim rather than resting on it.

### 5.7 A constraint on a projected station is written on the LLH axes [V]

A projected position is inverse-projected and written `LLH` (§4.4), so `XAxis` is a **latitude**. A
constraint stated on the grid must be reordered before it is written: easting is a *longitude*.

| held in GeoComp | written | not |
|---|---|---|
| easting | `FCF` | ~~`CFF`~~ |
| northing | `CFF` | ~~`FCF`~~ |

Latent until a **partially** constrained projected station was written — a fully fixed or fully free one is
`CCC` or `FFF` either way, which is why every earlier test passed. The failure it would have caused is the
quiet kind: the network is constrained along the perpendicular axis, and it still converges.

Parsing rules:

1. **Parse defensively and version-explicitly.** Output layout can change between versions. Each parser
   declares the versions it was validated against and refuses, with a clear message, a version it does not
   recognise — rather than silently misreading a column (FR-302).
2. **Never infer a missing quantity.** If DynAdjust did not report something GeoComp wants, the field is
   `None` and downstream code handles absence. A fabricated statistic is worse than a missing one.
3. **Round-trip identifiers** through the mapping of §4.3 rule 3.
4. **The parsed result is a `Solution`, identical in type to the in-house core's output** (FR-323). Every
   downstream consumer — visualisation, reporting, multi-epoch analysis, storage — is engine-agnostic.

---

## 6. Cross-validation with the in-house core

The exit criterion for roadmap phase P6: a network adjusted by both engines MUST agree within the tolerances
in [`20-testing-and-validation.md`](./20-testing-and-validation.md) — coordinates, residuals, σ̂₀², degrees of
freedom, and error ellipse parameters.

This is deliberately a hard test. Two independent implementations agreeing is strong evidence of
correctness; disagreement localises a real defect in one of them. Any discrepancy above tolerance is
investigated and documented before release, and where it stems from a genuine methodological difference
(a different refraction model, a different datum convention) that difference is documented rather than
tuned away.

### 6.1 The result [V]

Measured on upstream's `gnss-network` slice (11 stations, one four-baseline `X` cluster, one six-point `Y`
cluster and two standalone `G` baselines), the in-house core against DynAdjust 1.4.0:

| Quantity | In-house | DynAdjust | Agreement |
|---|---|---|---|
| Degrees of freedom | 3 | 3 | exact |
| Observations / parameters | 36 / 33 | 36 / 33 | exact |
| Variance factor σ̂₀² | 0.13769 | 0.138 | to the three decimals DynAdjust prints |
| Adjusted coordinates | — | — | **0.047 mm**, largest over 33 components |
| Residuals | — | — | 0.050 mm, largest over 36 rows |

The core is started from coordinates perturbed by up to **five metres**, so the agreement is a property of
the two solutions and not of a shared starting point.

**Why this network.** Its observations are GNSS baselines and points, both *linear* in the coordinates, so
the two engines solve the identical problem and any difference is arithmetic rather than modelling. It also
lets the core hold the network in geocentric metres directly — `Frame.SPACE_3D` is three orthogonal metres
whatever they are called — so no frame conversion stands between the two answers to be blamed for a
difference. Networks whose observation equations are non-linear (distances, angles, zenith angles) exercise
the Jacobians as well, and are the natural next case; they need the core's local frame and DynAdjust's
geodetic one to be related, which is a conversion GeoComp does not yet have.

### 6.2 What is compared, and what is refused [V]

`geocomp.engines.dynadjust.crossvalidation` compares degrees of freedom, observation and parameter counts
exactly; the variance factor relatively; coordinates and residuals within a stated tolerance. Counts first,
because they are properties of the model rather than of the arithmetic: if they differ the two engines were
given different networks, and comparing residuals after that is meaningless.

**Coordinates are compared only when both solutions are in the same frame**, and that is checked rather than
assumed. Differencing a geocentric X against a projected easting produces a number and the number means
nothing, so a frame mismatch is reported as *not compared*, naming both frames. A quantity that could not be
compared does **not** count as a disagreement: absence of evidence is not evidence, and treating it as such
would make an unconvertible frame look like a defect in an engine.

---

## 7. Failure handling

| Situation | Behaviour |
|---|---|
| Engine not installed | Operation disabled in the UI with an explanation and an offer to install (FR-306, FR-301) |
| Version outside tested range | Warn, proceed, and record the version prominently in the result (FR-302) |
| `dnaimport` rejects the input | Surface DynAdjust's message, and map it back to the GeoComp records that produced the offending lines |
| Adjustment does not converge | Report as a failure with DynAdjust's diagnostics; never present the last iterate as a result |
| Timeout | Terminate the process group, retain the working directory, report elapsed time and the configured limit (FR-304) |
| Non-zero exit with no message | Report exit code, full command line and working directory, and point the user to the retained input files |

---

## 8. Acceptance criteria

1. DynaML written by GeoComp validates against the DynaML schema and is accepted by `dnaimport` without
   warnings, for every observation type in the §4.2 mapping.
2. A GNSS baseline cluster round-trips through DynaML with its covariance intact to full double precision.
3. The full pipeline runs end to end from a GeoComp `Network` and returns a populated `Solution`.
4. Parsed results match, field for field, what is printed in the DynAdjust output files.
5. Cross-validation against the in-house core passes (§6).
6. Every claim in this document marked **[C]** has been confirmed against the User's Guide, and the marking
   updated to **[V]** or the statement corrected.
7. With DynAdjust absent, the plugin loads, all non-DynAdjust functionality works, and DynAdjust-dependent
   operations are disabled with an explanation (FR-306).
