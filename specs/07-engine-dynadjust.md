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
- **adjust gravimetric networks** — there is no gravity measurement type **[C]**, so gravimetry runs entirely
  on the in-house core ([`12-module-gravimetry.md`](./12-module-gravimetry.md));
- **perform network design / pre-analysis** on a network that has no observations
  ([`06-adjustment-core.md`](./06-adjustment-core.md) §5);
- **process GNSS observations** — it consumes baselines, it does not compute them
  ([`08-engine-rtklib.md`](./08-engine-rtklib.md)).

---

## 2. Acquisition and version handling (FR-300…FR-302)

Upstream distributes **pre-built binaries for Windows x64 (OpenBLAS and Intel MKL builds), macOS 14 Apple
Silicon (dynamic and static), Ubuntu 22.04+ (OpenBLAS dynamic) and generic x86-64 Linux (static)**, plus a
Docker image **[V]**. This is what makes FR-301 — installation without a command line — achievable. The
acquisition strategy is [`adr/0003-engine-acquisition.md`](./adr/0003-engine-acquisition.md).

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

---

## 4. Input generation (FR-320, FR-163)

DynAdjust accepts **DNA, DynaML and SINEX** formats **[V]**.

### 4.1 Format decision

GeoComp writes **DynaML (XML)** as its primary interchange format, and reads DNA `.stn`/`.msr` for
interoperability with existing user data. Rationale in
[`adr/0004-dynadjust-interchange-format.md`](./adr/0004-dynadjust-interchange-format.md); in short: DynaML is
schema-validated, so a generation error is caught by the schema rather than by a misparse; the DNA formats
are column-oriented and unforgiving of a one-character misalignment; and XML generation is far easier to test.

### 4.2 Mapping GeoComp observations to DynAdjust measurement types

DynAdjust identifies measurement types by single-letter codes. Confirmed upstream: **G** (GNSS baseline),
**X** (GNSS baseline cluster), **Y** (GNSS point cluster), **P** (geodetic latitude), **Q** (geodetic
longitude), **R** (ellipsoid height), **C** (ellipsoid chord distance), **E** (ellipsoid arc distance)
**[V]**; the suite also supports horizontal angles, geodetic azimuths, direction sets, slope distances,
zenith distances and levelling height differences **[V]**, whose codes are **[C]**.

The mapping table below is the module's contract. **Implementation MUST validate every row against the
User's Guide before the first release, and the DynaML schema is the authority.**

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
| `HORIZONTAL_ANGLE` | angle type | **[C]** |
| `DIRECTION` (set) | direction-set type | **[C]** |
| `AZIMUTH` / `ASTRONOMIC_AZIMUTH` | azimuth types | **[C]** |
| `SLOPE_DISTANCE` | slope distance type | **[C]** |
| `ZENITH_ANGLE` / `VERTICAL_ANGLE` | zenith / vertical angle types | **[C]** |
| `HEIGHT_DIFFERENCE` | levelling type | **[C]** |
| `ORTHOMETRIC_HEIGHT` | orthometric height type | **[C]** |
| `ASTRONOMIC_LATITUDE` / `ASTRONOMIC_LONGITUDE` | astronomic types | **[C]** |
| `GRAVITY`, `GRAVITY_DIFFERENCE` | **none** | **[C]** — see §1.1 |

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
files; the exact extensions in use (`.adj`, `.apu`, `.xyz`, `.cor`, and the phased-adjustment variants) are
**[C]** and MUST be confirmed against the User's Guide **[C]**. GeoComp parses:

| From | Into `Solution` |
|---|---|
| Adjusted coordinates and their uncertainties | `adjusted_stations` |
| Full variance matrix / positional uncertainty | `parameter_covariance`, per-station covariance blocks |
| Measurement residuals, standardised residuals, n-statistics | `observation_results` |
| Global statistics: σ̂₀², degrees of freedom, chi-square test result | `statistics` |
| Iteration and convergence information | `statistics` |
| Block structure, when phased | `statistics` / provenance |

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
