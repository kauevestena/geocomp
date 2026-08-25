# ADR-0005 — Every menu action is a Processing algorithm

**Status:** Accepted
**Date:** 2026-08
**Requirements:** FR-005, FR-033

## Context

The proposal requires two things that could easily become two implementations of the same capability:

- a dedicated top-level GeoComp menu organised by survey technique
  (`tex §Painel de Configuração Global`, `fig/menu_estrutura.png`), and
- the processing modules implemented as QGIS Processing algorithms, described as the **central objective** of
  the architecture, so they can be integrated and chained (`tex §Arquitetura do plugin`).

Many plugins solve this by writing a dialog that does the work and, separately, an algorithm that does
roughly the same work. The two then drift, and the divergence surfaces as "it gives a different answer from
the toolbox".

## Options

**A. Menu dialogs and Processing algorithms as separate implementations.** Maximum UI freedom, guaranteed
drift. Rejected.

**B. The menu is a thin launcher over the algorithms.** One implementation. Some interactions need a custom
dialog on top.

**C. Menu items are only shortcuts to the standard Processing dialog.** Simplest, but some required
interactions — interactive pre-analysis on the canvas (FR-272), field mapping with a data preview (FR-160) —
genuinely cannot be expressed as a static parameter form.

## Decision

**Option B.** Every capability exists exactly once, as a `QgsProcessingAlgorithm`. The menu is generated from
the algorithm registry. Most items open the standard Processing dialog; an enumerated set opens a custom
dialog that **collects parameters and then runs the same algorithm**.

The enumerated set is listed in [`../15-ui-menu-and-settings.md`](../15-ui-menu-and-settings.md) §1.2, and
adding to it is a deliberate decision, not a default.

## Consequences

- Every capability is scriptable from PyQGIS, chainable in the graphical modeller, and available in batch
  mode — which is exactly what the proposal asks of the Processing Provider.
- There is one place where a computation can be wrong, and one place to test it.
- The menu cannot contain an item with no algorithm, and an algorithm cannot exist with no menu route: a CI
  check asserts the correspondence in both directions
  ([`../20-testing-and-validation.md`](../20-testing-and-validation.md) §2).
- Custom dialogs are constrained to parameter collection and result presentation. Where a custom dialog seems
  to need computation of its own, that computation belongs in `core/` and should be exposed as an algorithm.
- Menu labels, groups and ordering come from algorithm metadata, so they are translated once (FR-090).
