# ADR-0008 — SciPy is optional for correctness and required for scale

**Status:** Accepted
**Date:** 2026-08
**Requirements:** NFR-008, NFR-002, FR-220
**Amends:** NFR-008's original wording in [`../02-requirements.md`](../02-requirements.md)

## Context

Phase P2 built the in-house least-squares core, and building it surfaced a conflict between two
requirements that had not previously been examined together.

**NFR-008** requires the adjustment to handle networks of at least 10,000 stations. **ADR-0002** requires the
in-house core to exist at all, because gravimetric adjustment (FR-700) and network pre-analysis (FR-270)
have no external engine — DynAdjust does not support a gravity observation type, and pre-analysis needs
**A** and **P** before any observation exists.

A 10,000-station 3D network has 30,000 parameters. Held densely, its normal matrix is 30 000² × 8 bytes ≈
**7.2 GB**, and inverting it is O(n³). That is not a tuning problem; it is the wrong data structure. The
normal matrix of a geodetic network is *sparse* — a station's parameters are coupled only to the stations it
was observed to — and a sparse Cholesky factorisation with a fill-reducing ordering is the standard answer.

SciPy provides that (`scipy.sparse`, `scipy.sparse.linalg`) and also provides the statistical distributions
the tests need. But **SciPy is not guaranteed to be present**: QGIS ships NumPy with every installation and
SciPy with some. It is absent from the container this phase was developed in, which is how the question
arrived concretely rather than theoretically.

## Options

**A. Require SciPy.** Declare it a hard dependency in `metadata.txt`. Simplest code. Costs an installation
failure on any QGIS without it, for a plugin whose teaching profile (P1 in
[`18-i18n-and-profiles.md`](../18-i18n-and-profiles.md)) is aimed at student machines and lab installations
where adding a Python package is not always the user's to decide.

**B. Forbid SciPy.** NumPy only, everywhere. Keeps installation trivial and keeps one code path. Puts a hard
ceiling of a few thousand stations on the in-house core, and either drops NFR-008 or hands every large
network to DynAdjust — including the gravimetric and pre-analysis cases DynAdjust cannot do.

**C. SciPy optional for correctness, required for scale.** Every computation has a NumPy-only path that is
always available and always correct. Where SciPy is present it is used: for the statistical distributions,
and for a sparse solver above a size threshold. A network beyond what the dense path can hold reports that
SciPy is needed, naming it, rather than exhausting memory.

## Decision

**Option C**, taken with the project coordinator during phase P2.

Concretely:

1. **The NumPy path is the reference implementation.** It is always present, and it defines what "correct"
   means. Where SciPy is used, the two are tested against each other.
2. **SciPy is a soft dependency**, declared in `metadata.txt` as such. Its absence never blocks
   installation and never changes an answer.
3. **CI keeps testing with SciPy absent** — the QGIS-free tier does exactly that today — so the fallback
   cannot rot.
4. **NFR-008 is reworded** (below).

## What phase P2 actually delivered

Stating this plainly, because an ADR that describes an intention as though it were code is worse than no
ADR.

**Delivered.** `core/statistics/distributions.py` implements the normal, chi-square, F and t distributions
with a SciPy fast path and a complete NumPy-only fallback: Acklam's rational approximation refined by
Newton for the normal quantile, the regularised incomplete gamma (series and continued fraction) for
chi-square, and Lentz's continued fraction for the incomplete beta behind F and t. Both paths are tested
against published table values, and against each other wherever SciPy is installed.

**Not delivered.** The sparse solver. `core/adjustment/normal_equations.py` forms and factorises a **dense**
normal matrix — Cholesky, falling back to QR on the weighted design matrix when Cholesky fails numerically.
That is correct for every network, and comfortable to roughly 2,000–3,000 stations; it is not the path to
10,000.

The sparse path belongs to **phase P12**, whose stated deliverable already includes "performance work
against NFR-008". Writing it in P2 would mean writing it against no network large enough to show that it
helps, and a performance claim nobody has measured is exactly the kind of thing this specification set
exists to avoid.

## Consequences

- **NFR-008 is reworded** from a flat "MUST handle at least 10,000 stations" to a statement that separates
  correctness from scale, and names the boundary:

  > NFR-008 — The adjustment MUST be correct at every network size it accepts, using only NumPy. Beyond
  > roughly 2,000–3,000 stations it MUST use a sparse factorisation, which requires SciPy; where SciPy is
  > absent and the network exceeds what the dense path can hold, the adjustment MUST refuse with a message
  > naming SciPy rather than exhausting memory. Networks of at least 10,000 stations MUST be supported with
  > SciPy present; beyond that, DynAdjust segmentation is the supported path.

- **`metadata.txt` gains no hard SciPy requirement.** The plugin installs and runs without it.
- **The refusal above is not yet implemented either**, and is listed with the sparse solver as P12 work. Until
  then a very large network on the dense path will be slow or will exhaust memory, which is the behaviour
  today and is recorded here rather than implied.
- **Every future numerical addition inherits the rule**: NumPy path first, SciPy as an accelerator. A module
  that only works with SciPy installed is a defect, not a trade-off.
- Should QGIS begin shipping SciPy universally, this ADR is superseded rather than edited — the NumPy paths
  would then be dead weight, and removing them is a decision worth recording.
