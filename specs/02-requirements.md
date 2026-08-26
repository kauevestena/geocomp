# 02 — Requirements

**Status:** Draft
**Read with:** [`01-vision-and-scope.md`](./01-vision-and-scope.md) for context,
[`traceability.md`](./traceability.md) for coverage, [`ROADMAP.md`](./ROADMAP.md) for sequencing.

Conventions (ID scheme, RFC 2119 keywords, `Source:` values) are defined in [`README.md`](./README.md).
Every requirement below carries its source. `derived` means it follows from another requirement or from a
platform constraint rather than appearing in the proposal; the reason is stated.

**ID blocks.** `0xx` platform · `1xx` data, persistence, interoperability · `2xx` uncertainty and adjustment ·
`3xx` engines · `4xx` total station · `5xx` levelling · `6xx` GNSS · `7xx` gravimetry · `8xx` integration and
multi-epoch · `9xx` visualisation, reporting, community. Gaps are intentional.

---

## 0xx — Platform

### Plugin and menu (FR-001…029)

| ID | Requirement | Source |
|---|---|---|
| FR-001 | The plugin MUST install into QGIS through the standard plugin mechanism and register itself on QGIS startup without further user action. | O1 |
| FR-002 | The plugin MUST add a dedicated top-level **GeoComp** menu to the QGIS menu bar, alongside Project, Edit, View and the rest. | tex §Painel de Configuração Global; `fig/menu_estrutura.png`; modificações.md |
| FR-003 | The GeoComp menu MUST present six entries in this order: Total Station, Level, GNSS, Gravimetry, Integration, and Global Settings, the last separated from the rest. | tex §Painel de Configuração Global; `fig/menu_estrutura.png` |
| FR-004 | Menu groups Total Station, Level, GNSS, Gravimetry and Integration MUST each open a submenu listing the operations specified in [`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md). | tex §Painel de Configuração Global |
| FR-005 | Every menu action MUST be backed by a Processing algorithm that performs the same computation with the same parameters. The menu MUST NOT be the only route to any capability. | derived from O1 (a *Processing Provider* is required so that algorithms are scriptable and chainable); see [`adr/0005-menu-algorithm-parity.md`](./adr/0005-menu-algorithm-parity.md) |
| FR-006 | The plugin MUST unregister its menu, its provider and all its resources cleanly on unload, leaving no orphaned UI elements. | derived (QGIS plugin contract; required for reload during development) |
| FR-007 | The plugin MUST expose a toolbar with the most frequently used actions, configurable to be hidden. | derived from FR-002 (professional profile P3 needs one-click access) |
| FR-008 | Long-running operations MUST execute off the GUI thread and MUST report progress and allow cancellation. | NFR-004; derived (QGIS freezes otherwise) |
| FR-009 | The plugin MUST write diagnostics to the QGIS message log under a `GeoComp` tab, at selectable verbosity. | derived from O2 ("captura de logs") |

### Processing Provider (FR-030…059)

| ID | Requirement | Source |
|---|---|---|
| FR-030 | The plugin MUST register a `QgsProcessingProvider` with the stable id `geocomp`. | O1 |
| FR-031 | Algorithms MUST be organised into Processing groups mirroring the menu groups. | derived from FR-003 |
| FR-032 | Algorithm ids MUST be stable across releases; renaming an algorithm MUST keep a deprecated alias for at least one minor release. | derived (model-builder models and scripts store algorithm ids) |
| FR-033 | Every algorithm MUST be usable from the toolbox, the graphical modeller, batch mode, and PyQGIS with identical results. | O1 |
| FR-034 | Algorithms MUST declare their outputs as formal Processing outputs (layers, files, or numeric/HTML outputs) so they can be chained. | O1 |
| FR-035 | Algorithms MUST validate their inputs and fail with an actionable message naming the offending input, before starting any computation. | NFR-006 |
| FR-036 | Where an algorithm wraps an external engine, the engine's stdout, stderr, exit code, command line and version MUST be recorded in the run's provenance and made available as an output. | O2; O11 |

### Settings and profiles (FR-060…089)

| ID | Requirement | Source |
|---|---|---|
| FR-060 | The plugin MUST provide a **Global Settings** window with a side menu organised by equipment type. | tex §Painel de Configuração Global; modificações.md |
| FR-061 | Global Settings MUST store instrumental constants: vertical index corrections, EDM calibration parameters (additive and scale), prism constants, nominal precisions, and closure tolerances. | tex §Painel de Configuração Global |
| FR-062 | Global Settings MUST store atmospheric parameters: default atmospheric correction model and default temperature, pressure and relative humidity. | tex §Painel de Configuração Global |
| FR-063 | Global Settings MUST store GNSS configuration: product and ephemeris directories, preferred download servers, default processing options, antenna model database, and reference station database. | tex §Painel de Configuração Global |
| FR-064 | Global Settings MUST store stochastic model defaults: default weights per observation type and outlier detection parameters. | tex §Painel de Configuração Global |
| FR-065 | Global Settings MUST store reference system defaults: preferred CRS, default reference epoch, and transformation parameters. | tex §Painel de Configuração Global |
| FR-066 | Global Settings MUST store paths: DynAdjust and RTKLIB executable locations, working directories, and report templates. | tex §Painel de Configuração Global |
| FR-067 | Global Settings MUST store interface preferences: language, usage mode (Basic/Advanced), and units of measure. | tex §Painel de Configuração Global |
| FR-068 | Settings MUST be layered: a project MAY override any global default, and a single algorithm run MAY override the project value. The effective value and its origin MUST be inspectable. | derived from FR-060 (a shared instrument constant must not be silently different between projects) |
| FR-069 | Instrument definitions MUST be manageable as named profiles (add, edit, duplicate, delete, import, export) rather than as a single set of values. | derived from FR-061 (organisations own several instruments) |
| FR-070 | The plugin MUST support two usage modes, **Basic** and **Advanced**; Basic exposes a reduced parameter set with defaults, Advanced exposes the full set including hand-written engine configuration files. | tex §Internacionalização e interface trilíngue; O1 |
| FR-071 | Switching between Basic and Advanced MUST NOT change results for parameters left at their defaults. | derived from FR-070 (otherwise Basic-mode results are not defensible) |

### Internationalisation (FR-090…099)

| ID | Requirement | Source |
|---|---|---|
| FR-090 | The plugin MUST be fully available in Portuguese (pt-BR), English (en) and Spanish (es), covering menus, dialogs, algorithm names, parameter names, help text, messages and errors. | O7 |
| FR-091 | Every user-facing string MUST pass through the translation layer from the commit that introduces it. | derived from O7 (retrofitting is expensive; see [`archive/README.md`](./archive/README.md) item 10) |
| FR-092 | The plugin MUST follow the QGIS UI language, with an explicit override in Global Settings. | O7; FR-067 |
| FR-093 | Translations MUST use the terminology fixed in [`00-glossary.md`](./00-glossary.md). | derived from O7 |
| FR-094 | Numbers, dates and angles MUST be formatted per the active locale; the decimal separator MUST NOT be hard-coded. | derived from O7 (pt-BR and es use a comma) |
| FR-095 | Data files written by GeoComp MUST use a locale-independent representation regardless of UI language. | derived from FR-094 (files must be portable between users) |

---

## 1xx — Data, persistence, interoperability

### Data model (FR-100…129)

| ID | Requirement | Source |
|---|---|---|
| FR-100 | GeoComp MUST represent a Project containing Campaigns, Networks, Stations, Observations, GNSS Sessions and Solutions, as specified in [`04-data-model.md`](./04-data-model.md). | tex §Levantamento de requisitos e modelagem conceitual |
| FR-101 | Every Station MUST carry an identifier, approximate coordinates with their CRS, a constraint status, and free-form metadata. | tex §Levantamento de requisitos |
| FR-102 | Every Observation MUST carry its type, participating stations, value(s), uncertainty, epoch, instrument reference, and provenance. | tex §Levantamento de requisitos; §Aplicação da propagação de covariâncias |
| FR-103 | The model MUST support angles, directions, distances (slope and horizontal), height differences, zenith/vertical angles, azimuths, gravity values and differences, GNSS positions and GNSS baselines. | O4 |
| FR-104 | Observations that share a covariance matrix MUST be representable as a cluster, not as independent scalars. | derived from O4 (GNSS baselines and direction sets are correlated; treating them as independent falsifies the adjustment) |
| FR-105 | Every coordinate set MUST carry both its CRS and its reference epoch. A coordinate set without an epoch MUST be rejected where an epoch is required rather than assumed. | O6 |
| FR-106 | Every Solution MUST carry adjusted coordinates, their full covariance, residuals, statistics, and complete provenance. | O2; O11 |
| FR-107 | The domain model MUST be implementable and testable without a QGIS runtime. | NFR-002 |

### Persistence (FR-130…159)

| ID | Requirement | Source |
|---|---|---|
| FR-130 | GeoComp MUST persist a complete Project — networks, observations, sessions, settings and results — to a single GeoPackage file. | tex §Levantamento de requisitos; O5 |
| FR-131 | GeoComp MUST persist the same content to a PostGIS schema, with tables for stations, observations by type, campaigns, projects, adjustment results, statistics and processing logs, and the keys needed for traceability and reprocessing. | O5; tex §Integração com PostGIS |
| FR-132 | The user MUST be able to switch between file mode and database mode transparently and configurably; the logical schema MUST be identical in both. | tex §Integração com PostGIS ("de forma transparente e configurável") |
| FR-133 | The storage schema MUST carry a version, and GeoComp MUST refuse to open a newer schema and MUST offer migration for an older one. | derived from FR-130 (multi-year project; monitoring data outlives releases) |
| FR-134 | Every stored result MUST record enough provenance — inputs, parameters, engine name and version, timestamps — to reproduce it. | O11; tex §Integração com PostGIS ("rastreabilidade e reprocessamento") |
| FR-135 | Deleting or superseding a Solution MUST NOT delete the observations it was computed from. | derived from FR-134 |

### Interoperability (FR-160…189)

| ID | Requirement | Source |
|---|---|---|
| FR-160 | GeoComp MUST import observations and stations from CSV and from `.xlsx` spreadsheets, with a user-controlled field mapping that can be saved and reused. | tex §Arquitetura do plugin ("planilhas .xlsx e arquivos CSV") |
| FR-161 | GeoComp MUST interoperate with the file format of the *Adjust* software accompanying Ghilani (2010). | tex §Arquitetura do plugin |
| FR-162 | GeoComp MUST export networks and results to CSV and `.xlsx`. | derived from FR-160 |
| FR-163 | GeoComp MUST read and write the DynAdjust interchange formats specified in [`07-engine-dynadjust.md`](./07-engine-dynadjust.md). | O2 |
| FR-164 | GeoComp MUST read RINEX observation and navigation files sufficiently to identify station, receiver, antenna, and the session time span. | O3 |
| FR-165 | GeoComp MUST import geoid models and height models, and apply them for reductions, corrections and approximate estimation of derived quantities such as the deflection of the vertical. | tex §Arquitetura do plugin |
| FR-166 | Import MUST report per-record errors without aborting the whole import, and MUST leave the target unchanged if the user cancels. | NFR-006 |
| FR-167 | GeoComp MUST integrate base maps and orthophotos for cartographic context of processed and planned networks. | tex §Arquitetura do plugin |

---

## 2xx — Uncertainty and adjustment

### Covariance propagation (FR-200…219)

| ID | Requirement | Source |
|---|---|---|
| FR-200 | Every measured and derived geodetic quantity in GeoComp MUST carry an uncertainty estimate. | modificações.md ("para todas as medidas e variáveis seja possível realizar estimativa de seus níveis de incerteza"); tex §Aplicação da propagação de covariâncias |
| FR-201 | GeoComp MUST implement rigorous covariance propagation, **Σ**_La = **A Σ**_Lb **A**ᵀ, with **A** the Jacobian of the transformation. | tex §Propagação de variâncias e covariâncias |
| FR-202 | GeoComp MUST also implement approximate/heuristic uncertainty estimation for use where complete input covariance information is unavailable or where simplification is acceptable. | tex §Aplicação da propagação de covariâncias |
| FR-203 | Any result computed by the approximate path MUST be labelled as such wherever it is displayed, exported or reported. | derived from FR-202 (a professional deliverable must not present a heuristic figure as rigorous) |
| FR-204 | Covariance MUST be propagated through observation pre-processing, including atmospheric, instrument and EDM corrections, carrying the uncertainty of the correction parameters. | tex §Aplicação da propagação de covariâncias |
| FR-205 | Covariance MUST be propagated through geometric reductions — to the ellipsoid, to the projection plane, and between heights — carrying the uncertainty of the heights and coordinates used. | tex §Aplicação da propagação de covariâncias |
| FR-206 | GNSS solution covariance matrices MUST be preserved end-to-end and used in combined adjustment, not reduced to a scalar. | tex §Aplicação da propagação de covariâncias |
| FR-207 | Covariance MUST be propagated into the displacement computation of multi-epoch comparison so that the statistical significance of a detected displacement can be assessed. | tex §Aplicação da propagação de covariâncias; O6 |
| FR-208 | Correlations between quantities MUST be preserved through propagation; treating correlated inputs as independent MUST require an explicit user choice. | derived from FR-201 |

### Adjustment (FR-220…249)

| ID | Requirement | Source |
|---|---|---|
| FR-220 | GeoComp MUST provide its own least-squares adjustment implementation using the parametric model, independent of any external engine. | derived — required by FR-700 (gravimetry, unsupported by DynAdjust), FR-270 (pre-analysis), the teaching profile P1, and CI without engine binaries. See [`adr/0002-in-house-lsq-core.md`](./adr/0002-in-house-lsq-core.md) |
| FR-221 | The adjustment MUST accept a full weight matrix derived from the observation covariance matrix, including correlations. | tex §Fundamentos do Ajustamento de Observações |
| FR-222 | The adjustment MUST support free networks (minimum-constraint and inner-constraint datum definition) and constrained networks (fixed and weighted stations). | tex §Justificativa pedagógica ("redes livres e amarradas") |
| FR-223 | The adjustment MUST iterate the linearised solution to convergence, with configurable criteria and a reported iteration count. | derived from FR-220 (the observation equations are non-linear) |
| FR-224 | The adjustment MUST report the estimated parameters with their full covariance matrix. | tex §Aplicação da propagação de covariâncias |
| FR-225 | The adjustment MUST report per-observation residuals, standardised residuals and redundancy numbers. | tex §Análise de Qualidade de Redes Geodésicas |
| FR-226 | The adjustment MUST detect and report a rank-deficient or ill-conditioned system with a diagnosis naming the affected stations, rather than returning a numerically meaningless result. | NFR-006; derived from FR-222 |
| FR-227 | 1D (height), 2D (planimetric) and 3D adjustment MUST all be supported. | O4 |

### Statistical validation and reliability (FR-250…269)

| ID | Requirement | Source |
|---|---|---|
| FR-250 | GeoComp MUST perform the global (chi-square) test comparing the a posteriori variance factor with the a priori value, reporting the statistic, the critical values, the confidence level and the decision. | tex §Análise de Qualidade de Redes Geodésicas |
| FR-251 | GeoComp MUST perform data snooping (Baarda's w-test) on standardised residuals to identify rejectable observations, reporting per-observation statistics and decisions. | tex §Análise de Qualidade de Redes Geodésicas |
| FR-252 | GeoComp MUST compute internal reliability (the minimal detectable bias per observation) for configurable α and β. | tex §Análise de Qualidade de Redes Geodésicas |
| FR-253 | GeoComp MUST compute external reliability — the effect on the adjusted coordinates of an undetected blunder at the MDB. | tex §Análise de Qualidade de Redes Geodésicas |
| FR-254 | GeoComp MUST compute error ellipses (2D) and error ellipsoids (3D) for adjusted stations, at a user-selectable confidence level, both absolute and relative between station pairs. | tex §Arquitetura do plugin; §Integração com o DynAdjust |
| FR-255 | Where an observation is rejected as an outlier, the rejection MUST be recorded, reversible, and never silent; re-adjustment after rejection MUST be an explicit action. | derived from FR-251 (automatic iterative rejection can delete real signal, which in monitoring is the thing being measured) |

### Pre-analysis (FR-270…289)

| ID | Requirement | Source |
|---|---|---|
| FR-270 | GeoComp MUST provide network pre-analysis: computing the expected precision of a *planned* network from its geometry and assumed observation precisions, before any observation exists. | O1 ("algoritmos de pré-análise de redes") |
| FR-271 | Pre-analysis MUST report expected error ellipses and expected internal and external reliability, so a design can be judged against a specification. | derived from FR-270 + FR-252/253 |
| FR-272 | Pre-analysis MUST allow a design to be edited on the QGIS canvas — adding, moving and removing planned stations and observations — and re-evaluated. | derived from FR-270 (this is the value of doing it inside a GIS) |
| FR-273 | GeoComp MUST additionally provide network *inspection* checks on real data: connectivity, isolated stations, duplicate observations, missing approximate coordinates and gross inconsistencies. | derived — the capability the archived roadmap called "pre-analysis"; genuinely useful, but distinct from FR-270 |

---

## 3xx — Engines

### Engine management (FR-300…319)

| ID | Requirement | Source |
|---|---|---|
| FR-300 | GeoComp MUST locate engine executables automatically, and MUST allow explicit paths to be configured. | FR-066 |
| FR-301 | GeoComp MUST be able to acquire the engines without the user using a command line, per [`adr/0003-engine-acquisition.md`](./adr/0003-engine-acquisition.md). | tex §Justificativa aplicada e comercial ("bastando instalar o QGIS e o plugin, com poucos cliques") |
| FR-302 | GeoComp MUST detect and record the version of each engine, and MUST warn when a version is outside the tested range. | derived from FR-036 (parsers are version-sensitive) |
| FR-303 | Engine invocation MUST be through a common abstraction so that an additional engine can be added without changing calling code. | tex §Integração com o rnx2rtkp ("a arquitetura modular do GeoComp permitirá a incorporação futura de outros motores") |
| FR-304 | Every engine run MUST capture stdout, stderr, exit code and wall time, and MUST enforce a configurable timeout. | O2 |
| FR-305 | An engine failure MUST surface the engine's own diagnostic message to the user, not merely a non-zero exit code. | NFR-006 |
| FR-306 | GeoComp MUST function, with reduced capability, when an engine is absent; affected operations MUST be disabled with an explanation rather than failing at run time. | derived from FR-301 |

### DynAdjust (FR-320…349)

| ID | Requirement | Source |
|---|---|---|
| FR-320 | GeoComp MUST generate valid DynAdjust input automatically from stations and observations held in QGIS layers, a database, CSV files or spreadsheets. | O2; tex §Integração com o DynAdjust |
| FR-321 | GeoComp MUST drive the DynAdjust pipeline (import, reference-frame transformation, geoid application, segmentation, adjustment, plotting) as specified in [`07-engine-dynadjust.md`](./07-engine-dynadjust.md), exposing the stages the user needs and defaulting the rest. | O2 |
| FR-322 | GeoComp MUST parse DynAdjust output: adjusted coordinates, adjustment statistics, residuals and positional uncertainty / covariance information. | O2; tex §Integração com o DynAdjust |
| FR-323 | Parsed DynAdjust results MUST populate the same Solution structure as the in-house adjustment, so downstream visualisation, reporting and multi-epoch analysis are engine-independent. | derived from FR-220 + FR-322 |
| FR-324 | GeoComp MUST convert DynAdjust results into QGIS geographic objects with error ellipses, displacement vectors and thematic quality maps. | tex §Integração com o DynAdjust |
| FR-325 | Advanced mode MUST allow the user to supply their own DynAdjust configuration and to inspect and edit the generated input files before execution. | FR-070 |

### RTKLIB / `rnx2rtkp` (FR-350…379)

| ID | Requirement | Source |
|---|---|---|
| FR-350 | GeoComp MUST model GNSS projects as sessions, stations and their RINEX observation and navigation files. | tex §Integração com o rnx2rtkp |
| FR-351 | GeoComp MUST discover GNSS sessions by scanning a folder, using file content where available and file naming as a fallback. | tex §Integração com o rnx2rtkp; O3 |
| FR-352 | GeoComp MUST download precise ephemerides, clock products and other required products automatically from configurable services, and MUST cache them. | O3; tex §Integração com o rnx2rtkp |
| FR-353 | Product download MUST handle services requiring authentication, storing credentials through the QGIS authentication system and never in plain text. | derived from FR-352 (major archives require credentials) |
| FR-354 | GeoComp MUST generate `rnx2rtkp` configuration files from user parameters or from predefined profiles. | tex §Integração com o rnx2rtkp |
| FR-355 | GeoComp MUST execute single-session and batch processing with progress monitoring and per-session error reporting that does not abort the batch. | tex §Integração com o rnx2rtkp; O3 |
| FR-356 | GeoComp MUST parse `rnx2rtkp` output into positions, baselines and quality indicators, preserving the covariance information the solution provides. | tex §Integração com o rnx2rtkp; FR-206 |
| FR-357 | GeoComp MUST import GNSS results as QGIS layers for analysis and for joint adjustment with other observations. | tex §Integração com o rnx2rtkp |
| FR-358 | GeoComp MUST support static and kinematic post-processing, with precise ephemerides, atmospheric correction models and solution quality parameters. | tex §Integração com o rnx2rtkp |
| FR-359 | GeoComp MUST offer comparative testing of different GNSS processing configurations over the same data, presenting the results side by side. | tex §Integração com o rnx2rtkp |

---

## 4xx — Total Station module

**Source for the whole block:** tex §Painel de Configuração Global, item 1 (Estação Total); modificações.md.
Seed implementation reference: `topo_test/processing_prototype.ipynb`.

| ID | Requirement | Source |
|---|---|---|
| FR-400 | GeoComp MUST provide generalised total-station pre-processing combining face-left and face-right (PD/PI) observations. | tex item 1 |
| FR-401 | Pre-processing MUST apply atmospheric corrections (first-velocity/refractive-index correction from temperature, pressure and humidity). | tex item 1 |
| FR-402 | Pre-processing MUST apply instrument corrections, including vertical index error and collimation. | tex item 1 |
| FR-403 | Pre-processing MUST apply EDM corrections, including additive (prism) constant and scale. | tex item 1 |
| FR-404 | Pre-processing MUST reduce slope distances to horizontal distances and compute height differences accounting for instrument and target heights. | derived from FR-400 (implemented in the prototype; required by every downstream computation) |
| FR-405 | Pre-processing MUST apply geometric reductions to the ellipsoid and to the projection plane, and corrections for Earth curvature and atmospheric refraction in trigonometric heighting. | tex §Aplicação da propagação de covariâncias; derived from FR-406 |
| FR-406 | GeoComp MUST compute and adjust traverses: open, closed (loop) and connected (enquadradas), with closure computation against tolerance. | tex item 1 |
| FR-407 | GeoComp MUST compute resection: coordinates of an occupied station from sights to known points. | tex item 1 |
| FR-408 | GeoComp MUST compute forward intersection: coordinates of a sighted point from known stations. | tex item 1 |
| FR-409 | GeoComp MUST adjust classical networks — triangulation, trilateration and triangulateration — from angular and/or distance observations. | tex item 1 |
| FR-410 | GeoComp MUST compute trigonometric levelling from vertical angles, slope distances and instrument heights, including the leap-frog method. | tex item 1 |
| FR-411 | GeoComp MUST compute 3D radiation: three-dimensional coordinates from horizontal angle, vertical angle, slope distance and heights. | tex item 1 |
| FR-412 | Every operation in this block MUST propagate uncertainty per FR-200…FR-208. | FR-200 |

---

## 5xx — Level module

**Source for the whole block:** tex §Painel de Configuração Global, item 2 (Nível).

| ID | Requirement | Source |
|---|---|---|
| FR-500 | GeoComp MUST process geometric levelling by the equal-sights method (backsight and foresight distances equal), identified as the preferred method. | tex item 2 |
| FR-501 | GeoComp MUST process geometric levelling by the equidistant-sights method used for crossing obstacles such as rivers. | tex item 2 |
| FR-502 | GeoComp MUST process geometric levelling by the extreme-sights method with multiple foresights from one setup. | tex item 2 |
| FR-503 | GeoComp MUST compute levelling line and loop closures and compare them against configurable tolerances. | derived from FR-500 (a levelling result is not usable without a closure check) |
| FR-504 | GeoComp MUST adjust levelling networks, weighting height differences by line length or number of setups. | O4; derived from FR-500 |
| FR-505 | Levelling operations MUST propagate uncertainty per FR-200…FR-208. | FR-200 |

---

## 6xx — GNSS module

**Source for the whole block:** tex §Painel de Configuração Global, item 3 (GNSS).

| ID | Requirement | Source |
|---|---|---|
| FR-600 | The GNSS menu MUST offer **Absolute** processing with Static (static PPP) and Kinematic (kinematic PPP) options. | tex item 3 |
| FR-601 | The GNSS menu MUST offer **Relative** processing with Static (static baselines) and Kinematic (post-processed RTK and kinematic trajectories) options. | tex item 3 |
| FR-602 | GeoComp MUST derive GNSS baseline observations, with their 3×3 covariance, from processed sessions, ready for combined adjustment. | O4; tex §Integração com o rnx2rtkp |
| FR-603 | GeoComp MUST report GNSS solution quality indicators per session and per epoch, including ambiguity resolution status, satellite count and dilution of precision. | tex §Integração com o rnx2rtkp |
| FR-604 | Where an engine's capability for a requested mode is known to be limited, GeoComp MUST state this in the UI rather than silently producing a degraded result. | derived from FR-600; see the PPP risk in [`08-engine-rtklib.md`](./08-engine-rtklib.md) |

---

## 7xx — Gravimetry module

**Source for the whole block:** tex §Painel de Configuração Global, item 4 (Gravímetro).

| ID | Requirement | Source |
|---|---|---|
| FR-700 | GeoComp MUST adjust gravimetric networks by least squares, supporting absolute and relative gravity differences. | tex item 4 |
| FR-701 | GeoComp MUST apply gravimetric pre-processing: instrument scale correction, tidal correction, and static and dynamic drift. | tex item 4 |
| FR-702 | The gravimetric adjustment MUST estimate drift parameters jointly with station gravity values where the observation scheme supports it. | derived from FR-701 (drift is not separable from gravity differences by pre-correction alone) |
| FR-703 | Gravimetric operations MUST propagate uncertainty per FR-200…FR-208. | FR-200 |

---

## 8xx — Integration and multi-epoch

### Combined adjustment (FR-800…829)

**Source for the block:** tex §Painel de Configuração Global, item 5 (Integração).

| ID | Requirement | Source |
|---|---|---|
| FR-800 | GeoComp MUST perform combined adjustment of GNSS baselines with terrestrial observations. | tex item 5 |
| FR-801 | GeoComp MUST perform combined adjustment of total-station and levelling observations. | tex item 5 |
| FR-802 | GeoComp MUST perform combined adjustment of GNSS and levelling observations, relating ellipsoidal and orthometric heights. | tex item 5 |
| FR-803 | GeoComp MUST perform combined adjustment of three or more techniques simultaneously. | tex item 5 |
| FR-804 | Combined adjustment MUST apply a geoid model when relating ellipsoidal and orthometric heights, and MUST record which model was used. | FR-165; derived from FR-802 |
| FR-805 | Combined adjustment MUST allow per-technique variance component scaling so that the relative weighting of techniques can be examined and reported. | derived from FR-221 (combining techniques with mis-scaled stochastic models is the classic failure mode) |

### Multi-epoch and monitoring (FR-830…879)

**Source for the block:** O6; tex §Comparação multiépoca e monitoramento de estruturas; §Introdução.

| ID | Requirement | Source |
|---|---|---|
| FR-830 | GeoComp MUST store temporal metadata — date, time, reference epoch and coordinate system — with every solution and campaign. | O6; tex §Comparação multiépoca |
| FR-831 | GeoComp MUST verify compatibility between solutions from different epochs before comparing them, and MUST refuse to difference incompatible solutions. | O6 |
| FR-832 | GeoComp MUST apply coordinate transformations automatically where needed to bring solutions to a common frame and epoch, recording the transformation applied. | O6; tex §Comparação multiépoca |
| FR-833 | GeoComp MUST compute displacement vectors between epochs, with their covariance. | O6; FR-207 |
| FR-834 | GeoComp MUST test the statistical significance of each computed displacement and report which displacements are significant at a stated confidence level. | FR-207; tex §Aplicação da propagação de covariâncias |
| FR-835 | GeoComp MUST support definition of reference epochs, and MUST support identifying a stable reference block against which object points are compared. | tex §Comparação multiépoca; §Introdução (Kuang) |
| FR-836 | GeoComp MUST compute deformation statistics across the network, not only per-station displacements. | O6; tex §Comparação multiépoca |
| FR-837 | GeoComp MUST support configurable alert thresholds and MUST flag stations exceeding them. | tex §Comparação multiépoca |
| FR-838 | GeoComp MUST produce coordinate time series per station across monitoring epochs, exportable and plottable. | tex §Comparação multiépoca |

---

## 9xx — Visualisation, reporting, community

### Visualisation (FR-900…929)

| ID | Requirement | Source |
|---|---|---|
| FR-900 | GeoComp MUST produce styled QGIS layers for adjusted stations, residuals, error ellipses, baselines and displacement vectors. | tex §Arquitetura do plugin ("ferramentas auxiliares para visualização de resíduos, elipses de erro, vetores de deslocamento e mapas representativos") |
| FR-901 | Error ellipses MUST be drawn at a user-selectable confidence level with an explicit, adjustable exaggeration factor stated in the legend. | derived from FR-254 (real ellipses are invisible at map scale; an unstated exaggeration is misleading) |
| FR-902 | GeoComp MUST produce thematic quality maps — for example by positional uncertainty, standardised residual, or redundancy number. | tex §Integração com o DynAdjust |
| FR-903 | GeoComp MUST plot coordinate time series for monitoring networks. | tex §Comparação multiépoca |
| FR-904 | Layer styling MUST be shipped as editable QML style files, not only as code. | derived from FR-900 (users must be able to restyle for their own reports) |
| FR-905 | Results MUST be immediately interpretable on the map canvas without manual styling after an algorithm runs. | tex §Justificativa técnica ("Visualização imediata") |

### Reporting (FR-930…949)

| ID | Requirement | Source |
|---|---|---|
| FR-930 | GeoComp MUST generate an adjustment report containing inputs, parameters, results, statistics, tests and provenance. | derived from O2 + O9 (a professional deliverable and the basis of commercial comparison) |
| FR-931 | Reports MUST be exportable in a form suitable for inclusion in a technical deliverable, and MUST be template-driven per FR-066. | FR-066 |
| FR-932 | GeoComp MUST generate a monitoring report with displacement table, significance results, map and time series. | tex §Justificativa aplicada ("geração de relatórios gráficos e cartográficos") |

### Validation, documentation, community (FR-950…979)

| ID | Requirement | Source |
|---|---|---|
| FR-950 | GeoComp MUST ship reference datasets with known correct results, usable for validation and for teaching. | O10 |
| FR-951 | The project MUST provide a documented protocol for comparing GeoComp results against commercial software, including how discrepancies are investigated and reported. | O9; tex §Comparação com softwares comerciais |
| FR-952 | The project MUST publish tutorials, worked examples and datasets suitable for undergraduate and postgraduate teaching. | O10 |
| FR-953 | The project MUST maintain a public repository with complete documentation, automated tests and continuous integration. | O11 |
| FR-954 | The project MUST document how external contributors — students, professionals, companies, public bodies — participate. | O8; O12; tex §Desenvolvimento aberto e colaboração |
| FR-955 | GeoComp MUST make it straightforward to report an engine-side defect upstream, preserving the inputs that triggered it. | tex §Resultados esperados ("Retroalimentação") |

---

## NFR — Non-functional requirements

| ID | Requirement | Source |
|---|---|---|
| NFR-001 | The plugin MUST target the QGIS **4.x** series: the current 4.x Long Term Release once one exists, and the current stable release until then. It MUST state its minimum QGIS version in `metadata.txt`. The 3.x series is deliberately not supported. | derived (plugin repository requirement); [`adr/0007-qgis-4-minimum.md`](./adr/0007-qgis-4-minimum.md) |
| NFR-002 | The geodetic computation layer MUST NOT import `qgis` or `PyQt`. This is enforced in CI. | derived from FR-107 — testability without a QGIS runtime, and reusability of the core; see [`03-architecture.md`](./03-architecture.md) |
| NFR-003 | The plugin MUST work on Windows, macOS and Linux. | derived from FR-301 (engines are distributed for all three) |
| NFR-004 | The UI MUST remain responsive during processing; no operation may block the GUI thread for more than 200 ms. | derived from FR-008 |
| NFR-005 | Runtime dependencies beyond those shipped with QGIS MUST be minimised and justified; each additional dependency requires a recorded decision. | derived from FR-001 (QGIS plugins cannot rely on the user's `pip`) |
| NFR-006 | Error messages MUST state what failed, why, and what the user can do about it. Stack traces alone are not acceptable user-facing errors. | tex §Justificativa técnica ("Redução de erros operacionais") |
| NFR-007 | Numerical results MUST be reproducible: the same inputs, parameters and engine version MUST produce identical output. | O11; FR-134 |
| NFR-008 | Adjustment MUST handle networks of at least 10,000 stations in file mode within practical time and memory on typical hardware; beyond that, DynAdjust segmentation is the supported path. | derived from FR-220 (bounds the in-house core against the engine's scale, per `tex §O Software DynAdjust`) |
| NFR-009 | The plugin MUST be licensed GPL-2.0-or-later, and MUST ship the notices required by its third-party components. | [`adr/0001-licensing.md`](./adr/0001-licensing.md) |
| NFR-010 | No credential, token or personal datum may be written to logs, provenance records or exported files. | derived from FR-353 |
| NFR-011 | Every module MUST have automated tests; the pure-Python core MUST be covered by tests that run without QGIS and without engine binaries. | O11; NFR-002 |
| NFR-012 | Public interfaces between modules MUST be documented and type-annotated. | derived from O11 (external contributors) |

---

## Withdrawn requirements

None yet. When a requirement is withdrawn it is moved here with its ID, original text and the reason; the ID
is never reused.
