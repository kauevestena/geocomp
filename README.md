# GeoComp

A QGIS plugin and modular framework for pre-analysis, pre-processing, GNSS processing and adjustment of
geodetic networks — integrating conventional and GNSS observations in one environment, encapsulating
[DynAdjust](https://github.com/GeoscienceAustralia/DynAdjust) and
[RTKLIB](https://www.rtklib.com/)'s `rnx2rtkp`, with cartographic visualisation and optional spatial-database
storage.

GeoComp is a research project of the Departamento de Geomática, Setor de Ciências da Terra, Universidade
Federal do Paraná. Licence: **GPL-2.0-or-later** (see
[`specs/adr/0001-licensing.md`](specs/adr/0001-licensing.md)).

## Status

**Phase P3 — the first vertical slice.** The specification set is written, and implementation proceeds phase
by phase from [`specs/ROADMAP.md`](specs/ROADMAP.md). Built so far:

- **P0** — plugin skeleton, Processing provider, layered settings, logging, i18n in three languages, packaging
  and CI.
- **P1** — units, `Quantity` and `Covariance` with rigorous propagation, complex-step differentiation, and the
  domain model.
- **P2** — the least-squares core: observation equations with analytic Jacobians, normal equations, datum
  handling, the global test, data snooping, reliability and error ellipses, plus network design and
  inspection. No external engine, and no SciPy required for correctness.
- **P3** — the total-station chain: field-book import with saved mappings, face reduction and the instrument,
  atmospheric and EDM corrections, traverse, resection, intersection, trigonometric levelling, radiation, and
  classical network adjustment — eleven Processing algorithms, with styled result layers.

**Run it on real data in five minutes:** the toolbox algorithm *Install tutorial dataset* copies
[RD-01](geocomp/resources/datasets/rd01/README.md) — the author's own total-station triangle — somewhere
writable, with a tutorial that walks the whole chain. It contains two real errors, and that is the point: the
software catches both.

## Repository layout

| Path | Contents |
|---|---|
| [`specs/`](specs/) | **Start here.** The authoritative specification set, the roadmap, and the architecture decision records |
| [`geocomp/`](geocomp/) | The installable QGIS plugin package |
| [`tests/`](tests/) | Three test tiers: pure Python, engine-dependent, and QGIS-dependent |
| [`research_project/`](research_project/) | The research proposal (LaTeX) — the **primary source** for every requirement |
| [`topo_test/`](topo_test/) | Total-station prototype and field data; adopted as reference dataset RD-01 |

## Where to start

| If you want to… | Read |
|---|---|
| Understand what GeoComp is and who it's for | [`specs/01-vision-and-scope.md`](specs/01-vision-and-scope.md) |
| See the full requirement list | [`specs/02-requirements.md`](specs/02-requirements.md) |
| Understand the design | [`specs/03-architecture.md`](specs/03-architecture.md) |
| Know what gets built when | [`specs/ROADMAP.md`](specs/ROADMAP.md) |
| Implement something | [`specs/README.md`](specs/README.md) — it explains the spec-driven process |
| Try it on real data | [`geocomp/resources/datasets/rd01/README.md`](geocomp/resources/datasets/rd01/README.md) |
| Know why a decision was made | [`specs/adr/`](specs/adr/) |

## Running the tests

Three tiers ([`specs/20`](specs/20-testing-and-validation.md) §2). The first two need nothing but Python:

```sh
pip install pytest ruff numpy
ruff check . && pytest -q
```

**Tier 3 needs a real QGIS**, and is where every "does it actually register, render and run" question is
answered. CI runs it in the official `qgis/qgis:latest` container. To run it locally, install QGIS with its
Python bindings and point pytest at the interpreter those bindings were built for:

```sh
sudo apt-get install -y qgis python3-qgis xvfb        # Debian/Ubuntu
QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/qgis
```

The bindings are built for the distribution's own Python, which may not be the `python3` on your PATH — if
the import fails with `No module named 'PyQt5.sip'`, you are running the wrong interpreter.

**Run tier 3 before believing a change works.** The QGIS-free tiers cannot reach the Processing boundary, the
dialogs, or the QML styles, and a change that passes them can still be broken everywhere a user would touch
it. Tests needing a QGIS newer than the one installed skip with the reason stated, rather than failing, so a
red result is a real one.

## What GeoComp does that the engines do not

DynAdjust adjusts networks; `rnx2rtkp` processes GNSS. Neither performs the instrument-level pre-processing,
the classical survey computations, the levelling schemes, the gravimetric reduction and adjustment, the
network pre-analysis, or the systematic covariance propagation that this project requires. Those are
GeoComp's own work — see [`specs/adr/0002-in-house-lsq-core.md`](specs/adr/0002-in-house-lsq-core.md).

Three properties distinguish it from a GUI wrapper:

- **Every measured and derived quantity carries an uncertainty**, propagated rigorously where the information
  exists and by documented approximate means where it does not — always labelled which
  ([`specs/05-uncertainty-and-covariance.md`](specs/05-uncertainty-and-covariance.md)).
- **Epochs are first-class.** Comparing two coordinate solutions checks datum and epoch compatibility and
  transforms where needed, rather than differencing numbers blindly
  ([`specs/14-multi-epoch-monitoring.md`](specs/14-multi-epoch-monitoring.md)).
- **Results are statistically validated** — global test, data snooping, internal and external reliability,
  error ellipses — with every statistic reported alongside its critical value and decision
  ([`specs/06-adjustment-core.md`](specs/06-adjustment-core.md)).

## Contributing

The project is developed openly and welcomes contributions from students, professionals, companies and public
bodies. Development is specification-driven: read [`specs/README.md`](specs/README.md) before opening a pull
request — it explains how requirements, phases and decisions relate, and what "done" means.
