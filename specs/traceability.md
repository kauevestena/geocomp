# Traceability

**Status:** Draft
**Purpose:** make coverage gaps mechanically visible. Every specific objective of the research project and
every item of the specified menu structure must map to at least one requirement and to a roadmap phase.

Sources: `research_project/projeto_geocomp_abnt.tex` §Objetivos específicos (O1–O12) and §Painel de
Configuração Global e Menu Principal; `research_project/modificações.md`; `research_project/fig/`.

Checked in CI ([`20-testing-and-validation.md`](./20-testing-and-validation.md) §2): every requirement ID
appears in exactly one phase of [`ROADMAP.md`](./ROADMAP.md), and no row below is empty.

---

## 1. Specific objectives (O1–O12)

| # | Objective (abridged) | Requirements | Phase |
|---|---|---|---|
| **O1** | Architect GeoComp as a QGIS *Processing Provider*, covering network pre-analysis, data preparation and processing | FR-005, FR-030…FR-036, FR-070, FR-270…FR-273 | P0, P2, P3 |
| **O2** | Integrate DynAdjust via the command line: automatic input generation, execution, result import into QGIS | FR-036, FR-163, FR-300…FR-306, FR-320…FR-325, FR-930 | P5, P6 |
| **O3** | Integrate `rnx2rtkp` (RTKLIB) for GNSS processing, including batch runs and automatic product download | FR-164, FR-350…FR-359, FR-600…FR-604 | P7 |
| **O4** | Support multiple geodetic observation types: angles, distances, height differences, gravimetry, GNSS points and baselines | FR-103, FR-104, FR-227, FR-400…FR-411, FR-500…FR-504, FR-602, FR-700, FR-800…FR-803 | P1, P3, P4, P7, P8, P9 |
| **O5** | Integrate PostGIS and other spatial databases for persistent storage of networks, observations and results | FR-130…FR-135 | P5, P11 |
| **O6** | Multi-epoch comparison and structural monitoring: temporal metadata, compatibility checks, transformation, displacements and deformation | FR-105, FR-207, FR-830…FR-838, FR-903, FR-932 | P1, P10 |
| **O7** | Make the plugin trilingual (pt-BR, en, es) using the QGIS i18n infrastructure | FR-090…FR-095 | P0, P12 |
| **O8** | Involve undergraduate and postgraduate students in development, test-data collection and real case studies | FR-950, FR-952, FR-954 | P3, P13 |
| **O9** | Evaluate performance, usability and applicability through case studies and comparison with traditional workflows and commercial software | FR-951, NFR-008 | P2, P13 |
| **O10** | Produce teaching material: tutorials, example projects, datasets | FR-950, FR-952 | P3, P13 |
| **O11** | Maintain the GitHub repository with complete documentation, automated tests and CI | FR-036, FR-134, FR-953, NFR-007, NFR-011, NFR-012 | P0, P1, P5, P6 |
| **O12** | Promote market professional participation across all project phases | FR-954, FR-955 | P13 |

## 2. Menu structure

From `tex §Painel de Configuração Global e Menu Principal` and `fig/menu_estrutura.png`. Specified in
[`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md).

### 2.1 Groups

| Menu group | Requirements | Phase |
|---|---|---|
| GeoComp top-level menu on the QGIS menu bar | FR-002 | P0 |
| Seven entries in order, separator before Global Settings | FR-003, FR-004 | P0 (amended in P2) |
| 1. Total Station | FR-400…FR-412 | P3 |
| 2. Level | FR-500…FR-505 | P4 |
| 3. GNSS | FR-600…FR-604 | P7 |
| 4. Gravimetry | FR-700…FR-703 | P8 |
| 5. Integration | FR-800…FR-805 | P9 |
| 6. Analysis | FR-220…FR-227, FR-250…FR-255, FR-270…FR-273, FR-830…FR-838 | P2, P3, P10 |
| 7. Global Settings | FR-060…FR-069 | P0, P3, P6, P7 |

The Analysis group is not in `fig/menu_estrutura.png`: the figure shows the five technique submenus and
Global Settings. It was added in phase P2 for the operations belonging to no single technique, settling what
[`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) §1.1 left open, and FR-003 and FR-004 were
amended to match rather than being contradicted by the code.

### 2.2 Total Station submenu

| Item (tex, item 1) | Requirement | Phase |
|---|---|---|
| Generalised pre-processing: PD/PI combination | FR-400 | P3 |
| — atmospheric corrections | FR-401 | P3 |
| — instrument corrections | FR-402 | P3 |
| — EDM corrections | FR-403 | P3 |
| Traverse: open, closed, connected | FR-406 | P3 |
| Resection | FR-407 | P3 |
| Forward intersection | FR-408 | P3 |
| Classical networks: triangulation, trilateration, triangulateration | FR-409 | P3 |
| Trigonometric levelling, including leap-frog | FR-410 | P3 |
| 3D radiation | FR-411 | P3 |

### 2.3 Level submenu

| Item (tex, item 2) | Requirement | Phase |
|---|---|---|
| Equal sights (preferred method) | FR-500 | P4 |
| Equidistant sights (obstacle crossing) | FR-501 | P4 |
| Extreme sights (multiple foresights) | FR-502 | P4 |

### 2.4 GNSS submenu

| Item (tex, item 3) | Requirement | Phase |
|---|---|---|
| Absolute → Static (static PPP) | FR-600 | P7 |
| Absolute → Kinematic (kinematic PPP) | FR-600 | P7 |
| Relative → Static (static baselines) | FR-601 | P7 |
| Relative → Kinematic (post-processed RTK, trajectories) | FR-601 | P7 |

### 2.5 Gravimetry submenu

| Item (tex, item 4) | Requirement | Phase |
|---|---|---|
| Pre-processing: scale, tide, static and dynamic drift | FR-701 | P8 |
| Gravimetric network adjustment (absolute and relative differences) | FR-700, FR-702 | P8 |

### 2.6 Integration submenu

| Item (tex, item 5) | Requirement | Phase |
|---|---|---|
| GNSS and Total Station | FR-800 | P9 |
| Total Station and Level | FR-801 | P9 |
| GNSS and Level | FR-802 | P9 |
| Multiple (three or more techniques) | FR-803 | P9 |

### 2.7 Global Settings sections

| Section (tex, item 6) | Requirement | Phase |
|---|---|---|
| Instrumental constants: vertical index, EDM calibration, nominal precisions, closure tolerances | FR-061 | P3 |
| Atmospheric parameters: correction models, default T / P / RH | FR-062 | P3 |
| GNSS configuration: product directories, servers, defaults, antenna and reference station databases | FR-063 | P7 |
| Stochastic models: default weights per type, outlier detection parameters | FR-064 | P3 |
| Reference systems: preferred CRS, default epochs, transformation parameters | FR-065 | P5 |
| Paths and directories: DynAdjust and RTKLIB executables, working directories, report templates | FR-066 | P6 |
| Interface preferences: language, usage mode, units | FR-067 | P0 |

## 3. Other named requirements from the proposal

| Source | Requirement | Phase |
|---|---|---|
| §Aplicação da propagação de covariâncias — rigorous and approximate uncertainty for every quantity | FR-200…FR-208 | P1 |
| §Análise de Qualidade — global χ² test, data snooping, internal and external reliability | FR-250…FR-253 | P2 |
| §Justificativa pedagógica — free and constrained networks, residuals, error ellipses explorable visually | FR-222, FR-254, FR-900, FR-901 | P2, P3 |
| §Arquitetura do plugin — CSV/XLSX and *Adjust* interoperability | FR-160…FR-162 | P3, P4, P5, P6 (FR-161 re-planned into P6 — see [`17`](./17-persistence-and-interoperability.md) §5.2) |
| §Arquitetura do plugin — geoid and height model import, deflection of the vertical | FR-165 | P5 |
| §Arquitetura do plugin — base maps and orthophotos for context | FR-167 | P5 |
| §Arquitetura do plugin — residual, ellipse, displacement vector and thematic map visualisation | FR-900…FR-905 | P3, P10, P12 |
| §Justificativa técnica — immediate visualisation | FR-905 | P3 |
| §Justificativa técnica — reduction of operational error, standardised workflows | FR-035, FR-134, NFR-006 | P0, P3, P5 |
| §Justificativa aplicada — installation in a few clicks | FR-301 | P6 |
| §Justificativa aplicada — monitoring reports, graphical and cartographic | FR-932 | P10 |
| §Integração com o rnx2rtkp — comparative testing of processing configurations | FR-359 | P7 |
| §Integração com o rnx2rtkp — architecture open to other GNSS engines | FR-303 | P6 |
| §Integração com PostGIS — transparent switching between file and database modes | FR-132 | P5, P11 |
| §Integração com PostGIS — traceability and reprocessing | FR-134, FR-135 | P5 |
| §Comparação com softwares comerciais — comparison protocol | FR-951 | P13 |
| §Resultados esperados — upstream feedback to DynAdjust and RTKLIB | FR-955 | P13 |
| §Desenvolvimento aberto — open repository, CI, community | FR-953, FR-954 | P0, P13 |
| modificações.md — dedicated top-level menu by survey technique | FR-002, FR-003, FR-004 | P0 |
| modificações.md — Global Settings window with per-equipment side menus | FR-060, FR-061 | P0, P3 |
| modificações.md — uncertainty for all measured and derived variables, rigorous and heuristic | FR-200, FR-201, FR-202 | P1 |
| modificações.md — student comparison against commercial software | FR-951 | P13 |
| `fig/menu_estrutura.png` — the rendered menu | FR-002, FR-003 | P0 |
| `fig/workflow_geo_comp.png` — menu input → background processing → optional database → QGIS visualisation | FR-005, FR-008, FR-130, FR-131, FR-900 | P0, P3, P5, P11 |

## 4. Requirements with no proposal source

Requirements marked `derived` in [`02-requirements.md`](./02-requirements.md) are engineering consequences,
not additions to the project's scope. Each names what it derives from. They fall into five groups:

| Group | Examples | Derived from |
|---|---|---|
| QGIS platform obligations | FR-006 (clean unload), FR-008 (threading), NFR-001, NFR-005 | The plugin contract |
| Correctness safeguards | FR-104 (clusters), FR-203 (labelling approximations), FR-208 (correlations), FR-226 (rank diagnosis), FR-255 (no silent rejection) | Preventing silently wrong results |
| Reproducibility | FR-133 (schema versioning), FR-134 (provenance), FR-302 (engine versions), NFR-007 | O11 |
| Usability consequences | FR-068 (layered settings), FR-069 (instrument profiles), FR-166 (partial import), FR-901 (stated exaggeration) | Making a stated capability actually usable |
| Security | FR-353, NFR-010 | FR-352 requiring authenticated downloads |

If a `derived` requirement cannot be traced to one of these, it is scope creep and should be challenged in
review.

## 5. Coverage summary

| | Count |
|---|---|
| Objectives O1–O12 | 12, all covered |
| Menu groups | 6, all covered |
| Menu items and Global Settings sections | 30, all covered |
| Functional requirements | 164 |
| Non-functional requirements | 12 |
| Requirements assigned to exactly one phase | 176 / 176 |
