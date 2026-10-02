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
 ├── Project              ▸     (added in phase P5 — see §1.1)
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

**Project** *(added in P5)* → Export solution tables · Adjustment report · Save to project store · Export
project to PostGIS · Import project from PostGIS · Add base map · Create print layout · GeoComp system report ·
Install tutorial dataset. *Create print layout* joined in P12b ([`19`](./19-visualization.md) §6).

> **P11 added the two mode switches** of [`17`](./17-persistence-and-interoperability.md) §4, beside the store
> they move a project into and out of, and gave *Save to project store* a database mode: a PostgreSQL connection
> saved in QGIS and a schema, instead of a GeoPackage. The connection is chosen from QGIS's own list, so its
> login stays QGIS's (NFR-010).

> **Why an eighth entry.** Six algorithms had accumulated with no menu home: P0's system report and tutorial
> dataset, and P5's export, report, store and base map. Each was individually defensible as toolbox-only, and
> `tests/test_registry.py` was right to fail when the sixth arrived — **six exceptions are not exceptions,
> they are a category**, and the honest answer to a category is an entry rather than a longer list of reasons
> it does not need one.
>
> They share a description that is not a stretch: *operations on a project's results rather than on one
> technique's observations.* Exporting, reporting and storing a solution are identical whether it came from a
> total station, a level, or P6's DynAdjust; a base map is context for any of them; the system report and the
> tutorial dataset are the project's own housekeeping. Filing any under a technique would say something
> false, and repeating them under all five would break the one-item-per-algorithm correspondence ADR-0005
> rests on — the same argument that produced Analysis in P2.
>
> Discoverability is the other half of it. A user who has just adjusted a network wants the report; leaving
> it reachable only from the Processing toolbox is a worse menu, not a purer one, in exactly the way this
> section already says of *Import field book*.

**GNSS** → Absolute (Static · Kinematic) · Relative (Static · Kinematic) · Scan sessions · Download products ·
Batch processing · Build baselines · Compare configurations.
See [`11-module-gnss.md`](./11-module-gnss.md).

> **Built in P7c as eight of the nine, and the ninth in P10c.** Download products waited on FR-352, which
> moved to P10 when the egress check found every major archive unreachable, and within P10 to **P10c**
> (maintainer's decision, 28 September 2026); until then a menu entry for it would have pointed at nothing,
> which §1.2 forbids outright. It arrived with the capability, after *Scan sessions*.
>
> **GNSS is the only group with a second level**, and the exception is narrow and enforced. Its four modes are
> two branches of two, and flattening them would give four entries distinguished pairwise by their first word
> — *Absolute static*, *Absolute kinematic*, *Relative static*, *Relative kinematic* — where the specification
> and the proposal's own figure both draw a tree. `geocomp/registry.py` names the permitted set in
> `NESTING_MENUS`, raises at import for a submenu declared under any other group, and `tests/test_registry.py`
> holds that set to one entry. A one-level menu stops being one by the second exception, not the first, so the
> guard is on the mechanism rather than on anyone's memory.

**Gravimetry** → Pre-processing · Gravimetric network adjustment.
See [`12-module-gravimetry.md`](./12-module-gravimetry.md).

**Integration** → GNSS and Total Station · Total Station and Level · GNSS and Level · Multiple.
See [`13-module-integration.md`](./13-module-integration.md). Populated in P9b; the items read, in the
sentence case every other entry uses, *GNSS and total station*, *Total station and level*, *GNSS and level*
and *Multiple techniques* — the last because "Multiple" alone names nothing.

**Analysis** → Inspect network · Pre-analyse network design · Adjust network · the DynAdjust pair ·
Compare two epochs · Time series and velocities · Monitoring report. The last three joined in P10b; in the
Processing toolbox they form the *Monitoring* group ([`16`](./16-processing-provider.md) §2).
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
| Comparative GNSS configuration (FR-359) | Runs *n* configurations and shows a side-by-side comparison. **Not built.** P7c ships `geocomp:gnss_compare_configurations` alone: ADR-0005 makes the algorithm the capability, and the dialog will hand it the same parameters |
| Multi-epoch comparison (FR-831) | Needs to display compatibility findings before the user commits. **Built in P10b** (`gui/compare_dialog.py`): it runs the algorithm's own `compare` on the two files chosen, lists the frames, transformations, findings and the independence assumption, or the refusal, and offers OK only for a comparable pair |
| Monitoring time series (FR-838) | An interactive panel, not a one-shot run. **Built in P10b as a dock panel rather than a dialog** (`gui/time_series_panel.py`, [`19`](./19-visualization.md) §5): the algorithm produces the series, and its velocity layer brings the panel up when it is added to the project, so the menu item stays the algorithm and no entry is needed in `CUSTOM_DIALOGS` |

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
│ Base maps        │                                              │
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

**What P7c declared, and what it deliberately did not.** Nine settings: the product directory, the ANTEX
file, the reference station database, and six processing defaults (elevation mask, ephemeris source,
ionosphere and troposphere models, ambiguity ratio threshold, and whether to keep only the independent
baseline subset). **All nine are read**, which is the point — see §2.3 for the 41 that were not until P12a,
and the rule that a newly declared setting must have a consumer.

Two of the row's items were absent in P7c, and not by oversight. *Preferred download servers and their
priority* belongs to FR-352, and *credential references* to FR-353 and NFR-010; all three moved to P10 with
the download capability itself, because a settings control for a server list that nothing downloads from
would be exactly the defect §2.3 describes. **P10c declared them with their consumer**, four settings, all
read by `algorithms/gnss/common.py`:

| Setting | Default | Meaning |
|---|---|---|
| `gnss.product_services` | `noaa-ncn` | Download services by id, in priority order; empty means GeoComp never downloads |
| `gnss.service_definitions` | empty | A JSON file defining further services ([`08`](./08-engine-rtklib.md) §5) |
| `gnss.product_cache` | empty | Where products are kept; empty is `geocomp/products` in the QGIS profile folder |
| `gnss.product_fallback` | off | Whether a missing final orbit may be replaced by the rapid one, recorded when it is |

**The credential references are not settings.** A service that needs a login names a QGIS authentication
configuration by its id in the services file; the credential itself stays in QGIS's encrypted store. There is
no setting a password could be typed into, which is the only arrangement that makes NFR-010 true by
construction rather than by care.

Wiring the ANTEX file was where the distinction between naming a setting and honouring one showed up in
practice: supplying `file-rcvantfile` without also setting `pos1-posopt2` loads a calibration model
`rnx2rtkp` then ignores, which is the quietest possible way to believe a run is calibrated. All three keys
are written together.
| **Gravimeter** | Gravimeter profiles: calibration table and factor, nominal precision, drift characteristics. Tidal model. Display unit (mGal / µGal) | FR-061 |

**What P8b declared.** Six settings — tide model, gravimetric factor, drift treatment, drift degree, a reading
precision floor (the section's default weighting) and the display unit — **all six read by the computation**,
each as the default of the algorithm parameter of the same meaning
([`12-module-gravimetry.md`](./12-module-gravimetry.md) §6 has the table). Gravimeter profiles are library
documents, like level profiles, not settings. Two of the six are numbers, which the window could not edit
until P12a: see §2.3.
| **Stochastic model** | Default weights per observation type; outlier detection parameters (α, β); variance component estimation defaults | FR-064 |
| **Reference systems** | Preferred CRS; default reference epoch; transformation parameters and preferred transformation paths; default geoid model | FR-065 |
| **Paths & engines** | DynAdjust and RTKLIB executable locations, engine installation and update, working directories, report templates | FR-066, FR-300 |
| **Base maps** | Whether to offer a base map with result layers; which service to offer; the catalogue file; whether to reuse one already in the project | FR-167 |
| **Interface** | Language; usage mode (Basic / Advanced); units of measure; angle display format; decimal places; log verbosity | FR-067, FR-092 |

**Amendment (P5): a ninth section, Base maps.** `tex §Painel de Configuração Global` item 6 lists eight, and
this table followed it. FR-167 asks for base map integration with "a configurable list with sensible
defaults" ([`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) §5.6), which
is configuration and belongs in the panel; none of the eight is where a user would look for it — it is not
equipment, not stochastic, not a reference system, not a path, and burying it under Interface would make
"Interface" mean "everything left over". It sits after Paths & engines and before Interface, among the
cross-cutting sections. FR-167 stays owned by P5; this is an amendment to the section list, not a transfer.

**What P5 declared, and why every default is empty.** Reference systems carries preferred CRS, default
epoch, transformation choice and preferred paths, transformation grid directory, default geoid model and its
stated accuracy (FR-065). Every one of them defaults to empty or to "ask", and that is the design rather
than an omission: GeoComp does not assume a CRS and refuses operations needing an epoch it was not given
(FR-105), so a settings module shipping a plausible default for either would make the plugin assume exactly
what the rest of it refuses. What the settings do is let a user state theirs once, and record in provenance
that they did.

**Amendment (P12a).** The transformation choice, preferred paths and grid directory are removed: GeoComp
never asks PROJ for an operation, so they had nothing to govern (§2.3). The default epoch is a decimal year
with 0 for none stated, and the other three — CRS, geoid model, geoid accuracy — are the defaults of the
parameters they name.

The geoid model's **accuracy** is a setting because no grid format carries it and
`geocomp.core.geoid` will not build a model without one (FR-204) — the figure that most often limits a
combined height solution is the user's to state, from the model's own documentation, not the reader's to
invent.

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

#### What was wired, and what was not — as found by the pre-P7 review

The *mechanism* above worked and was tested: declare a `SettingDef` and a labelled control appears, resolving
correctly through run, project and global scope. What was not generated is the **use** of the resolved value,
and the review found **36 of 47 declared settings read by nothing at all**. A user could open Global Settings,
change the angle format, the default meteorology, the levelling class tolerances or the default observation
weights, have the value stored and resolved and shown back correctly — and change no computation. The
Processing algorithms exposed the same quantities as run parameters with **hard-coded defaults**, which is why
nothing looked wrong at the default: the numbers agreed, and only a user who changed one discovered they did
not. It is the same shape as the defect P4 recorded one level up, when the dialog rendered raw dotted keys for
all seventeen settings P3 had declared — generated from the declarations, the labels were not, and nobody
looked.

The pre-P7 review also found, in P8b, that **the window edited only choices, switches and whole numbers**, and
showed every other setting as *(not editable in this version)*: by P11 that was 40 of 66 — every
floating-point setting (27), every path (5), string (4) and directory (3), and the CRS.

#### Resolved in P12a

**A parameter's default is its setting.** Each algorithm declares the parameter with
`defaultValue=configured("section.key")` (`geocomp/algorithms/defaults.py`), read when the algorithm is
instantiated — which Processing does for every dialog and every run — through the run, project and global
scopes. There is one value, not a setting and a literal that happen to agree. So changing a setting changes
what a run that does not override it computes, and a parameter hidden in Basic mode runs at the setting
exactly as Advanced mode left untouched would (FR-071, §3). The setting-to-parameter table is
`tests/qgis/test_settings_reach_the_computation.py`'s `WIRING`, which asserts every row: a value set for the
run becomes that parameter's default, in every algorithm the setting governs.

**Five more than the review counted.** `tests/structural/test_settings_are_honoured.py` asked whether a key
appeared *anywhere* in a module, and five passed on prose alone: `stochastic.outlier_alpha` named in a comment
about data snooping, both face tolerances in a note that a core constant "mirrors" them, `level.weighting` in
a docstring, `basemaps.reuse_existing_layer` likewise. It now reads string literals in code only — a key in a
comment is a sentence about a setting, not a use of one — so the true count at the start of P12a was **41 of
66**. Of those:

| | Settings | How |
|---|---|---|
| **Wired to parameter defaults** | 29 | Meteorology and its uncertainties, refraction and its uncertainty, the three traverse settings and both face tolerances (total station); weighting, *k*, the three sight limits and the reciprocal inflation (levelling); the three default observation sigmas, α, β and the confidence level; the preferred CRS, the default epoch, the geoid model and its accuracy; reusing a base map |
| **Wired to a behaviour** | 4 | The atmospheric model, through the generic instrument profile; the **tolerance gate** and the **orthometric correction** in *Levelling network adjustment* ([`10`](./10-module-levelling.md) §3, §5); the **base-map offer** ([`17`](./17-persistence-and-interoperability.md) §5.6) |
| **Wired to the reports** | 4 | Angle format and places, coordinate places, distance unit ([`19`](./19-visualization.md) §7.4) |
| **Removed** | 4 | Below |

`NOT_YET_HONOURED` is empty, and stays the rule: a setting declared without a consumer fails the build.

**Four settings removed, because nothing can consume them.** `reference_systems.transformation_choice`,
`preferred_transformations` and `transformation_grid_directory` govern how PROJ picks an operation between two
CRSs, and GeoComp never asks PROJ for one: its only transformation is between ITRF realisations, by the
published fourteen-parameter sets in `core/geodesy/frames.py`, and a change of CRS is QGIS's, under QGIS's own
transformation settings. `stochastic.default_sigma_height_difference` has no importer that reads a bare height
difference to apply it to. Three controls with nothing behind them are the defect this section records, not a
feature. FR-065's *transformation parameters* clause is therefore met by the frame transformation's own
published parameters, which are data with provenance rather than settings — see the traceability matrix.

**Four declarations changed to say what is computed.**

- `total_station.traverse_adjustment` offered *least squares* as its default, which the Traverse algorithm
  cannot do — least squares is *Classical network* on the same observations ([`09`](./09-module-total-station.md)
  §4.1). Its choices are now compass (the default the algorithm always used), transit and *none* (report the
  misclosure only).
- `total_station.traverse_angular_tolerance_per_station` said 1.45×10⁻⁴ rad, about 29.9″, where the algorithm's
  own default was 30″. It is now exactly 30″ in radians.
- `total_station.face_distance_tolerance` said 0.005 m — the core's last resort for an instrument with no EDM
  specification — where Preprocess's parameter defaulted to 0, *from the instrument*. Wired, the setting says
  what the parameter did: 0.
- `reference_systems.default_epoch` was free text, which nothing could validate. It is a decimal year, with 0
  for *none stated*, the convention the DynAdjust algorithm's epoch already used. Unstated, each algorithm keeps
  the epoch it always defaulted to, so an unconfigured installation computes what it did; the Integration
  algorithms keep taking their inputs' epoch.

**Every setting is editable.** The window builds an editor for every type: a number box for floating-point
settings that takes the user's locale and scientific notation, refuses a value outside the declared range by
naming it, and writes back exactly what it was given — a default shown to twelve digits and read back would
have stored an override on every press of OK; QGIS's own file and directory pickers for paths; QGIS's CRS
selector, with *not set* as a choice because it is the default. `tests/qgis/test_settings_dialog.py`.

**Not done in P12a.** The window still writes global scope only; *override for this project* (the third
bullet above) has its mechanism in the settings service and no control in the window. Number formatting per
locale (FR-094) was not addressed in P12a; it arrived in P12c ([`18`](./18-i18n-and-profiles.md) §5).

**Override for this project (P12c).** Each row whose setting a project may vary has a *this project* box,
checked when the effective value is the project's.
- **Checked:** OK saves the value in the project, and the global value is left alone.
- **Unchecked:** the editor shows the value that applies without the override, global or default. OK clears
  the project's override and saves the row globally.

The label beside each row names the scope its value comes from. Settings that must not vary by project offer
no box.

**Found on the way.** Before this, the window loaded a project's override as the row's value, and OK wrote
every row globally. Pressing OK in one project therefore made its override the global value for every other
project. `tests/qgis/test_settings_dialog.py` holds both.

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

**As built (P12b)** — `gui/results_panel.py`, reading through `core/visualization/results.py`, which is
QGIS-free and tested without QGIS. Docked on the right and hidden at start; Plugins ▸ GeoComp ▸ *Results
panel* shows it. Each clause of the paragraph above is a test in `tests/qgis/test_results_panel.py`.

- **Run history.** One row per solution: id, when, the algorithm, the global test's *passed* or *FAILED*,
  the variance factor, degrees of freedom, and the counts of blunder candidates and uncheckable observations.
  A superseded solution says so. Runs arrive three ways: an adjustment's result layers, when they are added to
  the project, because each carries the path of the solution document it came from
  (`SOLUTION_PROPERTY`, `geocomp/solution`); *Open solution…*; and *Open project store…*, which lists every
  solution in a GeoPackage store. The same run twice is one row. An unreadable file is said in the panel's
  status line, not listed.
- **Statistics.** Every quantity in `Statistics`, in reading order, each with its critical values and
  confidence (§5); what was not computed is shown as such, not left out. An approximate solution says so in the
  panel's status line (FR-203).
- **Observations.** Residual, w, redundancy, MDB, external reliability and the decision — *passes the
  w-test*, *blunder candidate*, *uncheckable*, *not tested*. Filters: all, blunder candidates, uncheckable,
  not tested, and an id search. Columns sort as numbers; an uncheckable MDB sorts as infinite, the largest
  there is, and a value nobody computed sorts last in either order.
- **To the map.** Selecting a row selects the feature with that id on the run's own result layer — matched by
  the result kind and the solution path, so the same id in another run's layer is left alone — and zooms to
  it. Selecting a station selects it on the stations layer and, when the time-series panel holds a series
  with that station, shows its series there (FR-838).
- **Stations.** Coordinates in the configured format (§7.4 of [`19`](./19-visualization.md)), standard
  deviations, positional uncertainty and the ellipse's semi-axes.

**Not built:** opening a PostGIS store in the panel — *Open project store…* takes a GeoPackage; a PostGIS
project's runs reach it through their layers or an exported solution. The observation table has no
observation-type column: the solution records results by id, and the type lives in the network document,
which the panel does not read.

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

1. The GeoComp menu appears on the QGIS menu bar with the eight entries in the specified order — the
   figure's five technique submenus, then Analysis and Project — and the separator before Global Settings.
   *(It said seven until P12c's audit, which found it had missed the Project entry FR-003 added in P5.)*
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
