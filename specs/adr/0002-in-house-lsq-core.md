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
| Gravimetric **corrections**, and drift estimated jointly with the network | ✖ (no gravity measurement type, and no nuisance parameter to carry drift) | ✖ |
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

1. **Gravimetry's corrections have no alternative, though its adjustment does.** *Corrected below — see
   Amendment 1.* A required menu group cannot be implemented any other way, but the part that has no
   alternative is the corrections and the joint drift estimation, not the network adjustment itself.
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

---

## Amendment 1 — gravimetric adjustment is levelling adjustment

*Raised in review; the decision stands, the reasoning did not.*

Rationale 1 originally read "gravimetry has no alternative", and the table said DynAdjust could not adjust a
gravimetric network. **The observation equation of a gravity difference is the observation equation of a
height difference.** Both are an observed difference between two station parameters, with partials of −1 and
+1; GeoComp implements them as one function, `_difference_1d` in
[`../../geocomp/core/adjustment/equations.py`](../../geocomp/core/adjustment/equations.py), called with the
component `"g"` or `"h"`. `tests/test_gravimetry_is_levelling.py` asserts the two design matrices are
identical element for element, and that the two adjustments agree on estimates, residuals, variance factor
and redundancy.

So a **drift-corrected** gravimetric network is a 1D difference network under a relabelling, and DynAdjust
adjusts those. What DynAdjust genuinely cannot do is the gravimetric corrections (scale, tidal, calibration
tables) and **drift estimated jointly with the network** — which matters, because drift and gravity
differences are not separable by pre-correction alone ([`../12-module-gravimetry.md`](../12-module-gravimetry.md)
§4.3), so pre-correcting is an approximation the in-house core does not have to make.

**Option C stands**, on rationales 2, 3 and 4, which the correction does not touch: pre-analysis needs the
design matrix before observations exist, CI must run with no engine binary, and the teaching profile needs
visible intermediates. Rationale 1 alone was never load-bearing.

Three consequences follow, and they are gains rather than losses:

- **P8 is much cheaper than planned.** The adjustment is P2's, already written and tested. P8 reduces to
  corrections, drift as a nuisance parameter, gravimeter profiles and the datum of a difference-only network.
- **P6 gains a cross-validation case it was assumed not to have.** A gravimetric network can be checked
  against DynAdjust by relabelling its differences, which is a real independent check on the in-house core in
  the one module we thought had none.
- **P9's combined adjustment is possible for the same reason.** Heights and gravity enter one normal matrix
  because they are the same kind of unknown observed the same way.

