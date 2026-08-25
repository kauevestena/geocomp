# ADR-0001 — Licence: GPL-2.0-or-later

**Status:** Accepted
**Date:** 2026-08
**Requirement:** NFR-009

## Context

The research project commits to open source with a **permissive** licence, arguing explicitly against tools
whose terms block commercial use or restrict modification and redistribution — naming Bernese as the
counter-example (`tex §Justificativa aplicada e comercial`).

Two constraints work against the literal word:

1. The official QGIS plugin repository (plugins.qgis.org) requires listed plugins to be licensed
   GPLv2-or-later. Listing there is not optional for this project: the proposal's "bastando instalar o QGIS e
   o plugin, com poucos cliques" depends on it.
2. PyQGIS and PyQt are GPL. A Python plugin that imports them is a derivative work in the sense the GPL
   intends.

## Options

**A. Permissive (MIT / Apache-2.0) throughout.** Matches the proposal's wording. Blocks listing on
plugins.qgis.org and is inconsistent with the GPL status of what the plugin imports.

**B. GPL-2.0-or-later throughout.** Satisfies the repository requirement and the PyQt/PyQGIS relationship.
Not "permissive" in the technical sense, but delivers every practical freedom the proposal asks for.

**C. Split: GPL plugin layer, permissive pure-Python core.** The QGIS-free `core/`
([`../03-architecture.md`](../03-architecture.md)) has no GPL dependency and could be MIT or Apache-2.0,
letting the geodetic mathematics be reused outside QGIS. Closest to the stated intent, at the cost of two
licences, two packaging paths, and a boundary contributors must understand.

## Decision

**Option B: GPL-2.0-or-later for the whole project.**

This was put to the project coordinator with options A, B and C and B was chosen.

## Rationale

The proposal's *intent* — no cost, no commercial restriction, free modification and redistribution — is
fully satisfied by GPL-2.0-or-later. Everything it objects to in Bernese is absent: no fee, no
non-commercial clause, no restriction on modifying or redistributing the source.

The gap between the intent and the word "permissive" is real but narrow: copyleft requires derivative works
to stay under the same licence. That obligation does not affect any user or use case the proposal describes.

Option C remains genuinely attractive and is not foreclosed. If reuse of the geodetic core outside QGIS
becomes a real demand, a future ADR can relicense `core/` — which is far easier than the reverse, and is one
more reason the QGIS-free core boundary is worth maintaining.

## Consequences

- `metadata.txt` declares `license=GPL-2.0-or-later`; the repository carries the full licence text; every
  source file carries an SPDX header.
- Third-party notices are maintained for DynAdjust (Apache-2.0), RTKLIB, NumPy, SciPy and `openpyxl`
  ([`../21-packaging-ci-release-licensing.md`](../21-packaging-ci-release-licensing.md) §7.2).
- The engines are invoked as separate processes, never linked, so their licences do not combine with
  GeoComp's.
- **The research project's wording should be corrected.** `tex §Justificativa aplicada e comercial` should
  read "licença livre" or "copyleft" rather than "licença permissiva". This is a wording change; the intent
  described in the surrounding text is unchanged and is met.
