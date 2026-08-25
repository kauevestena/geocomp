# `geocomp/` — the QGIS plugin package

This directory **is** the installable QGIS plugin package. Everything inside it — and nothing outside it —
is what gets zipped and shipped to users and to [plugins.qgis.org](https://plugins.qgis.org).

It is intentionally almost empty right now. Implementation is specification-driven: code lands here phase by
phase as described in [`../specs/ROADMAP.md`](../specs/ROADMAP.md), and every module is written against an
accepted specification in [`../specs/`](../specs/).

## Ground rules for anything added here

1. **`metadata.txt` lives at this level.** QGIS identifies the plugin by `geocomp/metadata.txt`; the ZIP must
   contain exactly one top-level folder named `geocomp`. See
   [`../specs/21-packaging-ci-release-licensing.md`](../specs/21-packaging-ci-release-licensing.md).
2. **`core/` must never import `qgis` or `PyQt`.** The geodetic computation layer is plain Python so it can be
   unit-tested, reused and reasoned about without a QGIS runtime. This rule is enforced in CI. See
   [`../specs/03-architecture.md`](../specs/03-architecture.md).
3. **Every user-facing string is translated from its first commit.** Source strings are English; PT-BR and ES
   ship as `.qm` files. See [`../specs/18-i18n-and-profiles.md`](../specs/18-i18n-and-profiles.md).
4. **Every quantity carries its uncertainty.** No bare floats for measured or derived geodetic values. See
   [`../specs/05-uncertainty-and-covariance.md`](../specs/05-uncertainty-and-covariance.md).
5. **No empty placeholder files.** A module is created by the phase that implements it.

## Planned layout

The target structure, for orientation only — see
[`../specs/03-architecture.md`](../specs/03-architecture.md) for the authoritative version:

```text
geocomp/
  metadata.txt          plugin manifest read by QGIS
  __init__.py           classFactory() entry point
  plugin.py             GeoCompPlugin: initGui() / unload(), menu construction
  provider.py           GeoCompProvider (QgsProcessingProvider)
  core/                 pure Python: units, uncertainty, models, adjustment, techniques
  engines/              subprocess adapters: DynAdjust, RTKLIB, engine manager
  gui/                  dialogs, the Global Settings window, menu actions
  algorithms/           QgsProcessingAlgorithm subclasses (one per menu action)
  io/                   GeoPackage / PostGIS / CSV / XLSX / RINEX / DNA / SINEX
  resources/            icons, QML layer styles, report templates
  i18n/                 geocomp_pt_BR.ts|qm, geocomp_es.ts|qm
```

## Licence

GPL-2.0-or-later. See [`../specs/adr/0001-licensing.md`](../specs/adr/0001-licensing.md) for why, and for the
third-party notices covering DynAdjust and RTKLIB.
