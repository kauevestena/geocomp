# Changelog

Semantic versioning. Breaking changes to the storage schema, algorithm ids or public core interfaces are
major ([`specs/21-packaging-ci-release-licensing.md`](specs/21-packaging-ci-release-licensing.md) §6).

## [Unreleased]

## [0.1.0] — Phase P0, Foundations

The first phase of [`specs/ROADMAP.md`](specs/ROADMAP.md). The plugin installs, loads, shows its menu and
its Processing provider, reads its settings, logs, tests and packages. **Nothing computes yet** — P0's job is
that everything which will compute has somewhere to live and a way to be tested, translated and shipped.

### Added

- **Plugin lifecycle** — `classFactory`, `initGui` / `unload`, the GeoComp menu on the QGIS menu bar with the
  six specified entries, a toolbar, and an About dialog under Plugins (FR-001…FR-007).
- **Processing provider** `geocomp`, with algorithms declared in a single QGIS-free registry that the menu
  and the toolbox both read, so the two cannot drift apart (FR-030…FR-032, ADR-0005).
- **Pure-Python core** — the exception hierarchy with stable machine-readable codes, the cancellation and
  progress protocols, the setting declarations, and layered settings resolution. Imports and runs with no
  QGIS (NFR-002).
- **Layered settings** — `run → project → global → built-in default`, with the origin scope of every
  effective value recoverable and shown in the UI (FR-068).
- **Global Settings window** with a side menu by equipment type, its pages generated from the setting
  declarations so a setting cannot exist without a UI (FR-060, FR-067).
- **Trilingual infrastructure** wired from the first commit rather than retrofitted: `tr()` discipline,
  catalogue extraction with an AST fallback for environments without the Qt tools, and complete pt-BR and es
  catalogues (FR-090…FR-095).
- **`geocomp:project_system_report`** — reports versions, engine availability and every setting with its
  origin scope. Proves the registry → provider → menu path, and answers the first question of any support
  request.
- **Structural CI checks** — no QGIS in the core, i18n string discipline, menu/algorithm parity, requirement
  phase partition, spec link integrity, SPDX headers, version consistency, translation completeness.
- **Reproducible packaging** — `scripts/build.py` produces a byte-identical ZIP for a given commit.

### Notes

- Minimum QGIS is **4.0.0**; the 3.x series is deliberately not supported
  ([`specs/adr/0007-qgis-4-minimum.md`](specs/adr/0007-qgis-4-minimum.md)).
- Marked `experimental=True` in `metadata.txt` until a phase ships geodetic computation.
- DynAdjust and RTKLIB are not integrated yet: they arrive in P6 and P7. The system report says so rather
  than reporting them as missing.
