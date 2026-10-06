# ADR-0009 — Bundle `rnx2rtkp` in the plugin; keep DynAdjust a download

**Status:** Accepted (amends [ADR-0003](./0003-engine-acquisition.md))
**Date:** 2026-10
**Requirements:** FR-301, FR-300, FR-302, FR-306

## Context

ADR-0003 chose to download pinned engines on demand and not to bundle them. For DynAdjust that stands. For
RTKLIB it left a gap its own text records: `specs/21` §4 ("RTKLIB is located, not acquired") found that the
upstream publishes executables for Windows only, at a release other than the one GeoComp's parsers were checked
against, so on Linux and macOS there is nothing to download, and a GNSS run needs a program the user must
build. The plugin is meant to be self-contained: a user who installs QGIS and GeoComp should be able to process
a GNSS session, and the proposal's promise of "poucos cliques" does not survive a `make`.

The reasons ADR-0003 gave against bundling were three. This ADR answers each for `rnx2rtkp` and for no other
program.

- **Size.** One `rnx2rtkp` is about 1 MB (under 2.5 MB statically linked). The objection was binaries for
  three operating systems multiplying the package; one small program per platform does not.
- **Licence.** RTKLIB's `license.txt` at the pinned commit is plain BSD 2-clause: redistribution in binary form
  is permitted as long as the notice and disclaimer travel with it. The earlier "see upstream" caution is
  settled by reading it (P7; `THIRD_PARTY.md`). DynAdjust's is not so simple (its GPL-2 CodeSynthesis XSD
  dependency), which is why it stays out.
- **Update coupling.** An engine update forces a GeoComp release. For `rnx2rtkp` that is wanted, not a cost:
  the parsers read a column layout that is not documented anywhere GeoComp can cite, and are checked against one
  commit. The program and the parser that reads it change together.

## Decision

1. **`rnx2rtkp` ships inside the plugin ZIP**, built in CI from the pinned RTKLIB-EX commit
   (`06e8644`, the one `scripts/check_rtklib_fixtures.py` checks the committed `.pos` fixtures against), under
   `resources/engines/<platform>/rtklib/`.
2. **Its licence ships beside it**, at `resources/engines/licences/RTKLIB-license.txt`. A build that carries a
   program without its licence fails (`scripts/build.py`).
3. **Search order** becomes: a configured path; GeoComp's managed installation; **the bundled copy**; the system
   `PATH`. A path the user configured still wins and is never silently replaced (ADR-0003 rule 3). The result
   says where the program came from: `bundled` is a source of its own in the provenance and the About dialog.
4. **Built on the oldest supported Ubuntu**, so that it runs on that and on every later one, and linked
   dynamically against `libc` and `libm` only. A static glibc would add LGPL relinking obligations that this
   avoids; `libgfortran` is not needed, because only the IERS tide model, which this build leaves out, uses it.
   CI fails the build if the program links anything else.
5. **A ZIP unpacked by QGIS loses the executable bit**, so the plugin restores it, once, before first use
   (`bundled_directories`). CI unpacks the archive the way QGIS does and runs the bundled program.
6. **DynAdjust stays a download** (ADR-0003 option C, unchanged), through the engine manager.

## Platforms

Linux x86-64 is built, tested and shipped. Windows and macOS are **not yet**: the same build needs a Windows and
a macOS runner and the fixtures run against each result, and a macOS binary has the further question of
Gatekeeper. Until they are done, those platforms fall through to a configured path or `PATH`, exactly as before.
This ADR does not claim more than what CI checks.

## Consequences

- `specs/21` §4 rule 1 and its RTKLIB paragraph are amended; ADR-0003 is marked as amended, not rewritten.
- `THIRD_PARTY.md` moves RTKLIB out of "not bundled".
- The plugin ZIP grows by about 1 MB and now differs per platform built; the reproducible-archive check still
  holds, because the program is built once and the same file goes into both builds.
- The bundled version is pinned to the commit above. Moving it means re-running the fixture check and reading
  the diff, as for any engine release.
