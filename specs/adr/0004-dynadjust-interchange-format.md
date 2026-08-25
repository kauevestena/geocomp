# ADR-0004 — Use DynaML XML as the primary DynAdjust interchange format

**Status:** Accepted
**Date:** 2026-08
**Requirements:** FR-163, FR-320

## Context

DynAdjust accepts three input formats: **DNA** (the `.stn`/`.msr` pair), **DynaML** (XML) and **SINEX**.
GeoComp must generate input automatically from QGIS layers, databases, CSV files and spreadsheets (FR-320),
and generating it wrongly is the failure mode with the worst consequences — a misaligned column produces a
file DynAdjust accepts and adjusts, giving a confidently wrong answer.

## Options

**A. DNA `.stn`/`.msr`.** Compact, human-readable, and what most existing DynAdjust users have. But the
format is column-oriented: a one-character misalignment silently changes a value's meaning. Every generation
and parsing bug is invisible until the numbers are wrong.

**B. DynaML XML.** Verbose, but schema-defined. A generation error is caught by schema validation before
DynAdjust ever sees it, structure is explicit rather than positional, XML generation and parsing use tested
standard-library machinery, and covariance matrices — the thing that most needs to survive intact — have
explicit structure rather than a positional convention.

**C. SINEX.** A standard, but oriented toward GNSS solution exchange rather than toward expressing a mixed
terrestrial-and-GNSS network from scratch.

## Decision

**Write DynaML (option B) as the primary format. Read DNA `.stn`/`.msr` for interoperability. Support SINEX
for GNSS solution exchange where it is the natural format.**

## Rationale

The asymmetry between writing and reading drives this. GeoComp *writes* input on every run, from
automatically assembled data, and correctness there is critical — so the format that can be machine-validated
wins. GeoComp *reads* DNA only when a user brings an existing project, which is occasional and where a parse
failure is visible and recoverable.

Verbosity is not a real cost: these files are generated, transient, and stored in a working directory.

DNA *writing* is a secondary path, for users who want to hand the generated files to another DynAdjust
workflow.

## Consequences

- The writer validates its output against the DynaML schema before invoking `dnaimport`, catching generation
  errors at their source rather than as a confusing adjustment result.
- The schema is the authority for the observation-type mapping in
  [`../07-engine-dynadjust.md`](../07-engine-dynadjust.md) §4.2 — including the entries marked **[C]** there,
  which must be confirmed against it and against the User's Guide during implementation.
- A DNA reader must still be written, and column-position fragility is confronted there — but on input,
  where a mistake surfaces immediately.
- Round-trip tests cover both directions and assert that covariance matrices survive at full double
  precision.
