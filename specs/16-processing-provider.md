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
| Parameter names | English, upper snake case (`FOLDER`, `KEEP_WORK_DIR`) as QGIS's own algorithms name theirs, each a module constant `NAME = "NAME"`; stable like algorithm ids; descriptions translated |
| Read | Every declared parameter is read by the run, and every declared output returned |
| Ordering | Required inputs → required options → optional options → advanced → outputs |
| Advanced flag | Parameters hidden in Basic mode are marked advanced (FR-070); see §4.1 |
| Layer inputs | Accept a layer *or* a stored network reference, so algorithms chain from either source |
| CRS | Never inferred silently; an algorithm needing a CRS takes one or reads it from the project, and reports which |
| Epoch | An algorithm needing an epoch takes one; it never defaults (FR-105) |
| Uncertainty | Where an algorithm needs a σ it takes one or resolves it per [`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) §5, and reports the source |
| Engine selection | Where more than one engine can perform an operation, engine choice is a parameter with a sensible default |
| Units | Stated in every parameter description; values are in the project unit, converted once at the boundary |

**As built (P12c-12).** The table said `snake_case` until P12c-12. No parameter was ever named that way:
all 162 are upper snake case, like Processing's own `INPUT` and `OUTPUT`. Renaming them would break every saved
model and script that names one, so the table was corrected to match the code, not the other way round. The
*Read* row was added because P12c-11 found a parameter that had been read by nothing since P7: the GNSS modes'
*Keep the engine's working directory* ([`08`](./08-engine-rtklib.md) §9). `tests/structural/test_parameters_are_read.py`
now holds both rules, and the name rule with them. It reads the sources, so it runs without QGIS. A parameter
counts as read only when the run asks for its value: through `parameterAs...`, as a key of `parameters`, or by
handing it to a helper together with `parameters`. A key that appears only in a log line or a result
dictionary does not count.

### 4.1 Basic / Advanced gating (FR-070, FR-071)

Implemented with `QgsProcessingParameterDefinition.FlagAdvanced` plus, where QGIS's advanced section is
insufficient, dynamic parameter construction from the mode setting.

The invariant is FR-071: **a parameter hidden in Basic mode takes exactly the value it would take as the
Advanced default.** Gating changes what is *shown*, never what is *computed*. A test runs every algorithm in
both modes with defaults and asserts identical numeric output.

**As built (P12a).** No algorithm builds its parameters from the mode: every one flags, and none removes, so
the dynamic construction anticipated above was never needed. A run therefore cannot differ by mode unless the
run itself asks which mode it is in, and none does. That is what `tests/qgis/test_basic_advanced_identity.py`
asserts, for every registered algorithm: the parameter set and every default identical in both modes; no
advanced parameter required with no default, which Basic mode could not supply; and nothing under
`algorithms/` reading the mode. Identical parameters and a mode-blind run are identical output, for every
input rather than for the one per algorithm a run-both-ways test could afford — so the test asserts the
construction instead of sampling its consequence. The defaults themselves are the Global Settings
([`15`](./15-ui-menu-and-settings.md) §2.3).

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

> **As built (P12c-6).** Two rules every algorithm inherits from `GeoCompAlgorithm`
> (`algorithms/inputs.py`). **Before the run**, every file and folder input must exist and every mandatory
> input be given, and a refusal names the input by the label the dialog shows; it is asked in
> `checkParameterValues()`, ahead of QGIS's own check, and again by the wrapper around `processAlgorithm()`,
> because a run from PyQGIS never calls `checkParameterValues()`. QGIS's own refusal ("Incorrect parameter
> value for VELOCITIES") is said against the label too. **During the run**, a refusal whose message carries
> one input's path is prefixed with that input's label, and a core error that reached the wrapper
> unconverted is rendered through its template. P12c-6's audit found that of 38 file inputs given a path that
> did not exist, none was named this way; four produced a traceback, an internal code, or "could not complete
> the operation". `tests/qgis/test_inputs_are_named.py` walks every algorithm and every input.

## 7. Execution

- `processAlgorithm()` orchestrates; it contains no geodetic mathematics. The mathematics is in `core/`
  ([`03-architecture.md`](./03-architecture.md)), which is what allows it to be tested without QGIS.
- Progress via `QgsProcessingFeedback`, determinate where the work is countable (FR-008).
- Cancellation checked at every iteration and between batch items; a cancelled run leaves no partial output
  in the target.

  **As built (P12c).** The second half is held in one place, `geocomp/algorithms/transaction.py`, which
  the base class wraps around every subclass's `processAlgorithm` when the class is defined.
  - **Before the run**, every file a destination parameter names is noted and, if it exists, copied aside.
  - **If the run is cancelled**, those files are put back: restored from the copy, or removed if the run
    made them. Anything the run added to a destination folder is removed. The run then raises, so
    Processing reports it as unfinished, not as a success with no results. That holds whether the
    algorithm noticed the cancel and returned early, ran on to the end, or failed because its engine was
    stopped.
  - **A run that fails is left as it failed.** Several algorithms deliberately write a refusal before
    raising — the document and report saying why — and the user needs those.
  - **Not covered.** A database destination is its provider's; GeoComp's own database writes (the project
    store, the PostGIS switches) roll back in a transaction checked before it commits. A model's children
    are runs of their own. An existing file inside a destination folder is not copied first. All three are
    explained in the module.

  The first half, polling at every iteration, is still per algorithm: 13 of the 46 poll. The rest run on to
  the end and then discard what they wrote.
- Every message the user needs goes through `feedback.pushInfo` / `pushWarning`; diagnostics go to the
  GeoComp log tab (FR-009).
- Provenance is assembled during the run and stored with the result (FR-134).

## 8. Documentation

Every algorithm provides `shortHelpString()` — what it does, what each parameter means with its units, what
the outputs contain, and a worked example reference. Translated (FR-090).

Where an algorithm implements a documented method, its help names the method and the reference. A student
reading the help should be able to find the theory.

**As built (P12c).** Each algorithm writes what it does (`help_body`). The base class appends the rest, so no
help can leave it out:
- every parameter and every output, by the labels the dialog shows;
- the requirement.

A number's label states its unit — `(m)`, `(rad)`, `(hPa)` — or the parameter is named dimensionless, with what
it is instead, in `tests/qgis/test_algorithm_help.py`, which holds all 46 algorithms to both. The audit found
one label without its unit: *Trigonometric levelling*'s imbalance tolerance, a fraction of the longer sight. The
label now says so. **Not built:** a worked-example reference in every help; some name their method and
source, most do not.

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

**As built (P12c).** `tests/qgis/test_model_chain.py` is that test. It builds RD-01's chain as a model: import →
pre-process → adjust, with the solution and the adjustment's layers as the model's outputs. It saves the model
to a `.model3` file, loads it back, and runs it headless. Until then each step's output had been fed to the
next by hand. The same file holds criterion 2. It runs the chain by PyQGIS, as a `QgsProcessingAlgRunnerTask`
on a worker thread (how QGIS's algorithm dialog runs any algorithm not flagged `NoThreading`, and how its
batch dialog runs each row), and through the model, and requires the same solution document from all three.

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
