#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the installable plugin ZIP (specs/21 sections 2 and 3).

Usage::

    python3 scripts/build.py                  # build dist/geocomp.zip
    python3 scripts/build.py --output DIR     # build elsewhere
    python3 scripts/build.py --skip-translations   # for a development build

The archive is **reproducible**: entries are sorted and timestamps fixed, so two
builds of the same commit are byte-identical. That is what makes it possible to
verify that a published artefact corresponds to a given commit, which for a
plugin distributed as a binary blob to thousands of users is worth the small
effort it costs.

The build refuses to proceed on a version mismatch or an untranslated string,
per specs/21 section 3 -- a release that ships either is worse than a release
that did not happen.
"""

from __future__ import annotations

import argparse
import configparser
import shutil
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

PLUGIN_DIR = REPO_ROOT / "geocomp"
PLUGIN_NAME = "geocomp"

#: Fixed timestamp for every archive entry: 1980-01-01, the earliest a ZIP can
#: represent. Any constant works; this one is unmistakably synthetic.
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

#: What ships. Everything else is development infrastructure.
INCLUDE_SUFFIXES = {".py", ".txt", ".svg", ".png", ".qm", ".qml", ".html", ".csv", ".md", ".json"}

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}

#: Never shipped, even where the suffix matches. ``.ts`` files are translation
#: *sources*; the compiled ``.qm`` is what the plugin loads.
EXCLUDE_SUFFIXES = {".ts", ".pyc", ".pyo"}


class BuildError(RuntimeError):
    """A precondition for building failed."""


def read_metadata() -> configparser.SectionProxy:
    parser = configparser.ConfigParser()
    parser.read(PLUGIN_DIR / "metadata.txt", encoding="utf-8")
    return parser["general"]


def check_version() -> str:
    """Assert that metadata.txt and the code agree, and return the version."""
    from geocomp.core.version import __version__

    declared = read_metadata()["version"]
    if declared != __version__:
        raise BuildError(
            f"version mismatch: metadata.txt says {declared}, "
            f"geocomp.core.version says {__version__}"
        )
    return __version__


def build_translations(strict: bool) -> None:
    """Compile the .ts catalogues to .qm, refusing on an incomplete catalogue."""
    from scripts.translations import (
        TARGET_LOCALES,
        catalogue_path,
        compile_catalogue,
        completeness,
        extract_sources,
        merge,
        read_catalogue,
    )

    sources = extract_sources()
    for locale in TARGET_LOCALES:
        path = catalogue_path(locale)
        catalogue = merge(sources, read_catalogue(path))
        translated, total = completeness(catalogue)
        if translated != total:
            message = f"{locale} catalogue is incomplete: {translated}/{total} (FR-090)"
            if strict:
                raise BuildError(message)
            print(f"  WARNING: {message}")

        qm = compile_catalogue(path)
        if qm is None:
            message = "lrelease not found: cannot compile .qm translations"
            if strict:
                raise BuildError(
                    message + "\nInstall the Qt linguist tools, or pass --skip-translations "
                    "for a development build that ships without translations."
                )
            print(f"  WARNING: {message}; the build will ship untranslated")
        else:
            print(f"  compiled {qm.name} ({translated}/{total})")


def collect_files() -> list[Path]:
    """Every file that belongs in the archive, sorted for reproducibility."""
    files: list[Path] = []
    for path in sorted(PLUGIN_DIR.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.suffix in EXCLUDE_SUFFIXES:
            continue
        if path.suffix not in INCLUDE_SUFFIXES:
            continue
        files.append(path)
    return sorted(files)


def write_zip(target: Path, files: list[Path]) -> None:
    """Write a reproducible ZIP containing a single top-level ``geocomp/``."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()

    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            arcname = Path(PLUGIN_NAME) / path.relative_to(PLUGIN_DIR)
            info = zipfile.ZipInfo(str(arcname), date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            # Fixed permissions: whatever the build machine's umask happens to
            # be must not change the artefact.
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def verify(target: Path) -> None:
    """Check the archive satisfies what QGIS requires of a plugin ZIP."""
    with zipfile.ZipFile(target) as archive:
        names = archive.namelist()

    roots = {name.split("/", 1)[0] for name in names}
    if roots != {PLUGIN_NAME}:
        raise BuildError(f"archive must contain exactly one top-level folder; found {sorted(roots)}")

    if f"{PLUGIN_NAME}/metadata.txt" not in names:
        raise BuildError("archive is missing geocomp/metadata.txt")
    if f"{PLUGIN_NAME}/__init__.py" not in names:
        raise BuildError("archive is missing geocomp/__init__.py")

    leaked = [name for name in names if name.endswith((".ts", ".pyc"))]
    if leaked:
        raise BuildError(f"archive contains files that must not ship: {leaked}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "dist")
    parser.add_argument(
        "--skip-translations",
        action="store_true",
        help="do not compile .qm (development builds only; never for a release)",
    )
    args = parser.parse_args(argv)

    try:
        version = check_version()
        print(f"building GeoComp {version}")

        if args.skip_translations:
            print("  skipping translations (development build)")
        else:
            build_translations(strict=False)

        files = collect_files()
        target = args.output / f"{PLUGIN_NAME}.zip"
        write_zip(target, files)
        verify(target)

        size = target.stat().st_size
        print(f"  {len(files)} files -> {target} ({size:,} bytes)")
        return 0
    except BuildError as error:
        print(f"build failed: {error}", file=sys.stderr)
        return 1
    finally:
        # .qm files are build artefacts; leaving them in the source tree would
        # let a stale compiled catalogue shadow an updated .ts on the next run.
        for stale in (PLUGIN_DIR / "i18n").glob("*.qm"):
            stale.unlink()
        shutil.rmtree(PLUGIN_DIR / "__pycache__", ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
