# Changelog

Semantic versioning. Breaking changes to the storage schema, algorithm ids or public core interfaces are
major ([`specs/21-packaging-ci-release-licensing.md`](specs/21-packaging-ci-release-licensing.md) §6).

## [Unreleased]

### Phase P1 - Core domain and uncertainty

The types everything else is built from, and the property that defines this project: no geodetic value
without an uncertainty. Still no QGIS dependency anywhere in this layer, and still no external engine.

#### Added

- **`core/units.py`** - SI and radians internally; DMS, gon, feet and mGal converted at the boundary and
  never stored. Sexagesimal parsing for field-book layouts, and a circular mean, which is what makes a
  face-left/face-right reduction correct across the zero of the horizontal circle.
- **`core/uncertainty.py`** - `Quantity` (value, variance, unit, rigorous-or-approximate mode) with
  propagating arithmetic and unit checking, and `Covariance` (labelled, symmetry- and PSD-validated) with
  rigorous propagation `Sigma_out = A Sigma A^T` (FR-200 to FR-208).
- **The correlation guard.** A quantity drawn from a covariance is tagged with it, and combining two
  quantities carrying the same tag through scalar arithmetic raises. This turns the most dangerous silent
  error in the system - treating correlated inputs as independent - into a loud one. `.detached()` is the
  explicit, documented escape hatch.
- **`core/differentiation.py`** - complex-step and central-difference Jacobians. The complex step is exact
  to machine precision and is what every analytic Jacobian is verified against, because a sign error there
  produces a plausible-looking wrong uncertainty rather than an error.
- **`core/models/`** - Epoch, Position, Station, ConstraintSpec, Observation, Cluster, GnssSession, Network,
  Campaign, Project, Solution and Provenance, with the observation type registry and lossless JSON
  round-tripping (FR-100 to FR-107).
- **RD-02 reference cases**, each validated three ways: a hand-derived closed form, the module's first-order
  propagation, and a derivative-free Monte Carlo simulation.
- **Structural check for FR-200**: a new plain-float field on a model class fails the build until someone
  decides whether it is a measurement or a diagnostic.

#### Notes

- Constraints are per component, not per station, so the routine case of a benchmark fixed in height and
  free in plan is expressible.
- Gravity carries no DynAdjust measurement type in the registry, which is the concrete form of ADR-0002:
  a required menu group with no engine behind it.
- NumPy is a hard dependency from this phase (it ships with QGIS); SciPy remains optional, and CI tests the
  SciPy-absent path.


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
