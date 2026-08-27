# `geocomp/` — the QGIS plugin package

This directory **is** the installable QGIS plugin package. Everything inside it — and nothing outside it —
is zipped and shipped to users and to [plugins.qgis.org](https://plugins.qgis.org).

Implementation is specification-driven: code lands here phase by phase per
[`../specs/ROADMAP.md`](../specs/ROADMAP.md), against accepted specifications in [`../specs/`](../specs/).

**Current state: phase P3 (Total station — the first vertical slice).** The plugin loads, and the whole
chain runs with no external engine anywhere in it: import a field book, reduce the faces, apply the
instrument, atmospheric and EDM corrections, compute a traverse, a resection, an intersection, a
trigonometric height or a radiation, assemble the network, inspect it, and adjust it by least squares in 1D,
2D or 3D — free or constrained — with the global test, data snooping, reliability and error ellipses.
Results arrive as styled map layers. Reachable from the **Total Station** and **Analysis** menus and from the
toolbox, and assemblable end to end in the graphical modeller.

Try it on RD-01, which ships in [`resources/datasets/rd01/`](resources/datasets/rd01/README.md): the toolbox
algorithm *Install tutorial dataset* copies it somewhere writable, and its tutorial walks the whole chain.

The remaining technique modules — levelling, GNSS, gravimetry, photogrammetric support — arrive from P4
onwards.

## Ground rules

1. **`core/` must never import `qgis` or `PyQt`.** The geodetic layer is plain Python so it can be
   unit-tested, reviewed by geodesists rather than QGIS developers, reused outside QGIS, and survive QGIS API
   changes. Enforced by `tests/structural/test_no_qgis_in_core.py`.
   See [`../specs/03-architecture.md`](../specs/03-architecture.md).
2. **Every user-facing string is translated from its first commit.** Source strings are English; pt-BR and es
   ship as compiled `.qm`. Enforced by `tests/structural/test_i18n_strings.py`.
   See [`../specs/18-i18n-and-profiles.md`](../specs/18-i18n-and-profiles.md).
3. **Every quantity carries its uncertainty.** No bare floats for measured or derived geodetic values.
   See [`../specs/05-uncertainty-and-covariance.md`](../specs/05-uncertainty-and-covariance.md).
4. **Algorithms are declared in `registry.py`.** The provider and the menu both read it, so they cannot drift
   apart. Enforced by `tests/structural/test_menu_algorithm_parity.py`.
   See [`../specs/adr/0005-menu-algorithm-parity.md`](../specs/adr/0005-menu-algorithm-parity.md).
5. **No empty placeholder files.** A module is created by the phase that implements it.

## Layout

```text
geocomp/
  metadata.txt          plugin manifest (minimum QGIS 4.0.0 — see ADR-0007)
  __init__.py           classFactory() entry point
  plugin.py             GeoCompPlugin: initGui / unload, menu, toolbar
  provider.py           GeoCompProvider (QgsProcessingProvider)
  registry.py           the algorithm registry — pure data, no QGIS imports

  core/                 pure Python, no QGIS: version, errors, cancellation, settings,
                        units, uncertainty, differentiation, models, adjustment,
                        statistics, preanalysis. Later: techniques, monitoring
  services/             logging, layered settings, QgsTask wrapping, message rendering
  gui/                  menu, Global Settings window, About dialog
  algorithms/           QgsProcessingAlgorithm subclasses, grouped as in the menu
  resources/            icons; later QML styles and report templates
  i18n/                 geocomp_pt_BR.ts, geocomp_es.ts (.qm built at packaging)

  io/                   field-book import with saved mappings (P3).
                        GeoPackage, PostGIS, RINEX             — arrive in P5, P7

  engines/              DynAdjust and RTKLIB adapters          — arrives in P6, P7
```

## Building and testing

From the repository root:

```bash
pytest                                    # tier 1 + structural checks; no QGIS needed
ruff check .
python3 scripts/update_translations.py    # refresh catalogues, report completeness
python3 scripts/build.py                  # produce dist/geocomp.zip
```

The ZIP is reproducible: two builds of one commit are byte-identical.

## Licence

GPL-2.0-or-later — see [`../LICENSE`](../LICENSE),
[`../THIRD_PARTY.md`](../THIRD_PARTY.md) and
[`../specs/adr/0001-licensing.md`](../specs/adr/0001-licensing.md).
