> **SUPERSEDED — ARCHIVED FOR REFERENCE ONLY. DO NOT IMPLEMENT FROM THIS FILE.**
>
> This document (originally `plugin_roadmap.md` at the repository root) was written by an earlier agent
> before the specification set existed. It is retained because parts of it were carried forward, but its
> central premise is incorrect and several major project requirements are missing from it.
>
> See [`README.md`](./README.md) in this folder for the full assessment, and use
> [`../ROADMAP.md`](../ROADMAP.md) as the authoritative plan.

---

# GeoComp QGIS Plugin – Implementation Roadmap (v2)

**Audience:** developers and code agents implementing the GeoComp plugin for QGIS.  
**Purpose:** provide a step-by-step, implementation-oriented plan with clear modules, functions,
and acceptance criteria.

---

## 0. Glossary (for agents)

- **Network** – logical collection of stations and observations to be adjusted.
- **Station** – geodetic point (GNSS marker, benchmark, etc.) with an ID and coordinates.
- **Observation** – single measurement between one or more stations (angle, distance, height difference,
  GNSS baseline, gravimetry, etc.).
- **GNSS session** – one continuous GNSS observation period (RINEX obs + nav + products).
- **Baseline** – vector between two stations derived from GNSS positions or double-differences.
- **Engine** – external CLI program used for computation (DynAdjust, RNX2RTKP).

The roadmap assumes all heavy geodetic math is delegated to **DynAdjust** and **RNX2RTKP**.

---

## 1. High-level plugin goals

1. Implement a QGIS plugin that registers a **Processing Provider** named `GeoComp`.
2. Provide algorithms to:
   - import and manage geodetic networks;
   - process GNSS data (RINEX → positions → baselines);
   - run least-squares adjustment via DynAdjust;
   - visualize results (error ellipses, residual vectors, diagnostics);
   - optionally store / load data from PostGIS.
3. Wrap external engines:
   - `dynadjust` (DynAdjust CLI) for network adjustment;
   - `rnx2rtkp` (RTKLIB-EX) for GNSS post-processing.
4. Implement two usage profiles:
   - **Basic**: minimal parameters, sensible defaults.
   - **Advanced**: full access to engine options via config files.
5. Provide a tri-lingual UI (PT-BR, EN, ES) via QGIS translation system.

---

## 2. Repository layout (target structure)

Recommended structure for the plugin source tree:

```text
geocomp-qgis-plugin/
  README.md
  roadmap.md
  geocomp/
    __init__.py
    metadata.txt
    plugin.py            # QGIS plugin entry point
    provider.py          # QgsProcessingProvider implementation

    i18n/
      geocomp_pt_BR.ts
      geocomp_en_US.ts
      geocomp_es_ES.ts

    core/
      models.py          # Network, Station, Observation, GnssSession, etc.
      config.py          # Project/global configuration objects
      io_network.py      # Import/export network to layers / files / DB
      io_gnss.py         # GNSS sessions & products metadata
      postgis.py         # Optional PostGIS helpers
      visualization.py   # Helper functions to style layers

    cli/
      dynadjust_runner.py    # Input builder + runner + parser for DynAdjust
      rnx2rtkp_runner.py     # Input builder + runner + parser for RNX2RTKP
      products_download.py   # Ephemeris/clock download and caching

    algorithms/
      __init__.py
      alg_project_init.py
      alg_import_observations.py
      alg_gnss_scan_sessions.py
      alg_gnss_download_products.py
      alg_gnss_rnx2rtkp_batch.py
      alg_gnss_build_baselines.py
      alg_network_preanalysis.py
      alg_network_adjust_dynadjust.py
      alg_visualize_results.py

    tests/
      test_models.py
      test_dynadjust_runner.py
      test_rnx2rtkp_runner.py
      test_algorithms.py
```

Agents should **create these files even if initially empty**, then iterate by phases.

---

## 3. Phase 1 – QGIS plugin + Processing Provider skeleton

### Target files

- `geocomp/__init__.py`
- `geocomp/plugin.py`
- `geocomp/metadata.txt`
- `geocomp/provider.py`
- `geocomp/algorithms/__init__.py`
- One dummy algorithm file (e.g. `alg_project_init.py`)

### Tasks (for agents)

- [ ] Implement `metadata.txt` with basic plugin information (name “GeoComp”, version, author, min QGIS version).
- [ ] In `__init__.py`, expose the plugin factory function required by QGIS.
- [ ] In `plugin.py`, implement a class `GeoCompPlugin` with:
  - [ ] `initGui()` → registers the `GeoCompProvider` with the processing registry.
  - [ ] `unload()` → unregisters the provider.
- [ ] In `provider.py`, implement `class GeoCompProvider(QgsProcessingProvider)` with:
  - [ ] `id()` → returns a stable ID, e.g. `"geocomp"`.
  - [ ] `name()` → returns translatable provider name.
  - [ ] `loadAlgorithms()` → registers a dummy algorithm
        (e.g. creating an empty text file and returning it as output).
- [ ] In `algorithms/alg_project_init.py`, implement a minimal
      `QgsProcessingAlgorithm` subclass with:
  - [ ] Unique algorithm ID, e.g. `"geocomp:project_init"`.
  - [ ] No-op behavior (or simple creation of a GeoPackage with empty layers).

### Done when

- Plugin can be installed in QGIS and enabled.
- “GeoComp” appears as a provider in the Processing Toolbox with at least one working algorithm.

---

## 4. Phase 2 – Core domain model

### Target files

- `geocomp/core/models.py`
- `geocomp/core/config.py`

### Required dataclasses / enums

In `models.py` define (Python `dataclasses` recommended):

- `ObservationType` (Enum or similar): `"ANGLE"`, `"DISTANCE"`, `"HEIGHT_DIFF"`, `"GNSS_BASELINE"`, `"GRAVIMETRY"`, etc.
- `Station`:
  - `id: str`
  - `name: str`
  - `approx_x, approx_y, approx_z: float` (or lat/lon/h)
  - `is_fixed: bool`
  - `meta: dict` (optional)
- `Observation`:
  - `id: str`
  - `type: ObservationType`
  - `from_station: str`
  - `to_station: str | None`
  - `values: dict` (e.g. `{angle: float, distance: float}`)
  - `sigma: float | dict`
  - `meta: dict`
- `GnssSession`:
  - `id: str`
  - `station_id: str`
  - `rinex_obs_path: str`
  - `rinex_nav_paths: list[str]`
  - `start_time, end_time` (datetime or strings)
  - `meta: dict`
- `Network`:
  - `stations: dict[str, Station]`
  - `observations: dict[str, Observation]`
  - `gnss_sessions: dict[str, GnssSession]`
  - `meta: dict`

In `config.py` define configuration objects, for example:

- `GeoCompConfig` – plugin/global settings (paths to engines, default working directory, DB connection name, etc.).
- `DynAdjustConfig` – options to control DynAdjust runs (stochastic model, constraints, output verbosity).
- `Rnx2rtkpConfig` – options to control RNX2RTKP runs (solution mode, frequency, elevation mask, etc.).

### Tasks (for agents)

- [ ] Implement the dataclasses and enums with type hints.
- [ ] Ensure model layer is **pure Python** (no QGIS imports).
- [ ] Add `to_dict()` / `from_dict()` helpers where useful (for JSON/YAML config files).

### Done when

- Tests in `tests/test_models.py` can create a `Network` with stations/observations/sessions in memory.
- These objects serialize/deserialize without loss of information.

---

## 5. Phase 3 – QGIS I/O and network construction

### Target files

- `geocomp/core/io_network.py`
- `geocomp/core/io_gnss.py`

### Responsibilities

`io_network.py`:

- Map between **QGIS layers** and `Network` objects.
  - Stations layer → `Station` objects.
  - Observations layer(s) → `Observation` objects.
- Support at least:
  - File-based GeoPackage (`.gpkg`).
  - Optional PostGIS via `QgsVectorLayer` (actual DB logic in `postgis.py`).

`io_gnss.py`:

- Scan GNSS folders to detect RINEX files and build `GnssSession` objects.
- Provide helper functions:
  - `find_sessions_in_folder(folder: Path) -> list[GnssSession]`
  - `group_sessions_by_day(sessions)` etc.

### Tasks (for agents)

- [ ] Implement `build_network_from_layers(project: QgsProject, config: GeoCompConfig) -> Network`.
- [ ] Implement `write_network_to_layers(network: Network, project: QgsProject, config: GeoCompConfig)`.
- [ ] Implement minimal RINEX folder scanning (filename-based) to create `GnssSession` objects.

### Done when

- From inside QGIS, the plugin can read stations/observations from layers and construct a `Network` instance.
- GNSS sessions can be discovered from a folder of RINEX files and listed in a QGIS table or log.

---

## 6. Phase 4 – DynAdjust CLI integration

### Target file

- `geocomp/cli/dynadjust_runner.py`

### Public functions (suggested signatures)

```python
def build_dynadjust_inputs(
    network: Network,
    config: DynAdjustConfig,
    work_dir: Path,
) -> dict:
    # Create all DynAdjust input files in work_dir and return their paths.


def run_dynadjust(
    work_dir: Path,
    executable: str = "dynadjust",
    timeout: int = 600,
) -> "DynAdjustRunResult":
    # Call DynAdjust in work_dir and return a small object with returncode, stdout, stderr.


def parse_dynadjust_results(
    work_dir: Path,
) -> "DynAdjustResult":
    # Parse DynAdjust output files and return adjusted stations/observations/statistics.
```

Implement simple result dataclasses:

- `DynAdjustRunResult` → `{returncode: int, stdout: str, stderr: str}`
- `DynAdjustResult` → `{adjusted_stations: dict[str, Station], residuals: list[Observation], stats: dict}`

### Tasks (for agents)

- [ ] Study DynAdjust input format; design how to map `Network` → DynAdjust measurement/constraint files.
- [ ] Implement `build_dynadjust_inputs()` for a simple 2D/3D network case.
- [ ] Implement `run_dynadjust()` using `subprocess.run()` with timeout and error checking.
- [ ] Implement `parse_dynadjust_results()` for at least:
  - Adjusted station coordinates.
  - Observation residuals.
  - Global adjustment statistics (chi-square, etc.).
- [ ] Write tests in `tests/test_dynadjust_runner.py` using a **small synthetic network** and a sample DynAdjust run
      (or using mocked subprocess for CI environments without DynAdjust).

### Done when

- Given a small `Network`, code can:
  - generate valid DynAdjust input files,
  - execute DynAdjust successfully,
  - parse adjusted coordinates and residuals into Python objects.

---

## 7. Phase 5 – RNX2RTKP GNSS pipeline

### Target files

- `geocomp/cli/rnx2rtkp_runner.py`
- `geocomp/cli/products_download.py`
- `geocomp/core/io_gnss.py` (extended)

### Public functions (suggested)

In `rnx2rtkp_runner.py`:

```python
def build_rnx2rtkp_config(
    options: Rnx2rtkpConfig,
    output_path: Path,
) -> Path:
    # Write an RTKLIB-style config file and return its path.


def run_rnx2rtkp(
    obs_file: Path,
    nav_files: list[Path],
    config_file: Path,
    output_pos: Path,
    executable: str = "rnx2rtkp",
    timeout: int = 600,
) -> "Rnx2rtkpRunResult":
    # Run rnx2rtkp for a single session.


def parse_rnx2rtkp_pos(
    pos_file: Path,
) -> list["GnssPosition"]:
    # Parse .pos output into a list of positions (time, coordinates, quality).
```

In `products_download.py`:

```python
def ensure_products_for_sessions(
    sessions: list[GnssSession],
    config: GeoCompConfig,
    cache_dir: Path,
) -> dict[str, list[Path]]:
    """
    For each session, download or reuse precise ephemeris / clock products.
    Return mapping session_id -> list of product file paths.
    """
```

### Tasks (for agents)

- [ ] Implement `Rnx2rtkpConfig` (config.py) with main RTKLIB options.
- [ ] Implement config writer (key=value format used by rnx2rtkp).
- [ ] Implement single-session runner and `.pos` parser (enough for static/kinematic solutions).
- [ ] Implement a simple product download mechanism (e.g. HTTP/FTP from a configurable list of providers).
- [ ] Implement `batch_rnx2rtkp(sessions, config)` helper that:
  - loops over sessions;
  - obtains products via `ensure_products_for_sessions()`;
  - runs rnx2rtkp for each;
  - returns list of GNSS results.
- [ ] Add tests for config generation and `.pos` parsing using small synthetic or sample files.

### Done when

- From RINEX files and config, the code can generate `.pos` files and parse them into coordinates and qualities.
- Sessions can be processed in batch with basic error reporting.

---

## 8. Phase 6 – Processing algorithms (QGIS Processing Provider)

**Goal:** expose the main workflows as Processing algorithms so they can be used from the toolbox,
model builder, and batch processing.

### Algorithms to implement

1. **Project init**
   - **ID:** `geocomp:project_init`
   - **Purpose:** create initial layers (stations, observations) in a GeoPackage or PostGIS schema.

2. **Import terrestrial/gravimetric observations**
   - **ID:** `geocomp:import_observations`
   - **Inputs:** CSV/file path + field mapping.
   - **Outputs:** populated observations layer.

3. **GNSS scan sessions**
   - **ID:** `geocomp:gnss_scan_sessions`
   - **Inputs:** folder path, filename pattern (optional).
   - **Outputs:** table/layer of `GnssSession` records.

4. **GNSS download products**
   - **ID:** `geocomp:gnss_download_products`
   - **Inputs:** sessions table, cache directory, provider URL template.
   - **Outputs:** updated table with product paths.

5. **GNSS RNX2RTKP batch**
   - **ID:** `geocomp:gnss_rnx2rtkp_batch`
   - **Inputs:** sessions table, config file or parameters.
   - **Outputs:** positions/baselines layer(s).

6. **Build baselines as observations**
   - **ID:** `geocomp:gnss_build_baselines`
   - **Inputs:** GNSS positions, station mapping.
   - **Outputs:** new “GNSS baseline” observations appended to observations layer.

7. **Network pre-analysis**
   - **ID:** `geocomp:network_preanalysis`
   - **Inputs:** stations layer, observations layer.
   - **Outputs:** diagnostics (connectivity, basic redundancy, simple consistency checks).

8. **Network adjustment with DynAdjust**
   - **ID:** `geocomp:network_adjust_dynadjust`
   - **Inputs:** stations layer, observations layer, constraints, optional advanced config.
   - **Outputs:** adjusted stations layer, residuals layer/table, summary HTML.

9. **Visualize adjustment results**
   - **ID:** `geocomp:visualize_results`
   - **Inputs:** adjusted stations, residuals, stats.
   - **Outputs:** styled layers (ellipses, vectors, thematic maps).

### Tasks (for agents)

For each algorithm class in `geocomp/algorithms`:

- [ ] Subclass `QgsProcessingAlgorithm`.
- [ ] Implement:
  - [ ] `name()`, `displayName()`, `group()`, `groupId()`, `tr()`.
  - [ ] `createInstance()` returning a new instance.
  - [ ] `initAlgorithm()` defining parameters and outputs.
  - [ ] `processAlgorithm()` calling the appropriate functions from `core/` and `cli/` modules.
- [ ] Ensure each algorithm is registered in `GeoCompProvider.loadAlgorithms()`.

### Done when

- All listed algorithms appear in the Processing Toolbox under the “GeoComp” group.
- Each algorithm can be executed (even if some are initially stubbed with minimal functionality).

---

## 9. Phase 7 – Visualization helpers

### Target file

- `geocomp/core/visualization.py`

### Responsibilities

- Create/update QGIS layers for:
  - adjusted stations (points);
  - residual vectors (line layer);
  - error ellipses (polygon layer);
  - baselines (line layer).
- Apply default styles:
  - symbol sizes based on uncertainty;
  - color ramps based on residual magnitude;
  - ellipses scaled by chosen confidence level (e.g. 95%).

### Tasks (for agents)

- [ ] Implement functions like:

  ```python
  def create_adjusted_stations_layer(result: DynAdjustResult, crs: QgsCoordinateReferenceSystem) -> QgsVectorLayer: ...
  def create_residuals_layer(result: DynAdjustResult, crs: QgsCoordinateReferenceSystem) -> QgsVectorLayer: ...
  ```

- [ ] Use QGIS renderer APIs to set basic styles in code.
- [ ] Ensure Processing algorithms can return these layers as formal outputs.

### Done when

- Running the adjustment algorithm creates styled layers that are immediately interpretable in the QGIS map canvas.

---

## 10. Phase 8 – Storage: GeoPackage + PostGIS

### Target file

- `geocomp/core/postgis.py`

### Responsibilities

- Provide optional persistence layer for networks and results in PostGIS.

### Tasks (for agents)

- [ ] Design a minimal schema (`gc_networks`, `gc_stations`, `gc_observations`, `gc_sessions`, `gc_runs`).
- [ ] Implement helpers:

  ```python
  def store_network(network: Network, conn_name: str, schema: str, network_id: str) -> None: ...
  def load_network(conn_name: str, schema: str, network_id: str) -> Network: ...
  ```

- [ ] Use QGIS `QgsVectorLayer` PostGIS connections where possible for simplicity.
- [ ] Add optional Processing parameters to store/load networks using this schema.

### Done when

- A complete network can be saved to PostGIS and reloaded into a fresh QGIS project using GeoComp tools.

---

## 11. Phase 9 – Internationalisation (i18n) and modes

### Target files

- `geocomp/i18n/*.ts`
- Minor changes across all modules (using translation functions).

### Tasks (for agents)

- [ ] Ensure all user-facing strings pass through translation (`self.tr()` or `QCoreApplication.translate()`).
- [ ] Generate translation source files (`.ts`) for:
  - PT-BR (`geocomp_pt_BR.ts`)
  - EN-US (`geocomp_en_US.ts`)
  - ES (`geocomp_es_ES.ts`)
- [ ] Load translations in plugin initialization (`plugin.py`).
- [ ] Implement a simple mechanism (e.g. in settings) to switch between **Basic** and **Advanced** modes:
  - In Basic mode, algorithms expose fewer parameters.
  - In Advanced mode, additional parameters (e.g., paths to custom DynAdjust / RTKLIB config files) are visible.

### Done when

- Changing the QGIS UI language changes the GeoComp provider / algorithm texts.
- Mode setting (Basic/Advanced) affects visible parameters in Processing dialogs.

---

## 12. Phase 10 – Testing, CI and packaging

### Tasks (for agents)

- [ ] Add unit tests for pure Python modules (`core/*`, `cli/*`) using `pytest` or `unittest`.
- [ ] Add basic integration tests using the PyQGIS test environment where feasible.
- [ ] Configure a CI workflow (GitHub Actions or similar) to run tests on push/PR.
- [ ] Implement a packaging script or document the manual steps to build a ZIP suitable for the QGIS plugin repository.

### Done when

- `pytest` (or equivalent) runs cleanly in CI.
- A single ZIP file containing the `geocomp` folder can be installed in QGIS and passes plugin validation.

---

This roadmap is designed to be consumed **phase by phase**.  
A code agent can take each phase, implement the listed modules and functions, run the tests,
and then move to the next phase.
