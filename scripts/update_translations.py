#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Update the translation catalogues, and report completeness.

Usage::

    python3 scripts/update_translations.py            # update .ts from the sources
    python3 scripts/update_translations.py --check    # report only, non-zero on a gap
    python3 scripts/update_translations.py --compile  # also build .qm (needs lrelease)

Existing translations are preserved: the ``.ts`` files are the source of truth
for translated text, and this only adds newly-found sources and removes ones the
code no longer contains.

``--check`` is what CI runs. FR-091 requires an untranslated string to be caught
at the commit that introduces it, so a new source string with no translation is
a build failure, not a note for later.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.translations import (
    TARGET_LOCALES,
    catalogue_path,
    compile_catalogue,
    completeness,
    extract_sources,
    have_qt_tools,
    merge,
    read_catalogue,
    write_catalogue,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report only; fail on any gap")
    parser.add_argument("--compile", action="store_true", help="also compile .qm files")
    args = parser.parse_args(argv)

    sources = extract_sources()
    total_sources = sum(len(entries) for entries in sources.values())
    print(f"extracted {total_sources} source strings in {len(sources)} contexts")
    if not have_qt_tools():
        print("note: Qt linguist tools not found; using the built-in AST extractor")

    incomplete = False
    for locale in TARGET_LOCALES:
        path = catalogue_path(locale)
        existing = read_catalogue(path)
        catalogue = merge(sources, existing)

        added = sum(
            1
            for context, entries in catalogue.items()
            for source in entries
            if source not in existing.get(context, {})
        )
        removed = sum(
            1
            for context, entries in existing.items()
            for source in entries
            if source not in sources.get(context, set())
        )

        if not args.check:
            write_catalogue(path, locale, catalogue)

        translated, total = completeness(catalogue)
        status = "complete" if translated == total else f"{total - translated} MISSING"
        print(f"  {locale}: {translated}/{total} translated ({status}) +{added} -{removed}")

        if translated != total:
            incomplete = True
            for context in sorted(catalogue):
                for source in sorted(catalogue[context]):
                    if not catalogue[context][source]:
                        print(f"      untranslated [{context}] {source[:70]!r}")

        if args.compile:
            qm = compile_catalogue(path)
            print(f"      compiled: {qm}" if qm else "      lrelease not found; skipped .qm")

    if incomplete:
        print("\nTranslation catalogues are incomplete (FR-091).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
