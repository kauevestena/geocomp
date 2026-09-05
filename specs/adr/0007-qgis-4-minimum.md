# ADR-0007 — Target QGIS 4.x; do not support the 3.x series

**Status:** Accepted
**Date:** 2026-08
**Requirements:** NFR-001, NFR-003
**Amends:** NFR-001's original wording in [`../02-requirements.md`](../02-requirements.md)

## Context

`metadata.txt` must declare a minimum QGIS version, and NFR-001 originally said GeoComp supports "the QGIS
Long Term Release current at the time of each release". At the time of writing that is **QGIS 3.44**, the
final 3.x LTR. QGIS 4.0 shipped in February 2026 and **4.2 becomes the first 4.x LTR in October 2026**.

The two series differ in ways a plugin feels directly: QGIS 3.x binds PyQt5, QGIS 4.x binds PyQt6. Supporting
both means either coding to the intersection of two Qt APIs or carrying compatibility shims through every GUI
module — for the whole life of the project, since GeoComp's own roadmap runs to a v1.0 well past the 3.x
end of life.

## Options

**A. Minimum 3.40 (the 3.x LTR line).** Widest immediate reach. Costs PyQt5/PyQt6 dual support across the
GUI layer, and locks the project to the older API for years while 3.x is still nominally supported.

**B. Minimum 4.0.0.** PyQt6 only. Excludes users still on 3.44 LTR until they upgrade.

**C. Minimum 3.40 now, raise to 4.0 later.** Defers the choice, and pays the dual-support cost during exactly
the phases (P0–P3) when the GUI layer is being written — the worst possible time to carry it.

## Decision

**Option B: `qgisMinimumVersion=4.0.0`.** Taken by the project coordinator.

## Rationale

- **The compatibility burden lands on the phases that can least afford it.** P0 through P3 build the entire
  presentation layer. Writing it twice, or to a lowest common denominator, would slow the phases that
  deliver the first usable product.
- **The timing is favourable.** GeoComp's own v1.0 is at the end of a multi-phase roadmap. By the time it
  ships, 4.x will have been the LTR line for some time, and 3.x will be at or past end of life. A plugin
  released in 2027 with a 3.40 minimum would be supporting a dead branch.
- **PyQt6-only is materially simpler**, particularly for the scoped enumerations (`Qgis.MessageLevel.Info`,
  `QDialogButtonBox.StandardButton.Ok`) that differ between the two.
- Imports still go through the **`qgis.PyQt` shim** rather than `PyQt6` directly. That is the idiomatic QGIS
  path, it keeps the code conventional for QGIS developers, and it costs nothing.

## Consequences

- Users on QGIS 3.44 LTR cannot install GeoComp. Given the plugin ships no geodetic computation before P3,
  nobody is losing a capability they had; they are waiting for one that does not exist yet.
- **NFR-001 is reworded**: GeoComp supports the current LTR *of the 4.x series* and the current stable
  release. Until 4.2 becomes LTR in October 2026, "current stable 4.x" is the only target, and CI tests
  against the QGIS container's current release.
- The CI matrix in [`../20-testing-and-validation.md`](../20-testing-and-validation.md) §7 targets the 4.x
  series.
- Should a funder or partner institution require 3.x support, this ADR is superseded rather than edited, and
  the cost is re-estimated then — with the compatibility layer added to a working codebase rather than
  designed into an empty one.
