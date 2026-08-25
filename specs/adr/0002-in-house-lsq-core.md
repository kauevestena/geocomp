# ADR-0002 — Implement an in-house least-squares core alongside DynAdjust

**Status:** Accepted
**Date:** 2026-08
**Requirements:** FR-220, FR-270, FR-700
**Supersedes reasoning in:** [`../archive/2025-plugin-roadmap-v2.md`](../archive/2025-plugin-roadmap-v2.md)

## Context

The archived roadmap states its organising premise directly:

> "The roadmap assumes all heavy geodetic math is delegated to **DynAdjust** and **RNX2RTKP**."

If true, GeoComp would be a GUI over two binaries and this project would be considerably smaller. It is not
true, and the decision to be recorded is what to build instead.

## What the engines do not cover

Reading the proposal's requirements against the engines' actual capabilities:

| Required by the proposal | DynAdjust | `rnx2rtkp` |
|---|---|---|
| PD/PI reduction, atmospheric / instrument / EDM corrections | ✖ | ✖ |
| Traverse, resection, forward intersection, 3D radiation | ✖ | ✖ |
| Geometric levelling schemes and closures | ✖ | ✖ |
| Gravimetric corrections and **gravimetric network adjustment** | ✖ (no gravity measurement type) | ✖ |
| Network pre-analysis on a network with no observations | ✖ | ✖ |
| Geometric reductions with covariance propagation | ✖ | ✖ |

`topo_test/processing_prototype.ipynb` settles the question empirically: the project author had already
prototyped the first row in Python, because there was nothing to delegate it to.

## Options

**A. Delegate everything (the archived roadmap's premise).** Rejected: the table above shows a whole menu
group (Gravimetry), a whole objective (pre-analysis, O1) and the entire pre-processing layer with no engine
behind them.

**B. Pre-processing in-house, all adjustment to DynAdjust.** Better, but still leaves gravimetric network
adjustment and pre-analysis unimplementable, makes CI depend on an external binary, and makes the teaching
use case (see every intermediate quantity) awkward.

**C. Pre-processing plus a full in-house least-squares core, with DynAdjust as a second engine.** Chosen.

## Decision

**Option C.** GeoComp implements its own least-squares adjustment with full statistical validation, *and*
drives DynAdjust. Both produce the same `Solution` type
([`../04-data-model.md`](../04-data-model.md) §2.8).

Division of labour is in [`../06-adjustment-core.md`](../06-adjustment-core.md) §1.

## Rationale

1. **Gravimetry has no alternative.** A required menu group cannot be implemented any other way.
2. **Pre-analysis needs the design matrix before observations exist** — an adjustment engine cannot help.
3. **CI must run without engine binaries** (NFR-011). With option B, no adjustment could be tested on every
   commit.
4. **The teaching profile needs visible intermediates.** An external binary's output is what it chooses to
   print; an in-house implementation can expose **A**, **P**, **Σ**ₓ and every intermediate.
5. **Two independent implementations agreeing is the strongest correctness evidence available.** This is
   worth the duplication on its own, and it is the exit criterion of roadmap phase P6.
6. **It delivers something working sooner.** With option B, nothing computes until the engine integration is
   finished. With option C a complete vertical slice ships at P3 with no external dependency.

## Consequences

- More code to write, test and maintain: an adjustment engine, its statistics, and its numerical edge cases.
  This is accepted; it is the core competence of the project.
- **Scope must be bounded** so it does not become a second DynAdjust. NFR-008 sets the boundary: the
  in-house core targets networks up to ~10⁴ stations; beyond that, DynAdjust with segmentation is the
  supported path. GeoComp will not implement network segmentation or phased adjustment.
- Cross-validation (T5, [`../20-testing-and-validation.md`](../20-testing-and-validation.md) §4) becomes a
  standing obligation: any divergence must be explained before release.
- The archived roadmap's phase ordering is invalidated, since it assumed nothing could be computed before
  DynAdjust was integrated.
