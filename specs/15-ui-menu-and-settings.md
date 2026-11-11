# 15 — UI: the GeoComp menu and Global Settings

**Status:** Draft
**Requirements covered:** FR-002…FR-007, FR-010…FR-017, FR-060…FR-071, FR-272.
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

**Total Station** → Field book · Generalised pre-processing · Traverse · Resection · Forward
intersection · Classical networks · Trigonometric levelling · 3D radiation.
See [`09-module-total-station.md`](./09-module-total-station.md).

> **Field book** is not in the proposal's list, which starts at pre-processing. Until P14a the item was
> *Import field book*, added because the list assumes the data is already in GeoComp and nothing else put
> it there. Since P14a it is the window in which the field book is **typed** (§7.2) — the first step of
> every Total Station window. Every item of the submenu is a window: four since P14a, the other four since
> P14b. Importing an instrument's *file* is the toolbox's *Import field book* (FR-015), also reachable with
> its mapping preview from Plugins ▸ GeoComp. The window keeps the algorithm's name, *Classical network*;
> the proposal's plural names the kind of computation.

**Level** → Import levelling field book · Equal sights · Equidistant sights · Extreme sights · Closures and
tolerances · Levelling network adjustment. *(Six as built in P4, rather than the proposal's four: import and
closures were implicit in the others and each produces a document the next step reads — see
[`10`](./10-module-levelling.md) §1.)*
See [`10-module-levelling.md`](./10-module-levelling.md).

**Project** *(added in P5)* → Export solution tables · Adjustment report · Save to project store · Export
project to PostGIS · Import project from PostGIS · Add base map · Create print layout · GeoComp system report ·
Install tutorial dataset · Install an engine · Package an engine problem. *Create print layout* joined in P12b
([`19`](./19-visualization.md) §6), *Install an engine* in P12c-6 ([`21`](./21-packaging-ci-release-licensing.md)
§4), *Package an engine problem* in P12c-48 ([`20`](./20-testing-and-validation.md) §8).

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

### 1.2 The menu opens windows that run the algorithms (FR-005, FR-011)

**Since P14a, a menu item opens an interactive window** in which observations are typed (§7), and a window
computes nothing: it runs registered Processing algorithms on what was typed and shows what they wrote
([`adr/0010-interactive-menu.md`](./adr/0010-interactive-menu.md), which supersedes the *launcher* half of
ADR-0005). The menu holds no second implementation. Consequences:

- The menu is **generated from the registry**: `geocomp/registry.py` declares the windows (`WINDOWS`), each
  with the algorithms it runs, and a menu item cannot point at nothing.
- A window may run **only** the algorithms its registry entry names; the runner refuses any other, and a
  structural test holds that no window imports a computation (§6, criterion 2).
- **The menu is rebuilt one group at a time** (ROADMAP P14). Until its group's windows exist, an item is a
  **legacy launcher**, as every item was under ADR-0005: it opens the standard Processing dialog of its
  algorithm. Their set may only shrink, and `tests/test_registry.py` pins it. After P14b it holds every item
  except the eight Total Station windows.
- Window names are translated once (`geocomp/gui/windows/labels.py`); a launcher's name is its algorithm's
  `displayName()`, as before (FR-090).
- A small, enumerated set of legacy launchers opens a custom dialog that collects parameters and then runs the
  same algorithm. The windows absorb them as their groups are rebuilt; the field-mapping preview stays, for
  the file route, under Plugins ▸ GeoComp:

| Custom dialog | Why the standard dialog is insufficient |
|---|---|
| Global Settings | Not an algorithm at all — it configures the others |
| Interactive pre-analysis (FR-272) | Design is edited on the canvas and re-evaluated in a loop. Arrives in P3, re-planned out of P2 — see [`ROADMAP.md`](./ROADMAP.md). The non-interactive route, `geocomp:analysis_network_preanalysis`, ships in P2 |
| Field mapping for import (FR-160) | Needs a preview of the source data to map columns against. **Since P14a reached from Plugins ▸ GeoComp ▸ *Import field book with mapping preview…***, the GeoComp menu's *Field book* being the window the book is typed in (FR-015) |
| Comparative GNSS configuration (FR-359) | Runs *n* configurations and shows a side-by-side comparison. **Not a dialog, since P12c-43**: the side by side is `geocomp:gnss_compare_configurations`'s HTML report, one column per configuration, which Processing's results viewer opens like every other report ([`11`](./11-module-gnss.md) §6). The parameters need nothing the standard dialog cannot show, so no entry is needed in `CUSTOM_DIALOGS` |
| Multi-epoch comparison (FR-831) | Needs to display compatibility findings before the user commits. **Built in P10b** (`gui/compare_dialog.py`): it runs the algorithm's own `compare` on the two files chosen, lists the frames, transformations, findings and the independence assumption, or the refusal, and offers OK only for a comparable pair |
| Monitoring time series (FR-838) | An interactive panel, not a one-shot run. **Built in P10b as a dock panel rather than a dialog** (`gui/time_series_panel.py`, [`19`](./19-visualization.md) §5): the algorithm produces the series, and its velocity layer brings the panel up when it is added to the project, so the menu item stays the algorithm and no entry is needed in `CUSTOM_DIALOGS` |

#### Algorithms with no menu item

Under ADR-0005 every algorithm had a menu item, and one without needed a recorded reason. **Since ADR-0010 an
algorithm without an item of its own is the rule**: the menu holds windows, and an algorithm is reached from
the menu by being **run by a window**. The parity test asks each algorithm for one of three things — a
window that runs it, a legacy launcher, or a reason recorded in `geocomp/registry.py`'s
`TOOLBOX_ONLY_JUSTIFICATIONS` — and fails on a reason left behind by a deleted algorithm.

`TOOLBOX_ONLY_JUSTIFICATIONS` is **empty**. It emptied in P5, when the Project entry gave its last members a
home, and it now holds the algorithms *no window runs either*: a reader of a file the menu has no business
typing (FR-015). P14a took one file reader out of the menu, *Import field book*, and it is not there, because
the Total Station windows read the typed book with it. Later stages may add some, each with its reason.

Note the asymmetry, which is deliberate: **every menu item must resolve to a registered window or
algorithm** with no exceptions, because a menu item pointing at nothing is a broken UI.

Recorded as [`adr/0005-menu-algorithm-parity.md`](./adr/0005-menu-algorithm-parity.md) and
[`adr/0010-interactive-menu.md`](./adr/0010-interactive-menu.md).

### 1.3 Toolbar (FR-007)

A GeoComp toolbar with a small set of frequent actions — open/create project, run last algorithm, network
inspection, adjust, and the results panel — hideable through the standard QGIS toolbar controls.

**As built (P12c-13).** Until P12c-13 the toolbar held one action, Global Settings. It now holds *Inspect
network*, *Adjust network*, *Save to project store*, *Run the last GeoComp algorithm again*, the results panel
and Global Settings, hidden by `interface.show_toolbar` as well as by QGIS's own controls. Each algorithm
opens the same dialog its menu item does. *Run again* repeats the last algorithm opened from the menu or the
toolbar — or, since P14a, opens again the last window opened from the menu — and is disabled until there is
one. **Open/create project** is *Save to project store*, which creates
the store when it does not exist. GeoComp has no *open*: a store is a GeoPackage or a PostGIS schema, and QGIS
opens either as it opens any other (`tests/qgis/test_plugin_lifecycle.py::TestTheToolbar`).

### 1.4 Unload (FR-006)

`unload()` removes the menu, the toolbar, the provider, every action, every dock panel and every signal
connection, and since P14a closes every open window first — each giving the map canvas back its tool and
taking its sketch off the map. Reload during development must leave no duplicate menu and no window behind —
a specific, tested condition.

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
| **Total Station** | Instrument profile library (§2.2): vertical index correction, collimation, EDM additive constant and scale, cyclic error, nominal precisions for direction / zenith angle / distance. Reflector profiles with prism constants. Atmospheric model and default temperature, pressure, humidity. Refraction coefficient. Closure tolerances by traverse class | FR-061, FR-062 |
| **Level** | Level profile library (§2.2). Default weighting (length or setups). Permissible-misclosure coefficient *k*. Sight-length, per-setup and per-line imbalance limits. Reciprocal-sight variance inflation. Orthometric corrections on or off. Whether a line that failed its tolerance may be adjusted | FR-061, FR-503, FR-504 |

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
| **Gravimeter** | Gravimeter profile library (§2.2): calibration table and factor, nominal precision, drift characteristics. Tidal model. Display unit (mGal / µGal) | FR-061 |

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

**Amendment (P12c-6): Paths & engines.** Declared in P0 and empty until P12c-6, while the window said its
settings were "added by the development phase that implements this equipment type". It now holds the
DynAdjust directory and the RTKLIB `rnx2rtkp` program, **global scope only** — where a program is installed
is a fact about a machine, and a configured path is never fallen back from, so one carried in a project to
another machine would refuse to run there. Empty, each engine is GeoComp's own installation, then the system
path. Below them the page states what each engine is and where it was found, and offers *Install
DynAdjust…*, which opens *Install an engine* ([`21`](./21-packaging-ci-release-licensing.md) §4). Working
directories and report templates, the rest of FR-066's list, are not settings: each algorithm takes its
working folder and its outputs as parameters, and the report its template (*Report template*,
[`19`](./19-visualization.md) §7.3).

**Amendment (P12c-46): the rest of FR-066's list.** Two more paths, global for the reason the engines are:
*Working directory for the engines' files*, under which every engine run makes its working folder -- DynAdjust,
a stopped DynAdjust job, a combination sent to DynAdjust, RTKLIB's batch and comparison runs, and its single
run when the solution is not saved (a saved one keeps its working folder beside it, as before) -- and
*Report templates folder*, from which every template-driven report takes its template: the adjustment report,
the combination's, the monitoring report, and the comparison's and the time series' own. Each is the default a
run falls back to, not a replacement for its parameter: a folder or template the run names still wins. Empty,
they are the system's temporary directory and the shipped templates, as before. A working directory that
cannot be written in is refused by name, saying where it is set; a templates folder without the template a
report needs falls back to the shipped one (`tests/qgis/test_paths_settings.py`).

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

**As built (P12c-16).** Until P12c-16 a profile was edited as a JSON document, and no window managed one.
*Instrument profiles…*, on the Total Station, Level and Gravimeter pages of Global Settings, now opens
`gui/profiles_dialog.py` on that technique's tab:

- **One library, one file.** The window opens, saves and saves-as the same profile library file an
  algorithm's *Instrument profiles* input reads. There is no second store of profiles that a run could fail
  to see. It has one tab for each kind: total stations, reflectors, levels, levelling classes and gravimeters.
- **Add, edit, duplicate, delete, default.** An id is fixed once given, because observations reference it
  (§2.2 above): a profile is renamed by duplicating it. The first profile of a kind becomes its default, as
  the library's own `add_instrument` makes it, so a library built in the window serves a run that names no
  instrument. Deleting the default profile clears the default rather than leaving it naming nothing.
- **Shown in a surveyor's units, stored in the profile's.** An angle is shown in the interface's small-angle
  unit (″, cc or µrad, as *Angle format* is set), a prism or EDM constant in millimetres, an EDM's
  proportional term in ppm, a levelling σ in mm/√km and a gravimeter's in µGal. The file keeps radians,
  metres and ratios. A decimal comma is accepted. Constants are shown as a value and its σ.
- **Refused in the profile's own words.** An edit is applied to the profile's serialised form and read back
  through its `from_dict`. So a value the profile refuses, such as a negative σ or a counter-reading
  gravimeter without its table, is refused with the same message as a file would be, and nothing is changed.
- **Import adds and never replaces.** Importing another library adds the profiles whose ids are new and keeps
  this library's where an id is already used, and it lists both. Export writes only the profiles selected.
- **Unsaved changes are asked about** before *New*, *Open* or closing discards them.

What the form does not edit it keeps. A gravimeter's counter-to-milligal table is the main case: it is long
and is copied from the manufacturer's sheet, so it is imported with the profile and is not typed in.
The operations and the units are `geocomp/core/instruments/editing.py`, tested without QGIS in
`tests/test_profile_editing.py`. The window is tested in `tests/qgis/test_profiles_dialog.py`.

**As built (P12c-17): the library a run reads.** Until P12c-17 Global Settings did not remember a library.
Each run was given one through its *Instrument profiles* input, or used the built-in default, and the window
opened empty. Now each technique's page names its library: *Instrument profile library*
(`total_station.profile_library`), *Level profile library* (`level.profile_library`) and *Gravimeter
profile library* (`gravimeter.profile_library`).

- **The default of every *Instrument profiles* input.** A run given no library reads the one its technique
  names, through the run, project and global scopes like any setting (§2.3). This applies to *Import field
  book* and *Generalised pre-processing* for the total station, to *Import levelling field book*, *Equal
  sights* and *Extreme sights* for levelling, and to gravimetry's *Pre-processing (scale, tide, drift)*. A run that names its own library still reads that
  one. Empty, the default, leaves every run as it was. The rows are in
  `tests/qgis/test_settings_reach_the_computation.py`'s `WIRING`.
- **One per technique, not one for all.** A department may keep one file for everything, and then names it
  three times. One setting for all three would make a library holding only total stations the levelling
  default, and stop a levelling run that worked without one. Each setting is read only by its own
  technique's runs, which find what they need in it or are refused as they would be had the file been given
  by hand.
- **The window opens the library the page names**, as the page shows it, before OK. A library named but not
  yet written is started empty there, and *Save* writes it. A library saved from the window while the page
  names none is entered on the page, where OK keeps it and Cancel drops it. The window alone changes no
  setting.
- **A project can name its own**, so a project handed to a colleague reads the constants it was computed
  with, as §2.3 asks.

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

  **Since P12c an unstated epoch is no longer assumed silently** (FR-105). The three network adjustments
  (*Network adjustment*, *Classical network*, *Levelling network*) default their epoch to the setting, 0 when
  none is stated, as DynAdjust's always did.
  - **Unstated**, a run takes its network's own epoch.
  - **Where the network states none either**, the old default still applies, so a solution still carries an
    epoch, as the model requires: 2000.0, or 2026.0 for levelling.
  - **Such an epoch is marked.** The provenance records it as `epoch_origin: assumed`, beside `stated` and
    `network`. The run warns, the adjustment report writes *assumed* beside it, and a comparison of epochs
    refuses it (`monitoring_solution_epoch_assumed`): a convention is not when anything was measured.
  - `algorithms/defaults.run_epoch` decides, and `tests/qgis/test_assumed_epoch.py` holds all three origins.

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

**As built (P12c-13).** Basic hides the advanced parameters (QGIS's hidden flag) and Advanced shows them. A
hidden parameter keeps its default, and a script or a model may still set it. Until P12c-13 both modes flagged
the same parameters advanced and QGIS showed them in both, so the setting changed nothing a user could see. A
change of mode refreshes the provider, so it takes effect without a restart.

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
2. Every submenu item opens a registered window or launches a registered algorithm, and every algorithm is
   run by a window, has a launcher, or records why it has neither; a window runs only the algorithms it
   declares and imports no computation (FR-005, FR-011).
3. Unloading the plugin removes the menu, toolbar, provider and panels; reloading produces no duplicates.
4. Global Settings shows the specified sections with the specified contents.
5. An instrument profile can be created, used in a computation, exported, imported into a fresh profile, and
   produces identical results.
6. A setting overridden at project scope takes effect, and the UI shows the override and its origin.
7. Running an algorithm in Basic mode and in Advanced mode with defaults produces identical numeric results
   (FR-071), asserted by a test over every algorithm.
8. No user-facing string in this module bypasses the translation layer (FR-091), asserted by the i18n check
   in [`20-testing-and-validation.md`](./20-testing-and-validation.md).
9. A window is not modal; its steps unlock in order and a locked one cannot be gone to; closing it gives the
   map canvas back its tool and removes its sketch (FR-010).
10. A field book typed in a window and computed there gives what the toolbox gives on the same book as a
    file: RD-01's reductions document to the last bit, with both of its known defects (FR-011).
11. A typed cell is kept as typed; one that cannot be read in the job's convention is marked and says why;
    a row the importer rejects is named by the grid's row number (FR-012).
12. A saved job reopens with its tables, conventions, options and results; a result made from an earlier state
    of the job is shown out of date; the open project remembers the job (FR-013).
13. A block pasted from a spreadsheet fills the grid, a readings document from the toolbox opens into it,
    and a point clicked on the map fills a coordinate (FR-014).
14. A window's options carry the algorithm's own labels and defaults, a changed Global Setting changes the
    default, and Basic mode hides what the algorithm hides (FR-016).

---

## 7. Interactive windows (FR-010…FR-017)

Added in P14a ([`adr/0010-interactive-menu.md`](./adr/0010-interactive-menu.md)). Built so far: the eight
Total Station windows of §7.2, four in P14a and four in P14b. The other groups follow in ROADMAP P14c–P14h.

### 7.1 Anatomy of a window (FR-010)

```text
┌ Traverse — Praça da Sé * ───────────────────────────────────────────────────────┐
│ Praça da Sé * — /surveys/praca.gcjob        [New job] [Open job…] [Save] [Save as…] │
├──────────────────────┬──────────────────────────────────────────────────────────┤
│ 1. Route  ✓          │ Starting data                                            │
│ 2. Starting data     │ ┌ the algorithm's own parameters, its labels and units ┐ │
│ 3. Options           │ │ Start easting (m)   [ 1000.0000 ]                    │ │
│ 4. Calculate         │ │ Start northing (m)  [ 5000.0000 ]  [Pick on the map] │ │
│ 5. Results           │ └───────────────────────────────────────────────────────┘ │
│                      │ ✖ A connected traverse arrives at a known point. Give …  │
├──────────────────────┴──────────────────────────────────────────────────────────┤
│                                                         [Back] [Next] [Close]   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

- **Not modal.** The map stays usable beside it; a coordinate can be picked on it and a sketch is drawn on
  it. Closing the window gives the canvas back its previous map tool and removes everything it drew.
- **The job bar** names the job, marks unsaved changes with `*`, and offers New, Open, Save and Save as.
  Closing the last open window of a technique asks about unsaved changes.
- **The steps** are numbered. A step is *locked* until the ones before it are complete, *ready*, *done* (✓),
  or *out of date* (↻) when the job changed since its result was made; any unlocked step can be gone back to.
- **The strip** beneath the page lists what is wrong with what is typed — each cell that cannot be read and
  each finding of the importer's reader, by the grid's row number — and choosing a line goes to its cell.
- A computation window whose field book cannot be computed from says so in a **banner** with a button that
  opens *Field book*: the book is put right where it is typed.
- Every computation window ends with **Calculate** and **Results** (§7.6).

### 7.2 The Total Station windows

| Window | Steps | Runs |
|---|---|---|
| **Field book** | Job and instrument (name, CRS or a local plane, angle convention, zenith or vertical angle, profile library, default precisions) → Field book (the grid) → Check → Report | `totalstation_import_fieldbook` |
| **Generalised pre-processing** | Conditions and tolerances → Calculate → Results | the import, then `totalstation_preprocess` |
| **Traverse** | Route (stations in order, chosen from the book; initial backsight; kind) → Starting data (start E, N, azimuth; closing data for a connected traverse, shown only then; picked on the map) → Options (distribution, tolerances) → Calculate → Results (misclosures, coordinates, the traverse drawn; *Use as known stations*; *Add stations to the map*) | the import, the pre-processing, then `totalstation_traverse` |
| **3D radiation** | Known stations (typed, pasted, picked on the map, or from *Traverse*) → Orientations and heights → Calculate → Results (points with their standard deviations, rays drawn; *Add points to the map*) | the import, the pre-processing, then `totalstation_radiation` |
| **Resection** *(P14b)* | Occupied station (chosen from the book's stations, with the points it sighted; in Advanced mode an approximate position, typed or picked) → Known points (at least three the station sighted; no height needed) → Calculate → Results (E, N and their standard deviations, the setup's orientation, rays drawn; *Use as a known point*; *Add the station to the map*) | the import, the pre-processing, then `totalstation_resection` |
| **Forward intersection** *(P14b)* | Known stations (where the point was sighted from) → Sightings (the point's name; one azimuth per station, in the job's angle convention; the azimuth precision) → Calculate → Results (E, N, the error ellipse's axes, weak geometry, rays drawn; *Use as a known point*; *Add the point to the map*) | `totalstation_intersection` alone: the field book is not read |
| **Classical network** *(P14b)* | Approximate coordinates (the known points, heights included) → Datum (dimension; datum definition; the stations held, or those the datum is defined over, ticked among the network's) → Options (CRS — the job's by default —, reduction to the grid, confidence) → Calculate → Results (global test, variance factor, degrees of freedom, outlier candidates, the adjusted stations, the network drawn; *Add result layers to the map*; *Use as known points*) | the import, the pre-processing, then `totalstation_network` |
| **Trigonometric levelling** *(P14b)* | Mode and refraction (radial or leap-frog; the instrument height, hidden in leap-frog mode, and the target height; the refraction coefficient and its uncertainty; with which setups leap-frog will read) → Calculate → Results (the height differences and their standard deviations) | the import, the pre-processing, then `totalstation_trig_levelling` |

**The known points are one table** of the job, which *Traverse*, *Resection*, *Forward intersection* and
*Classical network* write into and every window reads: a station resected is a station radiated from. A
plane computation reads a point without a height; *3D radiation* and *Classical network* need one, and a
point written by a plane computation keeps a height typed for it or takes the algorithm's zero, which the
window's tooltip says to replace.

**Trigonometric levelling takes one instrument height and one target height** for the whole book, its two
parameters, and does not read the heights typed in the book's rows, though its help says it does where they
are given. The window says so beside the two values. Recorded as a defect of the algorithm, not changed:
ADR-0010 keeps every algorithm as it is.

**The field-book grid.** One row per pointing: station, instrument height, target, face (`PD`/`PI`, also
typed `1`/`2`, `F1`/`F2`, `FL`/`FR`, `CD`/`CI`), horizontal circle reading, vertical circle reading, slope distance,
target height, set, note. A station, an instrument height and a target height are carried into a new row
from the row above, as on paper; a station left blank is the station of the row above. A row holding only
what it carried, or only a note, is not a pointing. Enter moves along the row and then to the next one; a
spare row at the foot is always there to type into.

### 7.3 Computing (FR-011)

A window **declares its algorithms in the registry** and runs nothing else. What was typed is written as
the inputs the first algorithm reads — the field book as a CSV under the importer's own field names, angles
in radians with every digit, and the identity mapping that reads it — and each later algorithm reads what the
one before it wrote, exactly as a model chains them ([`16`](./16-processing-provider.md) §9). Each runs as
`QgsProcessingAlgRunnerTask`, off the GUI thread, after `checkParameterValues`; a failure is shown in the
algorithm's own words. A run writes in a folder of its own, which replaces the window's results only when
every step has succeeded: a run that fails leaves the last good result as it was. The run step shows the **equivalent toolbox run**: each algorithm with the parameters
it was given, as lines for the Python console.

Once calculated, a window **calculates again by itself** a little over a second after the job last changed,
unless the user turns that off. Until then the result is marked out of date. **A computation window does not
run on a book with a row the importer rejects**: the toolbox carries on past a bad record because a file is
what it is, but a typed row is one keystroke from being right, and a traverse computed around a missing leg
is not what anyone meant.

### 7.4 Typing conventions (FR-012)

The angle convention is the job's, chosen in *Field book*'s first step, *Job and instrument*, and shown in every angle column's
heading:

| Convention | Typed as | Notes |
|---|---|---|
| Degrees, minutes and seconds, separated (**default**) | `87 31 15`, `87-31-15`, `87°31'15"` | Only the last part may carry decimals |
| DDD.MMSS | `87.3115` | Read from its digits; as Posição and most Brazilian field software take angles |
| Decimal degrees | `87.520833` | |
| Gon | `97.245370` | |

**A convention is strict**: `87.3115` is an angle in three of the four and a different angle in each, so a
cell is read in the job's convention or marked, never guessed. Minutes or seconds of 60 or more are marked,
not carried. **Changing the convention does not rewrite what is typed**: the cells are read again in the new
one, and that step says so. The vertical circle may read zenith angles (90° level) or vertical angles
from the horizon (0° level), emitted as the zenith angle the importer takes.

**Numbers** take a decimal point or a decimal comma, never a thousands separator — the rule the importer
already rests on ([`18`](./18-i18n-and-profiles.md) §5). A cell holds the text typed, so a value typed to four
decimals is four decimals when the job is reopened.

### 7.5 The job file (FR-013)

`<name>.gcjob`, kind `geocomp.job` ([`17`](./17-persistence-and-interoperability.md) §5.7): the typed tables
cell for cell, the conventions, the CRS, each window's options and an index of its last results with a
fingerprint of the inputs that produced them. Results lie in `<name>_results/<window>/<step>/` beside the file
and can all be made again from it. The windows of one technique share one job; the open QGIS project records
where each technique's job is (relative to the project) and reopens it with the project, unless a job with
unsaved changes is open.

### 7.6 Entry routes and results (FR-014, FR-017)

- **Paste**: a block copied from a spreadsheet — rows on lines, cells between tabs — fills the grid from the
  current cell; the selection, or the whole grid, copies back as one. Every edit can be undone.
- **Open a toolbox document**: *Field book* opens the readings document the toolbox's *Import field book*
  wrote, angles written in the job's convention to 0.0001″. Its precisions are not carried: *Job and instrument*'s
  are used when the book is read again, and the window says so.
- **Pick on the map**: a click, snapped where the project's snapping says, fills a coordinate in the job's CRS.
- **Results**: the figures the algorithms returned, under the window's labels and in the display format; the
  report the last algorithm wrote, shown as it wrote it; *Copy table* (the algorithm's CSV, every digit);
  *Open report*; *Open results folder*; and the sketch — known points, computed points, a traverse's legs, a
  radiation's, resection's or intersection's rays, a network's observed lines — which *Add … to the map*
  turns into a labelled point layer the user owns.
- **Result layers** (P14b): *Classical network* writes the algorithm's six result layers (FR-905) beside its
  documents on every run, and *Add result layers to the map* adds those with features to a group of the
  project, styled as a toolbox run styles them, carrying the properties the results panel reads, and named
  with the exaggeration their geometry was drawn at (FR-901), read back from the features. Each is a copy in
  memory: the files are in the window's results folder, which the next calculation replaces.

### 7.7 Options (FR-016)

A window's options are drawn from its algorithm's parameter definitions: the algorithm's labels with their
units, its choices, its defaults — Global Settings, read when the window is opened — its ranges, and
Basic/Advanced gating. A value is stored in the job only while it differs from the default; set back, the
choice is the algorithm's again. A window may show a parameter Basic mode hides when it cannot be used
without it: *Traverse* shows the closing coordinates of a connected traverse.

The widgets are GeoComp's own: a number is typed into a text field and read as the grid reads one, with a
point or a comma and every digit kept, and one outside the parameter's range is marked and not used. P14a
first drew them with QGIS's `QgsProcessingGuiRegistry.createParameterWidgetWrapper`, which ended the process
with a trap on QGIS 4.2 for macOS, on the CI runner, while Linux and Windows were fine.

