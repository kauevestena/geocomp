# Architecture Decision Records

Each ADR records one significant, hard-to-reverse decision: the context, the options considered, the choice,
and its consequences.

**To change a decision, add a new ADR that supersedes the old one.** Do not edit an accepted ADR except to
add a "Superseded by" line. The value of these records is the reasoning at the time, including the reasoning
that later turned out to be wrong.

| ADR | Decision | Status |
|---|---|---|
| [0001](./0001-licensing.md) | GPL-2.0-or-later | Accepted |
| [0002](./0002-in-house-lsq-core.md) | Implement an in-house least-squares core alongside DynAdjust | Accepted |
| [0003](./0003-engine-acquisition.md) | Download pinned engine binaries; do not bundle | Accepted |
| [0004](./0004-dynadjust-interchange-format.md) | Use DynaML XML as the primary DynAdjust interchange format | Accepted |
| [0005](./0005-menu-algorithm-parity.md) | Every menu action is a Processing algorithm | Accepted |
| [0006](./0006-storage.md) | GeoPackage canonical, PostGIS mirror, identical logical schema | Accepted |

"Accepted" here means accepted into the draft specification set; all remain subject to the coordinator's
first review ([`../README.md`](../README.md) §Document status).
