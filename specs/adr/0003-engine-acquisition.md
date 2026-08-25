# ADR-0003 — Engine acquisition: download pinned binaries, do not bundle

**Status:** Accepted
**Date:** 2026-08
**Requirements:** FR-301, FR-300, FR-302, FR-306

## Context

The proposal's commercial justification promises that adoption is easy:

> *"...inclusive devido à sua fácil instalação, bastando instalar o QGIS e o plugin, com poucos cliques."*
> — `tex §Justificativa aplicada e comercial`

But DynAdjust and RTKLIB are compiled C++ programs, distributed separately, per platform. A user who must
find, build or install them from a command line has not had a two-click installation — and that user is
precisely the professional the proposal is trying to reach. The archived roadmap does not address this at
all.

## Options

**A. Require manual installation.** Simplest for the project, and it is what the archived roadmap implicitly
assumed. Rejected: it breaks the proposal's stated adoption promise for the exact audience the promise is
aimed at.

**B. Bundle binaries in the plugin ZIP.** Truly two clicks. Rejected: binaries for three platforms multiply
the package size well beyond what the plugin repository expects; it breaks the single-artefact model; it
makes GeoComp a redistributor of both engines with the licence obligations that entails (including
DynAdjust's GPL2-licensed CodeSynthesis XSD dependency); and every engine update forces a GeoComp release.

**C. Download pinned releases on demand.** Chosen.

**D. Docker.** Both engines are available as container images. Rejected as the default: it requires Docker
installed and running, which is a larger ask than the binary it avoids. Retained as an *option* for advanced
and server users.

## Decision

**Option C.** An engine manager in Global Settings downloads the pinned upstream release for the user's
platform, verifies its checksum, extracts it into the QGIS profile directory, and records the version.
Option D is offered as an alternative in Advanced mode.

This is workable because upstream already publishes what is needed: DynAdjust distributes prebuilt binaries
for Windows x64 (OpenBLAS and MKL), macOS Apple Silicon (dynamic and static), Ubuntu 22.04+ and generic
x86-64 Linux (static), plus a Docker image.

## Rules

1. **Prefer self-contained/static builds** where offered, so the user is never asked to resolve a system
   library chain.
2. **Verify checksums before extraction.** A downloaded executable that is not verified is a security
   problem, not a convenience.
3. **Install into the QGIS profile directory**, not a system location — no elevated privileges, and removal
   is clean.
4. **An explicitly configured path always wins** (FR-300), for users with a system installation or their own
   build.
5. **Versions are pinned and recorded** (FR-302, FR-134). The output parsers are version-sensitive; a
   silently updated engine is a silently changed result.
6. **Absence is graceful** (FR-306): the plugin loads, everything not needing that engine works, and
   operations that do are disabled with an explanation and an offer to install — never a runtime crash.
7. **Downloads go through the QGIS network stack**, honouring the user's proxy configuration.

## Consequences

- An engine manager must be built, tested per OS, and maintained as upstream release layouts change. This is
  real ongoing cost, accepted because the alternative defeats a stated project goal.
- Users behind restrictive networks may be unable to download; the manual path (rule 4) and an offline
  install from a downloaded archive both remain available.
- Engine version pinning becomes a release-management concern: each GeoComp release states its tested engine
  version range ([`../21-packaging-ci-release-licensing.md`](../21-packaging-ci-release-licensing.md) §6).
- GeoComp never redistributes engine binaries, so their licences remain entirely upstream's business.
