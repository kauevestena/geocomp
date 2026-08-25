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

**Specification stage.** No plugin code yet. The specification set is written and under review; implementation
proceeds phase by phase from [`specs/ROADMAP.md`](specs/ROADMAP.md).

## Repository layout

| Path | Contents |
|---|---|
| [`specs/`](specs/) | **Start here.** The authoritative specification set, the roadmap, and the architecture decision records |
| [`geocomp/`](geocomp/) | The installable QGIS plugin package (currently a placeholder — see its README) |
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
| Know why a decision was made | [`specs/adr/`](specs/adr/) |

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
