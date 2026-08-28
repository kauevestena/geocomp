# 15 — UI: the GeoComp menu and Global Settings

**Status:** Draft
**Requirements covered:** FR-002…FR-007, FR-060…FR-071, FR-272.
**Source:** tex §Painel de Configuração Global e Menu Principal; `fig/menu_estrutura.png`; modificações.md.

The proposal devotes a full subsection and a figure to this. The archived roadmap omits it entirely
([`archive/README.md`](./archive/README.md), item 2), which is why it is specified here in full.

---

## 1. The GeoComp menu (FR-002, FR-003)

A **top-level menu on the QGIS menu bar**, alongside Project, Edit, View and the rest — not a submenu under
Plugins. `fig/menu_estrutura.png` shows it rendered exactly there.

```text
GeoComp
 ├── Total Station        ▸
 ├── Level                ▸
 ├── GNSS                 ▸
 ├── Gravimetry           ▸
 ├── Integration          ▸
 ├── Analysis             ▸     (added in phase P2 — see §1.1)
 ├──────────────────────────   (separator)
 └── Global Settings…
```

The separator before Global Settings, and the ellipsis on it, follow the figure and standard menu convention
(the item opens a dialog rather than performing an action).

> **Naming note.** The proposal's text calls the fourth group *Gravímetro* (the instrument) while
> `fig/menu_estrutura.png` shows *Gravimetria* (the technique). GeoComp uses **Gravimetry / Gravimetria /
> Gravimetría**, matching the figure and matching the technique-based naming of every other group. Recorded
> in [`00-glossary.md`](./00-glossary.md) §Ambiguities resolved.

### 1.1 Submenu contents (FR-004)

Directly from `tex §Painel de Configuração Global`:

**Total Station** → Import field book · Generalised pre-processing · Traverse · Resection · Forward
intersection · Classical networks · Trigonometric levelling · 3D radiation.
See [`09-module-total-station.md`](./09-module-total-station.md).

> **Import field book** is not in the proposal's list, which starts at pre-processing. It is added because
> the list assumes the data is already in GeoComp and nothing else puts it there: FR-160's saved field
> mapping is a total-station capability (`specs/09` §5 specifies it against RD-01's layout), and a user who
> has to hunt for it in another submenu before they can use any of the seven has been given a worse menu,
> not a purer one.

**Level** → Import levelling field book · Equal sights · Equidistant sights · Extreme sights · Closures and
tolerances · Levelling network adjustment. *(Six as built in P4, rather than the proposal's four: import and
closures were implicit in the others and each produces a document the next step reads — see
[`10`](./10-module-levelling.md) §1.)*
See [`10-module-levelling.md`](./10-module-levelling.md).

**GNSS** → Absolute (Static · Kinematic) · Relative (Static · Kinematic) · Scan sessions · Download products ·
Batch processing · Build baselines · Compare configurations.
See [`11-module-gnss.md`](./11-module-gnss.md).

**Gravimetry** → Pre-processing · Gravimetric network adjustment.
See [`12-module-gravimetry.md`](./12-module-gravimetry.md).

**Integration** → GNSS and Total Station · Total Station and Level · GNSS and Level · Multiple.
See [`13-module-integration.md`](./13-module-integration.md).

**Analysis** → Inspect network · Pre-analyse network design · Adjust network · *(multi-epoch comparison and
the monitoring report join it in P10).*
See [`06-adjustment-core.md`](./06-adjustment-core.md) §5 and
[`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md).

#### Why Analysis is a seventh entry (settled in P2)

This document previously left the placement open, noting that a top-level Analysis group was the likely
answer. Phase P2 needed it, and it was settled then rather than in P3, because the alternatives are worse in
ways that are easy to state:

- **Filing them under one technique** — say Total Station — would say something false about them. Network
  adjustment, inspection and pre-analysis are what the technique modules *feed*; a levelling user needs them
  as much as a total-station user, and would not look under Total Station to find them.
- **Duplicating them across all five** would break the one-item-per-algorithm correspondence ADR-0005 rests
  on: the menu is generated from the algorithm registry, and an algorithm appearing five times has no single
  menu route.
- **Leaving them toolbox-only** would put the plugin's central capability outside the menu the proposal
  devotes a figure to.

A seventh entry leaves both the figure's five technique submenus and the algorithm correspondence intact.
FR-003 and FR-004 are amended to say seven rather than being quietly contradicted by the code, and
`tests/test_registry.py` asserts both the new list and that the figure's five come first, in its order.

### 1.2 The menu is a launcher (FR-005)

Every menu item runs a Processing algorithm. The menu holds no second implementation. Consequences:

- The menu is **generated from the algorithm registry**, so an algorithm cannot exist without a menu route
  and a menu item cannot point at nothing.
- Menu item names, groups and ordering come from algorithm metadata, and are translated once (FR-090).
- Most items open the standard Processing dialog. A small, enumerated set opens a custom dialog that
  collects parameters and then runs the same algorithm:

| Custom dialog | Why the standard dialog is insufficient |
|---|---|
| Global Settings | Not an algorithm at all — it configures the others |
| Interactive pre-analysis (FR-272) | Design is edited on the canvas and re-evaluated in a loop. Arrives in P3, re-planned out of P2 — see [`ROADMAP.md`](./ROADMAP.md). The non-interactive route, `geocomp:analysis_network_preanalysis`, ships in P2 |
| Field mapping for import (FR-160) | Needs a preview of the source data to map columns against |
| Comparative GNSS configuration (FR-359) | Runs *n* configurations and shows a side-by-side comparison |
| Multi-epoch comparison (FR-831) | Needs to display compatibility findings before the user commits |
| Monitoring time series (FR-838) | An interactive panel, not a one-shot run |

#### Toolbox-only algorithms

A small, enumerated set of algorithms has **no menu entry at all**. The GeoComp menu presents five
technique-oriented entries plus Analysis (FR-003); an operation belonging to no survey technique and to no
analysis of one — environment diagnostics, maintenance — would have to be filed under one of them, which
would misrepresent that structure.

Permitted only for maintenance and diagnostic operations, and only with the reason recorded in code, in
`geocomp/registry.py`'s `TOOLBOX_ONLY_JUSTIFICATIONS`. The parity test holds the exception list to exactly
the algorithms that declare a justification, fails on a justification left behind by a deleted algorithm, and
fails if the list grows beyond a handful — a growing list means the menu is drifting away from the
algorithms, which is the drift ADR-0005 exists to prevent.

| Toolbox-only algorithm | Why it has no menu entry |
|---|---|
| `geocomp:project_system_report` | Environment diagnostics belong to no survey technique. Reachable from the toolbox and from the About dialog under Plugins ▸ GeoComp |
| `geocomp:project_tutorial_dataset` | Installing a reference dataset belongs to no survey technique. RD-01 is a total-station survey, but the operation is *copy files somewhere writable*, and the levelling and GNSS datasets to come would use the same algorithm — filing it under Total Station would misplace it the moment the second one ships |

Note the asymmetry, which is deliberate: **every menu item must resolve to a registered algorithm** with no
exceptions, because a menu item pointing at nothing is a broken UI. The reverse direction admits this narrow,
recorded exception.

Recorded as [`adr/0005-menu-algorithm-parity.md`](./adr/0005-menu-algorithm-parity.md).

### 1.3 Toolbar (FR-007)

A GeoComp toolbar with a small set of frequent actions — open/create project, run last algorithm, network
inspection, adjust, and the results panel — hideable through the standard QGIS toolbar controls.

### 1.4 Unload (FR-006)

`unload()` removes the menu, the toolbar, the provider, every action, every dock panel and every signal
connection. Reload during development must leave no duplicate menu behind — a specific, tested condition.

---

## 2. Global Settings (FR-060)

> *"'Configurações Globais' que deverá abrir uma janela onde com menus laterais para cada tipo de
> equipamento, onde deverão estar armazenadas constantes e valores configuráveis para os possíveis fluxos de
> trabalho do plugin."* — `research_project/modificações.md`

A dialog with a **side menu**, the sections organised primarily by equipment type as specified.

```text
┌──────────────────┬──────────────────────────────────────────────┐
│ Total Station    │                                              │
│ Level            │   (settings for the selected section)        │
│ GNSS             │                                              │
│ Gravimeter       │                                              │
│ ───────────────  │                                              │
│ Stochastic model │                                              │
│ Reference systems│                                              │
│ Paths & engines  │                                              │
│ Interface        │                                              │
├──────────────────┴──────────────────────────────────────────────┤
│                      [Restore defaults]  [Cancel]  [OK]         │
└─────────────────────────────────────────────────────────────────┘
```

Equipment sections first, then the cross-cutting ones, separated.

### 2.1 Section contents

Each row below is a requirement, taken from `tex §Painel de Configuração Global`, item 6.

| Section | Contents | Req |
|---|---|---|
| **Total Station** | Instrument profiles (§2.2): vertical index correction, collimation, EDM additive constant and scale, cyclic error, nominal precisions for direction / zenith angle / distance. Reflector profiles with prism constants. Atmospheric model and default temperature, pressure, humidity. Refraction coefficient. Closure tolerances by traverse class | FR-061, FR-062 |
| **Level** | Default weighting (length or setups). Permissible-misclosure coefficient *k*. Sight-length, per-setup and per-line imbalance limits. Reciprocal-sight variance inflation. Orthometric corrections on or off. Whether a line that failed its tolerance may be adjusted | FR-061, FR-503, FR-504 |

**Level profiles and levelling classes are not settings**, for the same reason instrument profiles are not
(§2.2): they are named, structured records with their own uncertainties and their own provenance, so they
live in `geocomp.core.instruments.level` and travel as documents. A department owns several levels and works
under more than one specification at once; a single "the" tolerance would be wrong for all but one job.
| **GNSS** | Product and ephemeris directories; preferred download servers and their priority; default processing options per mode; antenna model database (ANTEX); reference station database; credential references (never the credentials) | FR-063, NFR-010 |
| **Gravimeter** | Gravimeter profiles: calibration table and factor, nominal precision, drift characteristics. Tidal model. Display unit (mGal / µGal) | FR-061 |
| **Stochastic model** | Default weights per observation type; outlier detection parameters (α, β); variance component estimation defaults | FR-064 |
| **Reference systems** | Preferred CRS; default reference epoch; transformation parameters and preferred transformation paths; default geoid model | FR-065 |
| **Paths & engines** | DynAdjust and RTKLIB executable locations, engine installation and update, working directories, report templates | FR-066, FR-300 |
| **Interface** | Language; usage mode (Basic / Advanced); units of measure; angle display format; decimal places; log verbosity | FR-067, FR-092 |

### 2.2 Instrument profiles (FR-069)

Instrument settings are **named profiles**, not a single set of values: add, edit, duplicate, delete, import,
export. A department owns several total stations; a value that is "the" instrument constant is wrong for all
but one of them.

Each profile records make, model, serial number, calibration date, calibration certificate reference, and its
constants with their uncertainties. Observations reference an instrument by id
([`04-data-model.md`](./04-data-model.md) §2.5), so a later calibration correction can be traced to exactly
the observations it affects.

Profiles export and import as files, so an organisation can distribute a calibrated instrument definition to
its staff.

### 2.3 Layered settings (FR-068)

Three scopes, resolving **run parameter → project → global → built-in default**.

- Global settings live in `QgsSettings` under a `GeoComp/` prefix.
- Project settings live in the project store (GeoPackage or PostGIS) so they travel with the data — a project
  handed to a colleague carries the instrument constants it was computed with.
- Every settings widget shows which scope the effective value came from, and offers "override for this
  project".
- The effective value and its origin are recorded in provenance (FR-134), which is what makes a result
  explicable months later.

---

## 3. Basic and Advanced modes (FR-070, FR-071)

Set in Interface, switchable without restart.

| | Basic | Advanced |
|---|---|---|
| Parameters shown | The reduced set, with defaults | Everything |
| Engine configuration | Generated | Generated, inspectable, editable; or user-supplied (FR-325) |
| Pipeline stages | Chosen automatically | Individually controllable |
| Approximate uncertainty paths | Applied where needed, labelled | Selectable per operation |
| Automatic outlier rejection | Not offered | Offered, with an explicit warning ([`06-adjustment-core.md`](./06-adjustment-core.md) §4.2) |

**FR-071 is the rule that makes this safe:** a parameter hidden in Basic mode uses exactly the value it would
have had as the Advanced default. Switching modes without changing anything must not change results — a
Basic-mode result must be defensible, not a cheaper approximation.

See [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md) §4 for the parameter-gating mechanism.

---

## 4. Results panel

A dockable panel showing the current project's solutions: run history with status, statistics summaries,
per-observation results with sorting and filtering, and links from a table row to the corresponding map
feature. Selecting a station shows its time series when the project has multiple epochs (FR-838).

This is where the teaching value concentrates: the statistics are *visible*, next to the map, rather than
buried in an output file.

---

## 5. UI conventions

- **Nothing is silently defaulted where it matters.** Where GeoComp picks a value the user did not supply,
  the choice is shown, not hidden — particularly for uncertainties, frames and epochs.
- **Every statistic is shown with its critical value, confidence level and decision**
  ([`06-adjustment-core.md`](./06-adjustment-core.md) §7).
- **Approximate results are visibly marked** wherever displayed (FR-203).
- **Angles display in the configured format** (DMS or decimal degrees) and are stored in radians.
- **Errors follow NFR-006:** what failed, why, what to do.
- **Long operations show determinate progress and can be cancelled** (FR-008).

---

## 6. Acceptance criteria

1. The GeoComp menu appears on the QGIS menu bar with the seven entries in the specified order — the
   figure's five technique submenus, then Analysis — and the separator before Global Settings.
2. Every submenu item launches an algorithm; a test asserts that the set of menu items and the set of
   registered algorithms correspond, with no orphan on either side (FR-005).
3. Unloading the plugin removes the menu, toolbar, provider and panels; reloading produces no duplicates.
4. Global Settings shows the specified sections with the specified contents.
5. An instrument profile can be created, used in a computation, exported, imported into a fresh profile, and
   produces identical results.
6. A setting overridden at project scope takes effect, and the UI shows the override and its origin.
7. Running an algorithm in Basic mode and in Advanced mode with defaults produces identical numeric results
   (FR-071), asserted by a test over every algorithm.
8. No user-facing string in this module bypasses the translation layer (FR-091), asserted by the i18n check
   in [`20-testing-and-validation.md`](./20-testing-and-validation.md).
