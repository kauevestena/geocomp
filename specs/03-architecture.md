# 03 — Architecture

**Status:** Draft
**Requirements covered:** FR-001, FR-005, FR-006, FR-008, FR-009, FR-030, FR-036, FR-068, FR-107, FR-303,
FR-306, NFR-002, NFR-003, NFR-004, NFR-005, NFR-006, NFR-012.
**Source:** tex §Arquitetura do plugin e integração com o QGIS; O1.

---

## 1. The shape of the system

GeoComp is four layers with a strict one-way dependency rule.

```text
┌─────────────────────────────────────────────────────────────────────┐
│  PRESENTATION            gui/            algorithms/                │
│  GeoComp menu, dialogs,  Global Settings  QgsProcessingAlgorithm    │
│  toolbar                  window          subclasses                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ depends on
┌────────────────────────────────▼────────────────────────────────────┐
│  APPLICATION             services/                                  │
│  Use-case orchestration: run a workflow, manage a project,          │
│  execute an engine job, assemble a Solution. Knows about tasks       │
│  and cancellation. Knows nothing about widgets.                      │
└──────────────┬──────────────────────────────────┬───────────────────┘
               │                                  │
┌──────────────▼───────────────┐  ┌───────────────▼───────────────────┐
│  DOMAIN        core/         │  │  INFRASTRUCTURE  engines/  io/    │
│  Pure Python. Units, uncer-  │  │  Subprocess adapters, downloads,  │
│  tainty, models, adjustment, │  │  GeoPackage/PostGIS, file formats │
│  techniques, statistics.     │  │  QGIS-facing I/O lives here only. │
│  NO qgis, NO PyQt imports.   │  │                                   │
└──────────────────────────────┘  └───────────────────────────────────┘
```

Arrows point one way. `core/` depends on nothing in this diagram. `engines/` and `io/` may depend on `core/`
for its data types but never the reverse. Presentation never reaches past `services/` into `engines/`.

### Why `core/` is QGIS-free (NFR-002)

This is the single most important structural rule, and it is enforced in CI.

1. **Testability.** The geodetic mathematics — the part where a mistake produces a plausible-looking wrong
   coordinate — can be tested exhaustively in a plain Python process, in milliseconds, against textbook
   worked examples. Requiring a QGIS runtime to test a variance propagation would make that testing rare.
2. **Reviewability by domain experts.** The proposal's collaborators are geodesists, not necessarily QGIS
   developers (`tex §Equipe`). A pure-Python module is reviewable by someone who knows adjustment theory.
3. **Reuse.** The same core can be driven from a Jupyter notebook — which is how the project's own prototype
   already works (`topo_test/processing_prototype.ipynb`) — or by a future non-QGIS front end.
4. **Longevity.** PyQGIS APIs change across major QGIS versions. Adjustment mathematics does not.

**Enforcement:** a CI check greps the `core/` tree for `import qgis`, `from qgis`, `import PyQt`,
`from PyQt`, `import qgis.PyQt` and fails the build on a hit. See
[`20-testing-and-validation.md`](./20-testing-and-validation.md).

---

## 2. Package layout

```text
geocomp/
  metadata.txt              QGIS plugin manifest (name, version, minimum QGIS, licence)
  __init__.py               classFactory(iface) -> GeoCompPlugin
  plugin.py                 GeoCompPlugin: initGui / unload, menu + toolbar construction
  provider.py               GeoCompProvider(QgsProcessingProvider)

  core/                     ── pure Python, no QGIS ──────────────────
    units.py                angles, distances, unit conversion, DMS parsing/formatting
    uncertainty.py          Quantity, Covariance, propagation (see 05-)
    models/                 Project, Campaign, Epoch, Network, Station, Observation, Solution (see 04-)
    adjustment/             parametric LSQ, stochastic model, datum handling (see 06-)
    statistics/             global test, data snooping, reliability, ellipses (see 06-)
    preanalysis/            network design and simulation (see 06-)
    techniques/
      total_station/        PD/PI, corrections, reductions, traverse, resection,
                            intersection, classical networks, trig. levelling, radiation (see 09-)
      levelling/            equal / equidistant / extreme sights, closures (see 10-)
      gnss/                 session model, baseline construction, quality (see 11-)
      gravimetry/           drift, tide, scale, gravimetric network (see 12-)
      integration/          multi-technique combination (see 13-)
    monitoring/             epoch compatibility, displacement, deformation (see 14-)
    reporting/              report assembly from a Solution (data, not rendering)

  engines/                  ── external process adapters ─────────────
    base.py                 Engine interface, EngineRun, EngineResult, discovery, timeouts
    manager.py              acquisition, installation, version detection (see ADR-0003)
    dynadjust/              input writers, pipeline driver, output parsers (see 07-)
    rtklib/                 config writer, runner, .pos parser, product download (see 08-)

  io/                       ── formats and storage ───────────────────
    geopackage.py           canonical project store
    postgis.py              database mirror
    layers.py               Network <-> QGIS layer mapping
    tabular.py              CSV / XLSX with field mapping
    adjust_format.py        Ghilani "Adjust" interoperability
    rinex.py                RINEX header scanning
    models.py               geoid / height model import

  services/                 ── use cases and orchestration ───────────
    project_service.py      open, save, migrate, switch storage mode
    workflow_service.py     run a technique workflow end to end
    engine_service.py       schedule an engine job as a QgsTask
    settings_service.py     layered settings resolution (global / project / run)

  gui/                      ── widgets ───────────────────────────────
    menu.py                 GeoComp menu construction from the algorithm registry
    settings_dialog.py      Global Settings window
    widgets/                shared parameter widgets, field-mapping widget
    panels/                 dockable result and time-series panels

  algorithms/               ── QgsProcessingAlgorithm subclasses ─────
    <group>/<algorithm>.py  one file per algorithm, grouped as in the menu

  resources/                icons, .qml layer styles, report templates
  i18n/                     geocomp_pt_BR.ts|qm, geocomp_es.ts|qm
```

---

## 3. Key architectural decisions

### 3.1 The menu is a thin launcher over Processing algorithms (FR-005)

Every capability exists exactly once, as a `QgsProcessingAlgorithm`. The GeoComp menu launches those
algorithms; it does not contain a second implementation. Some menu items open a richer dialog than the
generic Processing dialog — but that dialog *collects parameters and runs the algorithm*.

This buys: scriptability from PyQGIS, chaining in the graphical modeller, batch mode, and a single place
where a computation can go wrong. The cost is that a few interactions (interactive network design on the
canvas, FR-272) need a custom dialog on top; those are named explicitly in
[`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md). Recorded as
[`adr/0005-menu-algorithm-parity.md`](./adr/0005-menu-algorithm-parity.md).

### 3.2 Two adjustment engines behind one result type (FR-323)

GeoComp has an in-house least-squares implementation *and* drives DynAdjust. Both produce the **same**
`Solution` object. Everything downstream — visualisation, reporting, multi-epoch comparison, storage — is
written once against `Solution` and is engine-agnostic.

The immediate benefit is cross-validation: the same network adjusted both ways must agree within tolerance,
which is a far stronger test than either alone. This is the exit criterion of roadmap phase P6.

Rationale for having an in-house core at all is in
[`adr/0002-in-house-lsq-core.md`](./adr/0002-in-house-lsq-core.md).

### 3.3 Engines are an abstraction, not a call site (FR-303)

The proposal states that the modular architecture must permit other GNSS engines later. Concretely:

```python
class Engine(Protocol):
    name: str
    def detect(self) -> EngineVersion | None: ...
    def prepare(self, job: Job, work_dir: Path) -> PreparedJob: ...
    def run(self, prepared: PreparedJob, *, timeout: float,
            on_progress: ProgressCallback) -> EngineRun: ...
    def parse(self, run: EngineRun) -> Solution: ...
```

`prepare` / `run` / `parse` are separate so that Advanced mode can stop after `prepare`, let the user inspect
or edit the generated input (FR-325), and then continue. Every `EngineRun` records the exact command line,
environment overrides, exit code, stdout, stderr, wall time and engine version (FR-036).

### 3.4 Layered settings (FR-068)

Three scopes resolve in order: **run parameter → project setting → global setting → built-in default.** Every
resolved value can be traced to its origin, and the UI shows which scope a value came from. Without this,
a shared instrument constant silently differs between projects, which is exactly the operational error class
the proposal set out to reduce (`tex §Justificativa técnica`).

Global settings live in `QgsSettings` under a `GeoComp/` prefix; project settings live in the GeoPackage or
PostGIS store so they travel with the data.

### 3.5 Threading (FR-008, NFR-004)

Anything that runs an engine, touches the network, or adjusts more than a trivial network runs as a
`QgsTask`. Rules:

- `core/` functions are synchronous, pure and cancellation-aware through an injected callback — they know
  nothing about `QgsTask`.
- `services/` wraps them in tasks. Only `services/` and above may touch QGIS threading.
- No layer or `QgsProject` mutation off the main thread; tasks return data, the main thread creates layers.
- Every task reports determinate progress where the work is countable (a batch of GNSS sessions, adjustment
  iterations) and indeterminate otherwise.

### 3.6 Errors (NFR-006)

A single exception hierarchy rooted at `GeoCompError`, with subclasses carrying structured context:

| Exception | Raised when | Carries |
|---|---|---|
| `ValidationError` | Input fails a precondition | Which input, what was expected, what was received |
| `DataError` | Data is internally inconsistent | The offending records |
| `ComputationError` | The mathematics fails (singular normal matrix, non-convergence) | Diagnosis: which stations, which observations |
| `EngineError` | An engine failed | Command line, exit code, the engine's own message |
| `EngineMissingError` | A required engine is absent | Which engine, how to obtain it |
| `StorageError` | Persistence failed | Store, operation, underlying cause |

Every one carries a message that states what failed, why, and what to do. Stack traces go to the log
(FR-009), never to the user as the sole message.

### 3.7 Dependencies (NFR-005)

QGIS ships NumPy; GeoComp uses it. Beyond that, every additional runtime dependency needs a recorded
justification, because a QGIS plugin cannot assume the user can run `pip`.

| Dependency | Status | Note |
|---|---|---|
| NumPy | Assumed present | Ships with QGIS |
| SciPy | **Preferred present, not required** | Used for sparse factorisation and distribution quantiles when available; the core MUST provide a NumPy-only fallback path, which is the reference implementation. See [`adr/0008-scipy-and-network-scale.md`](./adr/0008-scipy-and-network-scale.md); as of P2 the distributions use it and the sparse factorisation is not yet written |
| GDAL/OGR, `qgis.core` | Assumed present | Ships with QGIS; used only in `io/` and above |
| `openpyxl` | Optional | Required only for `.xlsx` (FR-160); the feature degrades to CSV with a clear message when absent |
| `requests` | Avoided | Use Python's standard library plus the QGIS network stack, so proxy and authentication settings are honoured |

---

## 4. Extension points

Designed in from the start, because the proposal commits to community contribution (O8, O12) and to future
engines (`tex §Integração com o rnx2rtkp`).

| Extension point | To add | Contract |
|---|---|---|
| New engine | An adapter in `engines/` | Implement `Engine`; register it; produce a `Solution` |
| New observation type | A member of the observation type registry | Value schema, covariance shape, design-matrix contribution, serialisation, import/export mapping |
| New technique operation | A module in `core/techniques/` + an algorithm | Pure function taking and returning `Quantity`-bearing types |
| New import/export format | A module in `io/` | Reader and/or writer over the data model |
| New report template | A file in `resources/` | Consumes the report data structure (FR-931) |

---

## 5. What this architecture deliberately does not do

- **It does not abstract QGIS.** No wrapper layer over `QgsVectorLayer` "in case we leave QGIS". `core/` is
  already QGIS-free; that is sufficient portability, and a second abstraction would cost clarity for no gain.
- **It does not use a plugin/entry-point system for internal modules.** Techniques are imported directly.
  Dynamic discovery would obscure the call graph for the students who are meant to read this code.
- **It does not introduce an ORM.** Storage is GeoPackage and PostGIS through OGR and the QGIS data
  providers, with an explicit mapping layer. See
  [`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md).
