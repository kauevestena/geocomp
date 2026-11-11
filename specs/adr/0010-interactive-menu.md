# ADR-0010 — The menu is interactive windows that run the algorithms

**Status:** Accepted
**Date:** 2026-11
**Supersedes:** [ADR-0005](./0005-menu-algorithm-parity.md) in part — its *launcher* half
**Requirements:** FR-005, FR-010…FR-017

## Context

Under ADR-0005 every item of the GeoComp menu opened the standard Processing dialog of one algorithm, and
every algorithm reads files: a field-book CSV, a readings document, a JSON of known stations. A surveyor
with a field book on paper had nothing to type into. The first thing every workflow asked of them was to
build a CSV in another program, in a layout they then mapped column by column — the manual handling the
research project set out to remove (`tex §Justificativa técnica`).

Brazilian land-surveying software — Posição is the one the maintainer named — is organised the other way:
*Caderneta* (field book), *Partidas* (starting data), *Calc. Poligonal*, *Calc. Irradiações*, *Croqui*, each a
form in which the observations are typed, angles in degrees-minutes-seconds, with the closure shown as the
book is filled. The pre-analysis simulator (FR-272) had already shown, inside GeoComp, that an interactive
window over the map is where a GIS earns its place.

The maintainer's decision (10 November 2026): **the top-bar menu becomes interactive, guided windows in which
observations are typed, while every Processing algorithm stays exactly as it is** and remains the route for
files — CSV, XLSX, RINEX, instrument exports — from the toolbox, the modeller, batch and PyQGIS.

## Options

**A. Windows with their own computation.** The window reduces the face pairs and walks the traverse itself.
Fast to show a closure; and it is option A of ADR-0005 again — two implementations that drift, with the
first sign a user getting a different misclosure from the menu and the toolbox. Rejected.

**B. Windows that run the registered algorithms.** A window writes what was typed as the very inputs an
algorithm reads, runs the unchanged algorithm in the background, and shows what it wrote. One
implementation. Instant feedback is limited to what the importer's own reader says of a row; every number
comes from an algorithm run.

**C. Keep the launchers; add a field-book editor beside them.** Least work, and the menu stays a list of
file dialogs with one exception — not what was asked.

## Decision

**Option B.** ADR-0005's first half stands: *every capability exists exactly once, as a Processing
algorithm.* Its second half — *the menu is a launcher of Processing dialogs* — is replaced:

1. **A menu item opens an interactive window.** Guided (numbered steps that unlock as the earlier ones are
   complete, any unlocked step revisitable), non-modal (the map stays usable, with a sketch on it), over a
   **job** — one shared, typed field book per technique, saved as a file.
2. **A window computes nothing.** It writes what was typed as an algorithm's inputs and runs registered
   algorithms, in order, each reading what the one before wrote. Each window declares in the registry the
   algorithms it runs, and the runner refuses any other; a structural test holds that no window module
   imports a computation.
3. **Typed data is Qt-free.** `geocomp/jobs/` holds the job file, the typed tables and the emission of
   algorithm inputs, under the same no-QGIS rule as `core/`. A typed total-station field book is emitted as
   rows under the importer's own field names with angles in radians, read by
   `geocomp:totalstation_import_fieldbook` through an identity mapping — so *typed equals imported* to the
   last bit, and is tested so.
4. **A window's options are its algorithm's parameters**, drawn by QGIS's own parameter widgets from the
   algorithm's definitions: the same labels and units, defaults (Global Settings), ranges and Basic/Advanced
   gating, translated once.
5. **File readers stay in the toolbox.** An algorithm whose purpose is a file the menu has no business
   typing is reached from the toolbox; FR-160's mapping preview stays reachable from Plugins ▸ GeoComp.
6. **The menu is rebuilt one group at a time** (ROADMAP P14). Until a group's windows exist, its items stay
   the launchers ADR-0005 made them; the registry calls them *legacy launchers*, and their set may only
   shrink.

## Consequences

- The menu and the toolbox cannot disagree: they run the same code on the same numbers. `tests/qgis/
  test_totalstation_windows.py` holds RD-01 typed and pre-processed in the windows equal, document for
  document, to the toolbox chain on its CSV.
- The menu's structure (FR-003) is unchanged: eight entries in the same order. What is under them changes.
- Every algorithm is still scriptable, chainable and batchable, and every window shows the equivalent
  toolbox run of what it did, so a user can move from one route to the other with what they learned.
- Instant feedback is bounded by option B. A window shows the importer's findings as a row is typed, and a
  closure only after the algorithms have run — a second or so after the typing stops, automatically. A
  number a window showed without running an algorithm would be the drift this ADR exists to prevent.
- The job file is the record and the results are not: everything in `<job>_results/` can be made again
  from the job, and a result made from an earlier state of the job is shown as out of date, never as current.
- A window is code that ADR-0005 did not have to maintain: a step list, a grid, a sketch. The framework
  (`gui/workbench/`) is written once and the windows are thin over it; a window that needs computation of
  its own has found a capability that belongs in `core/` and an algorithm.
- Custom dialogs (§1.2 of [`../15-ui-menu-and-settings.md`](../15-ui-menu-and-settings.md)) remain for the
  legacy launchers and the file route, and the windows absorb them as their groups are rebuilt.
