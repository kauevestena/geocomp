# 16 — Processing Provider

**Status:** Draft
**Requirements covered:** FR-005, FR-030…FR-036.
**Source:** O1; tex §Arquitetura do plugin ("Os módulos individuais de processamento (objetivo central)
pertencentes ao plugin serão implementados como os já mencionados Algoritmos *Processing Provider* do QGIS,
permitindo sua integração e encadeamento").

The proposal calls the Processing algorithms the **central objective** of the architecture. This document
fixes the conventions that make them consistent, chainable and stable.

---

## 1. Provider (FR-030)

`GeoCompProvider(QgsProcessingProvider)`, id **`geocomp`**, registered on `initGui()` and unregistered on
`unload()` (FR-006). Provides its icon, its translated name, and a version string matching `metadata.txt`.

## 2. Groups (FR-031)

Mirroring the menu ([`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md)):

| Group id | Displayed |
|---|---|
| `totalstation` | Total Station |
| `levelling` | Level |
| `gnss` | GNSS |
| `gravimetry` | Gravimetry |
| `integration` | Integration |
| `analysis` | Analysis (pre-analysis, inspection, statistics) |
| `monitoring` | Monitoring (multi-epoch, deformation) |
| `project` | Project and data (import, export, storage) |
| `visualization` | Visualisation and reporting |

Group ids are English and stable; displayed names are translated.

**The `project` group is the only one whose menu entry the proposal does not name** — see
[`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) §1.1, where P5 adds it and gives the reasoning.
It held two toolbox-only algorithms from P0; P5's four brought it to six, at which point the exception list
had stopped being a list of exceptions.

## 3. Algorithm identity (FR-032)

`geocomp:<group>_<operation>` — for example `geocomp:totalstation_preprocess`,
`geocomp:gnss_rnx2rtkp_batch`, `geocomp:monitoring_compare_epochs`.

**Ids are permanent.** Models saved in the graphical modeller, scripts and batch definitions store the id;
changing it breaks the user's saved work. A renamed algorithm keeps a deprecated alias for at least one
minor release, and the alias emits a deprecation warning naming the new id.

`displayName()` is translated; `name()` never is.

## 4. Parameter conventions

Consistency here is what makes twenty algorithms feel like one plugin.

| Convention | Rule |
|---|---|
| Parameter names | English, `snake_case`, stable like algorithm ids; descriptions translated |
| Ordering | Required inputs → required options → optional options → advanced → outputs |
| Advanced flag | Parameters hidden in Basic mode are marked advanced (FR-070); see §4.1 |
| Layer inputs | Accept a layer *or* a stored network reference, so algorithms chain from either source |
| CRS | Never inferred silently; an algorithm needing a CRS takes one or reads it from the project, and reports which |
| Epoch | An algorithm needing an epoch takes one; it never defaults (FR-105) |
| Uncertainty | Where an algorithm needs a σ it takes one or resolves it per [`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) §5, and reports the source |
| Engine selection | Where more than one engine can perform an operation, engine choice is a parameter with a sensible default |
| Units | Stated in every parameter description; values are in the project unit, converted once at the boundary |

### 4.1 Basic / Advanced gating (FR-070, FR-071)

Implemented with `QgsProcessingParameterDefinition.FlagAdvanced` plus, where QGIS's advanced section is
insufficient, dynamic parameter construction from the mode setting.

The invariant is FR-071: **a parameter hidden in Basic mode takes exactly the value it would take as the
Advanced default.** Gating changes what is *shown*, never what is *computed*. A test runs every algorithm in
both modes with defaults and asserts identical numeric output.

## 5. Outputs (FR-034)

Formal Processing outputs, so algorithms chain:

| Output | Type |
|---|---|
| Station and observation layers | `QgsProcessingParameterFeatureSink` |
| Result tables (residuals, statistics) | Feature sink (non-spatial) or file output |
| Reports | HTML file output |
| Scalar results (σ̂₀², degrees of freedom, test decisions) | Number/string outputs, so they can drive a model |
| Engine logs | File output (FR-036) |
| Solution reference | String output identifying the stored solution, so downstream algorithms consume it |

Layer outputs arrive styled (FR-905) via the QML assets of
[`19-visualization.md`](./19-visualization.md).

## 6. Validation (FR-035)

`checkParameterValues()` performs every check it can before any computation starts: engine availability
(FR-306), CRS and epoch compatibility, required fields present, referential integrity, and unit consistency.
Failures name the offending parameter and what was expected (NFR-006).

Cheap checks that cannot run in `checkParameterValues()` — those needing the data — run first in
`processAlgorithm()`, before the expensive work.

## 7. Execution

- `processAlgorithm()` orchestrates; it contains no geodetic mathematics. The mathematics is in `core/`
  ([`03-architecture.md`](./03-architecture.md)), which is what allows it to be tested without QGIS.
- Progress via `QgsProcessingFeedback`, determinate where the work is countable (FR-008).
- Cancellation checked at every iteration and between batch items; a cancelled run leaves no partial output
  in the target.
- Every message the user needs goes through `feedback.pushInfo` / `pushWarning`; diagnostics go to the
  GeoComp log tab (FR-009).
- Provenance is assembled during the run and stored with the result (FR-134).

## 8. Documentation

Every algorithm provides `shortHelpString()` — what it does, what each parameter means with its units, what
the outputs contain, and a worked example reference. Translated (FR-090).

Where an algorithm implements a documented method, its help names the method and the reference. A student
reading the help should be able to find the theory.

## 9. Chainability (FR-033)

The proposal's stated reason for the Processing Provider is that algorithms can be *chained*. Concretely, a
full workflow must be assemblable in the graphical modeller with no scripting:

```text
Import observations → Pre-process → Build network → Inspect
   → Adjust → Test → Visualise → Report
```

Each step's outputs must be directly acceptable as the next step's inputs. This constrains output design as
much as input design, and it is tested: [`20-testing-and-validation.md`](./20-testing-and-validation.md)
includes a model-builder workflow test that runs the whole chain headlessly.

**The tail of that chain arrived in P5.** `geocomp:project_export`, `project_report` and `project_store` all
take a *solution document* — the JSON an adjustment algorithm writes — so they chain onto any of them, and
onto DynAdjust's in P6 without changing. The mismatch this design risks is between what one algorithm writes
and what the next reads, which no single-algorithm test can see; `tests/qgis/test_project_algorithms.py`
therefore drives the documents through, rather than constructing each algorithm's input by hand.

Result keys are declared as module-level constants exactly as parameters are (`NAME = "NAME"`), because a
model reads a result by name just as it sets a parameter by name, and
`tests/structural/test_tier3_parameter_names.py` checks both sides against those declarations. A key that
existed only as a string literal in the return statement would be unchecked on both.

## 10. Acceptance criteria

1. The provider registers with id `geocomp`; all algorithms appear in the toolbox under the specified groups.
2. Every algorithm runs from the toolbox, the modeller, batch mode and PyQGIS with identical results (FR-033).
3. The menu-to-algorithm correspondence test passes with no orphans on either side (FR-005).
4. Basic and Advanced modes produce identical numeric results with defaults (FR-071).
5. A model-builder model chaining import → pre-process → adjust → visualise runs headlessly end to end.
6. Every algorithm has a translated `shortHelpString()` documenting every parameter with its units.
7. Every algorithm validates its inputs before computing, and its failure message names the offending
   parameter.
8. Cancelling any algorithm mid-run leaves no partial output.
