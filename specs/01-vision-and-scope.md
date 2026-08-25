# 01 — Vision and scope

**Status:** Draft
**Source:** `projeto_geocomp_abnt.tex` §Introdução e contextualização, §Justificativa, §Objetivos,
§Resultados esperados; `00-dados.tex` (abstract).

---

## 1. The problem

Modern geodetic work routinely combines observation types — total station angles and distances, levelling
height differences, GNSS baselines, gravity differences — and rigorous joint processing of them requires
tools that handle large data volumes, varied stochastic models, and different strategies for tying a network
to a reference frame.

Two consolidated open-source engines already do the heavy computation well:

- **DynAdjust** (Geoscience Australia) for network adjustment — proven at national scale on the GDA2020
  adjustment of more than 330,000 stations and 2.4 million observations.
- **RTKLIB** (`rnx2rtkp`) for GNSS post-processing from RINEX.

Both are command-line programs configured through text files. That is a real barrier: students and
professionals without a CLI background cannot reach them, and even experienced users pay a tax in manual file
preparation, transcription errors, and disconnected result interpretation.

Meanwhile QGIS is an established open-source GIS with a Python plugin environment, a Processing framework
that unifies native and third-party algorithms, direct spatial-database connectivity, and excellent
cartographic visualisation.

**Nothing connects the two worlds.** A typical professional workflow today spans a GNSS package, a separate
adjustment program, auxiliary spreadsheets, and finally a GIS — with manual handoffs at each boundary and no
end-to-end record of what produced what.

A second, related gap: comparing surveys across **epochs**. Structural monitoring — dams, bridges, slopes,
large works — requires comparing coordinate solutions from different occasions, which is only meaningful if
temporal and reference-frame metadata are carried and checked. That checking is usually done by hand, if at
all.

## 2. What GeoComp is

GeoComp is a QGIS plugin and modular framework for **pre-analysis, pre-processing, GNSS processing and
adjustment of geodetic networks**, integrating conventional and GNSS observations in one environment,
encapsulating DynAdjust and `rnx2rtkp` transparently, with cartographic visualisation and optional storage in
a spatial database.

Three things distinguish it from a GUI wrapper around two binaries:

1. **It computes what the engines do not.** Instrument-level pre-processing, geometric reductions, classical
   survey problems, levelling schemes, gravimetric reduction and gravimetric network adjustment are
   GeoComp's own work. See [`06-adjustment-core.md`](./06-adjustment-core.md) and modules `09-`…`13-`.
2. **Every quantity carries its uncertainty.** Covariance propagation is applied systematically from raw
   reading to final displacement, by rigorous means where the information exists and by documented
   approximate means where it does not. See
   [`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md).
3. **Epochs are first-class.** Coordinate solutions carry datum and epoch metadata; comparing two solutions
   checks compatibility and transforms when needed, rather than differencing numbers blindly. See
   [`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md).

## 3. Who it is for

The proposal justifies the project on technical, pedagogical, applied/commercial and open-development
grounds. Those map onto three user profiles, which the **Basic / Advanced** mode split serves directly
(see [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md)).

### P1 — The student

Learning geodesy, adjustment theory or GNSS. Needs to *see* what free and constrained networks, residuals,
error ellipses, and internal and external reliability actually look like, on real data, without first
learning a command-line toolchain. Values: visual feedback, intermediate results being inspectable, defaults
that work, and the ability to break something and see the statistics react.

**Design consequences.** Intermediate quantities are never hidden — every pre-processing step is a separate
algorithm with a visible output. Every statistical test reports the value, the critical value and the
decision, not just a pass/fail. Reference datasets ship with the plugin so a student can reproduce a
textbook example.

### P2 — The researcher

Investigating processing strategies, comparing configurations, or developing method. Needs full parameter
access, reproducibility, batch execution, and the ability to script. Values: nothing decided silently on
their behalf, complete provenance, and the ability to plug in a different engine.

**Design consequences.** Advanced mode exposes every engine parameter, including passing a hand-written
engine configuration file. Every run records inputs, parameters, engine version and timestamps. Algorithms
are Processing algorithms, so they work from PyQGIS and from the graphical modeller. The engine interface is
an abstraction, not a hard-coded call.

### P3 — The practising professional

Delivering surveys, cadastral georeferencing, or monitoring services commercially. Needs a defensible
result, fast, with a report at the end. Values: not paying for a licence, low setup cost, and being able to
show a client where the numbers came from.

**Design consequences.** Basic mode with sound defaults. Installation is *install QGIS, install the plugin*
— engines are acquired by the plugin, not by the user (see
[`adr/0003-engine-acquisition.md`](./adr/0003-engine-acquisition.md)). Results export as report plus map
layers. Monitoring produces displacement maps and time series without custom work.

## 4. In scope

Grouped by the proposal's specific objectives (O1–O12). Requirement IDs are in
[`02-requirements.md`](./02-requirements.md); the mapping is in [`traceability.md`](./traceability.md).

**Platform.** A QGIS plugin providing both a dedicated top-level **GeoComp menu** (six groups, per
`fig/menu_estrutura.png`) and a **Processing Provider**, with every menu action backed by a Processing
algorithm so workflows can be chained, batched and scripted (O1).

**Computation GeoComp performs itself.** Total-station pre-processing and classical survey problems;
geometric levelling in three schemes; gravimetric reduction and gravimetric network adjustment; geometric
reductions; least-squares adjustment with full statistical validation; network pre-analysis; systematic
covariance propagation (O4, and `tex §Aplicação da propagação de covariâncias`).

**Engine integration.** DynAdjust for large-scale and multi-technique adjustment, including automatic input
generation, execution with log capture, and result import (O2). `rnx2rtkp` for GNSS post-processing,
including batch runs and automatic download of ephemeris and clock products (O3).

**Observation types.** Angles, distances, height differences, gravity, GNSS positions and baselines, and the
combinations of them (O4).

**Storage.** File mode (GeoPackage) and database mode (PostGIS and compatible), switchable transparently
(O5).

**Multi-epoch.** Temporal and datum metadata control, compatibility verification, automatic coordinate
transformation, displacement and deformation computation, alert thresholds, time series (O6).

**Trilingual UI.** Complete PT-BR, EN and ES via the QGIS internationalisation infrastructure (O7).

**Openness.** Public GitHub repository, complete documentation, automated tests, CI (O11), with
contribution paths for students (O8), professionals (O12) and the wider community.

**Validation.** Case studies, usability and performance assessment, and systematic comparison against
commercial software using published reference datasets (O9). Teaching material and datasets (O10).

## 5. Out of scope

Stated explicitly so that scope creep is a visible decision rather than a drift.

| Not in scope | Why | If it becomes necessary |
|---|---|---|
| Real-time RTK / NTRIP streaming | The proposal targets post-processing (`rnx2rtkp` is the post-processing tool). Real-time introduces a whole different architecture | New ADR and a phase after v1.0 |
| Writing a new GNSS processing engine | The proposal explicitly selects RTKLIB and explicitly allows *other engines* to be added later, not written | Add an adapter behind the engine interface |
| Reimplementing large-scale network adjustment | DynAdjust exists, is proven at continental scale, and is Apache-2.0. The in-house core is for pre-processing, teaching-scale networks, pre-analysis and cases DynAdjust does not cover (notably gravimetry) | — |
| Instrument drivers / direct field data download | Vendor-specific, hardware-dependent, and orthogonal to the processing goal. GeoComp ingests exported files | Separate companion plugin |
| Field data collection UI | QGIS has QField and Mergin Maps | — |
| Photogrammetry, laser scanning, InSAR | Different techniques with different toolchains | — |
| Geoid model *computation* | GeoComp *imports and applies* geoid models; computing them is a research field of its own | — |
| Cadastral/legal document generation | Jurisdiction-specific, and outside the geodetic processing goal | Downstream plugin consuming GeoComp output |
| A web service or server component | The proposal mentions this only as something to be *studied* for documentation hosting | New ADR |

## 6. Success criteria

The project succeeds if, at v1.0:

1. **It computes correctly.** Every module reproduces its reference dataset within the tolerances in
   [`20-testing-and-validation.md`](./20-testing-and-validation.md), and results agree with published
   official solutions and with commercial software within documented bounds.
2. **It installs in two steps.** Install QGIS, install the plugin from the official repository; the plugin
   handles the engines.
3. **A student can complete a full workflow unaided** — raw field data to adjusted, statistically validated,
   visualised network — using Basic mode and the shipped tutorials.
4. **A researcher can reproduce a run exactly** from the recorded provenance, and can script the same
   workflow from PyQGIS.
5. **A professional can deliver a monitoring report** — displacement vectors with significance testing and a
   time series — without leaving QGIS.
6. **It works in all three languages**, with no untranslated user-facing strings.
7. **It is genuinely open.** Public repository, green CI, documented contribution process, and at least one
   external contribution merged.

## 7. Non-goals of the *specification* itself

These documents specify behaviour, interfaces and acceptance criteria. They deliberately do **not** fix
internal implementation detail — algorithm internals, class hierarchies below the module boundary, or
private helper design — unless a decision there has cross-module consequences, in which case it becomes an
ADR.
